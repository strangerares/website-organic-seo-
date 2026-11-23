import time
from collections import deque

import requests
from bs4 import BeautifulSoup

from seo_engine.utils.url_utils import absolute_url, same_domain, validate_url
from .robots import fetch_robots
from .sitemap import parse_sitemap


class Crawler:
    def __init__(self, max_pages=100, delay=1.0, timeout=15.0, user_agent=None, session=None):
        self.max_pages = max_pages
        self.delay = delay
        self.timeout = timeout
        self.user_agent = user_agent or "RioOrganicSEO/1.0 (+public website SEO audit)"
        self.session = session or requests.Session()

    def crawl(self, start_url: str):
        start_url = validate_url(start_url)
        robots = fetch_robots(start_url, self.session, self.user_agent, self.timeout)

        sitemap_urls = list(dict.fromkeys(robots.declared_sitemaps))
        if not sitemap_urls:
            sitemap_urls = [absolute_url(start_url, "/sitemap.xml")]

        all_sitemap_urls = []
        sitemap_diagnostics = {"declared": robots.declared_sitemaps, "checked": [], "errors": []}
        for sitemap_url in sitemap_urls:
            if not same_domain(sitemap_url, start_url):
                sitemap_diagnostics["errors"].append({"url": sitemap_url, "status": None, "description": "Sitemap points outside the audited domain"})
                continue
            if not robots.allows(sitemap_url, self.user_agent):
                continue
            entries, diagnostics = parse_sitemap(sitemap_url, self.session, self.timeout, self.user_agent)
            all_sitemap_urls.extend(entries)
            sitemap_diagnostics["checked"].extend(diagnostics["urls_checked"])
            sitemap_diagnostics["errors"].extend(diagnostics["errors"])

        queue = deque()
        queued = set()

        def enqueue(url):
            url = absolute_url(start_url, url)
            if url and same_domain(url, start_url) and url not in queued:
                if robots.allows(url, self.user_agent):
                    queued.add(url)
                    queue.append(url)

        enqueue(start_url)
        for url in all_sitemap_urls:
            enqueue(url)

        pages = []
        status_by_url = {}
        failed_requests = 0
        last_request = None

        while queue and len(pages) < self.max_pages:
            url = queue.popleft()
            if last_request is not None:
                time.sleep(self.delay)
            last_request = time.monotonic()

            try:
                response = self.session.get(url, timeout=self.timeout, headers={"User-Agent": self.user_agent}, allow_redirects=True)
                status_by_url[normalize_result_url(response)] = response.status_code
                status_by_url[url] = response.status_code
                if response.status_code >= 400:
                    failed_requests += 1
                page = {
                    "url": url,
                    "final_url": normalize_result_url(response),
                    "status": response.status_code,
                    "redirects": [hop.url for hop in response.history],
                    "headers": dict(response.headers),
                    "html": response.text if "text/html" in response.headers.get("Content-Type", "") or "html" in response.headers.get("Content-Type", "") else "",
                    "error": None,
                }
                pages.append(page)

                if page["html"]:
                    soup = BeautifulSoup(page["html"], "html.parser")
                    for anchor in soup.find_all("a", href=True):
                        enqueue(anchor["href"])
            except requests.RequestException as exc:
                failed_requests += 1
                status_by_url[url] = None
                pages.append({"url": url, "final_url": url, "status": None, "redirects": [], "headers": {}, "html": "", "error": str(exc)})

        return {
            "start_url": start_url,
            "robots": {
                "exists": robots.exists,
                "declared_sitemaps": robots.declared_sitemaps,
                "error": robots.error,
                "content": robots.content,
            },
            "sitemap": sitemap_diagnostics,
            "sitemap_urls": list(dict.fromkeys(all_sitemap_urls)),
            "pages": pages,
            "status_by_url": status_by_url,
            "successful_requests": sum(1 for page in pages if page["status"] and 200 <= page["status"] < 400),
            "failed_requests": failed_requests,
            "max_pages": self.max_pages,
            "delay": self.delay,
            "user_agent": self.user_agent,
        }


def normalize_result_url(response):
    return str(response.url)
