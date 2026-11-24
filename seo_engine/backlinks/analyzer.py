import re
import time
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from seo_engine.crawler.robots import fetch_robots
from seo_engine.utils.url_utils import normalize_url, validate_url


USER_AGENT = "RioOrganicSEOBacklinkResearch/1.0"
EMAIL_RE = re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)


class ProspectAnalyzer:
    def __init__(self, delay=1.0, timeout=15.0, session=None):
        self.delay = max(0.0, float(delay))
        self.timeout = float(timeout)
        self.session = session or requests.Session()
        self.last_request = 0.0

    def _get(self, url: str):
        elapsed = time.monotonic() - self.last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request = time.monotonic()
        return self.session.get(url, timeout=self.timeout, headers={"User-Agent": USER_AGENT}, allow_redirects=True)

    def analyze(self, prospect: dict) -> dict:
        page_url = validate_url(prospect["page_url"])
        base_url = f"{urlsplit(page_url).scheme}://{urlsplit(page_url).netloc}"
        robots = fetch_robots(base_url, self.session, USER_AGENT, self.timeout)
        if robots.exists and not robots.allows(page_url, USER_AGENT):
            result = dict(prospect)
            result["last_error"] = "Blocked by robots.txt"
            return result

        try:
            response = self._get(page_url)
            if response.status_code >= 400:
                result = dict(prospect)
                result["last_error"] = f"HTTP {response.status_code}"
                return result
            html = response.text
            final_url = normalize_url(response.url)
        except requests.RequestException as exc:
            result = dict(prospect)
            result["last_error"] = str(exc)
            return result

        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.find("title")
        page_title = title_tag.get_text(" ", strip=True) if title_tag else ""
        description_tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
        meta_description = description_tag.get("content", "").strip() if description_tag else ""
        html_tag = soup.find("html")
        language = (html_tag.get("lang", "") if html_tag else "").strip()

        headings = [tag.get_text(" ", strip=True) for tag in soup.find_all(["h1", "h2", "h3"])]
        paragraphs = [tag.get_text(" ", strip=True) for tag in soup.find_all("p")]
        summary_text = " ".join(headings + paragraphs)
        summary_text = re.sub(r"\s+", " ", summary_text).strip()
        if len(summary_text) > 800:
            summary_text = summary_text[:797] + "..."

        contact_url = ""
        for link in soup.find_all("a", href=True):
            label = link.get_text(" ", strip=True).lower()
            href = link["href"].lower()
            if "contact" in label or "contact" in href:
                contact_url = normalize_url(urljoin(final_url, link["href"]))
                break

        emails = sorted(set(email.lower() for email in EMAIL_RE.findall(html)))
        public_email = "; ".join(emails[:5])

        category = classify_category(page_title + " " + meta_description + " " + summary_text)
        opportunity = classify_opportunity(category, summary_text)

        result = dict(prospect)
        result.update({
            "page_url": final_url,
            "domain": urlsplit(final_url).hostname or prospect.get("domain", ""),
            "page_title": page_title,
            "meta_description": meta_description,
            "language": language,
            "content_summary": summary_text,
            "website_category": category,
            "opportunity_type": opportunity,
            "contact_page_url": contact_url,
            "public_email": public_email,
            "last_error": None,
        })
        return result


def classify_category(text: str) -> str:
    text = text.lower()
    if any(word in text for word in ("travel agency", "tour operator", "guided tours")):
        return "Travel Agency / Tour Operator"
    if any(word in text for word in ("hotel", "hostel", "accommodation", "guesthouse")):
        return "Hotel / Accommodation"
    if any(word in text for word in ("airport", "transfer", "transportation", "private driver")):
        return "Airport Transfer / Transportation"
    if any(word in text for word in ("expat", "expats", "brazilian living abroad")):
        return "Expat Community"
    if any(word in text for word in ("rio de janeiro", "brazil", "travel guide")):
        return "Travel Blog / Tourism Resource"
    return "General Website"


def classify_opportunity(category: str, text: str) -> str:
    lowered = text.lower()
    if "guest post" in lowered or "contribute" in lowered or "writer" in lowered:
        return "Guest article opportunity"
    if "resources" in lowered or "recommend" in lowered:
        return "Resource-page recommendation"
    if category == "Airport Transfer / Transportation":
        return "Useful transportation recommendation"
    if category in ("Travel Agency / Tour Operator", "Hotel / Accommodation"):
        return "Relevant local partnership inquiry"
    return "Editorial article contribution"
