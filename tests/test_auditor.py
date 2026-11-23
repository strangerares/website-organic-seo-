import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from seo_engine.auditor.page_audit import PageAudit
from seo_engine.auditor.technical_audit import TechnicalAudit
from seo_engine.crawler.crawler import Crawler
from seo_engine.crawler.robots import fetch_robots
from seo_engine.crawler.sitemap import parse_sitemap
from seo_engine.reporting.csv_report import write_csv_report
from seo_engine.reporting.html_report import write_html_report
from seo_engine.reporting.json_report import write_json_report
from seo_engine.utils.url_utils import validate_url, same_domain, absolute_url
from main import main


class FakeResponse:
    def __init__(self, url, status=200, text="", content=None, headers=None, history=None):
        self.url = url
        self.status_code = status
        self.text = text
        self.content = content if content is not None else text.encode()
        self.headers = headers or {"Content-Type": "text/html"}
        self.history = history or []


class URLTests(unittest.TestCase):
    def test_url_validation(self):
        self.assertEqual(validate_url("https://example.com/test#fragment"), "https://example.com/test")
        with self.assertRaises(ValueError):
            validate_url("example.com")

    def test_domain_and_link_resolution(self):
        self.assertTrue(same_domain("https://example.com/page", "https://example.com"))
        self.assertFalse(same_domain("https://other.com", "https://example.com"))
        self.assertEqual(absolute_url("https://example.com/a/", "../b"), "https://example.com/b")


class RobotsAndSitemapTests(unittest.TestCase):
    def test_robots_parsing(self):
        session = Mock()
        session.get.return_value = FakeResponse("https://example.com/robots.txt", text="User-agent: *\nDisallow: /private/\nSitemap: https://example.com/sitemap.xml\n")
        info = fetch_robots("https://example.com", session, "RioTest", 5)
        self.assertTrue(info.exists)
        self.assertEqual(info.declared_sitemaps, ["https://example.com/sitemap.xml"])
        self.assertFalse(info.allows("https://example.com/private/page", "RioTest"))

    def test_sitemap_parsing(self):
        session = Mock()
        session.get.return_value = FakeResponse("https://example.com/sitemap.xml", text="", content=b"<?xml version='1.0'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'><url><loc>https://example.com/a</loc></url><url><loc>https://example.com/b</loc></url></urlset>")
        urls, diagnostics = parse_sitemap("https://example.com/sitemap.xml", session, 5, "RioTest")
        self.assertEqual(urls, ["https://example.com/a", "https://example.com/b"])
        self.assertTrue(diagnostics["is_xml"])


class PageAuditTests(unittest.TestCase):
    def test_page_element_extraction(self):
        html = """<html lang='en'><head><title>Example Page</title><meta name='description' content='A useful description'><meta name='robots' content='index, follow'><link rel='canonical' href='/preferred/'><meta name='viewport' content='width=device-width'></head><body><h1>Main heading</h1><h2>Section</h2><h3>Detail</h3><a href='/about'>About</a><a href='https://outside.com'>Outside</a><img src='/image.jpg'><script type='application/ld+json'>{"@type":"Article"}</script></body></html>"""
        page = {"url": "https://example.com/page", "final_url": "https://example.com/page", "status": 200, "headers": {}, "html": html}
        result = PageAudit().audit(page, "https://example.com")
        self.assertEqual(result["title"], "Example Page")
        self.assertEqual(result["meta_description"], "A useful description")
        self.assertEqual(result["h1"], ["Main heading"])
        self.assertEqual(result["canonical"], "https://example.com/preferred")
        self.assertEqual(len(result["internal_links"]), 1)
        self.assertEqual(len(result["external_links"]), 1)
        self.assertTrue(result["images"][0]["missing_alt"])
        self.assertTrue(result["json_ld"])


class CrawlerTests(unittest.TestCase):
    def test_domain_restriction_duplicate_page_detection(self):
        session = Mock()
        def get(url, **kwargs):
            if url.endswith("robots.txt"):
                return FakeResponse(url, text="User-agent: *\nAllow: /\n")
            if url.endswith("sitemap.xml"):
                return FakeResponse(url, status=404, text="")
            if url.endswith("broken"):
                return FakeResponse(url, status=404, text="")
            return FakeResponse(url, text="<html><head><title>T</title><meta name='description' content='D'></head><body><a href='/'>Duplicate</a><a href='/broken'>Broken</a><a href='https://outside.com'>Outside</a></body></html>")
        session.get.side_effect = get
        crawler = Crawler(max_pages=100, delay=0, session=session)
        crawl = crawler.crawl("https://example.com")
        urls = [page["url"] for page in crawl["pages"]]
        self.assertEqual(urls.count("https://example.com/"), 1)
        self.assertTrue(all(not url.startswith("https://outside.com") for url in urls))


class AuditAndReportingTests(unittest.TestCase):
    def test_broken_link_and_duplicate_findings(self):
        crawl = {
            "start_url": "https://example.com",
            "robots": {"exists": True, "declared_sitemaps": [], "error": None, "content": "User-agent: *\nAllow: /"},
            "sitemap": {"declared": [], "checked": [], "errors": []},
            "sitemap_urls": [],
            "pages": [{"url": "https://example.com/a", "final_url": "https://example.com/a", "status": 200, "redirects": [], "headers": {}, "html": "<html lang='en'><head><title>Same</title><meta name='description' content='Same description'><link rel='canonical' href='https://example.com/a'></head><body><h1>Same H1</h1><a href='/missing'>Missing</a><meta name='viewport' content='width=device-width'></body></html>", "error": None}, {"url": "https://example.com/b", "final_url": "https://example.com/b", "status": 404, "redirects": [], "headers": {}, "html": "", "error": None}],
            "status_by_url": {"https://example.com/a": 200, "https://example.com/b": 404, "https://example.com/missing": 404},
            "successful_requests": 1,
            "failed_requests": 1,
        }
        audit = TechnicalAudit().audit(crawl)
        codes = {item["code"] for item in audit["issues"]}
        self.assertIn("HTTP_ERROR", codes)
        self.assertIn("BROKEN_INTERNAL_LINK", codes)

    def test_all_report_formats(self):
        crawl = {"start_url": "https://example.com", "pages": [], "successful_requests": 0, "failed_requests": 0}
        audit = {"pages": [], "issues": [], "health_score": 100, "health_score_explanation": "Diagnostic metric only"}
        result = {"audit_metadata": {"generated_at": "2026-01-01T00:00:00Z"}, "crawl": crawl, "audit": audit}
        with tempfile.TemporaryDirectory() as directory:
            html = str(Path(directory) / "audit.html")
            json = str(Path(directory) / "audit.json")
            csv = str(Path(directory) / "pages.csv")
            write_html_report(result, html)
            write_json_report(result, json)
            write_csv_report(audit, csv)
            self.assertIn("Rio Organic SEO Website Audit", Path(html).read_text())
            self.assertIn("audit_metadata", Path(json).read_text())
            self.assertIn("url,status,title", Path(csv).read_text())

    def test_cli_rejects_invalid_url(self):
        self.assertEqual(main(["--url", "not-a-url"]), 2)


if __name__ == "__main__":
    unittest.main()
