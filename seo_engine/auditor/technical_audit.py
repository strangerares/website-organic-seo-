from collections import Counter
from urllib.parse import urlsplit
from urllib import robotparser

from seo_engine.utils.url_utils import same_domain
from .issue_classifier import issue, SEVERITY_WEIGHT
from .page_audit import PageAudit


class TechnicalAudit:
    def __init__(self, session=None):
        self.page_audit = PageAudit()
        self.session = session

    def audit(self, crawl: dict):
        issues = []
        base_url = crawl["start_url"]
        audited_pages = []

        robots = crawl["robots"]
        if robots["exists"]:
            if not robots["declared_sitemaps"]:
                issues.append(issue("Low", "ROBOTS_NO_SITEMAP", "robots.txt does not declare an XML sitemap.", base_url.rstrip("/") + "/robots.txt", "A sitemap declaration helps crawlers discover the XML sitemap, though discovery is not required for crawling.", "Declare the canonical sitemap in robots.txt.", "Add one line such as 'Sitemap: https://example.com/sitemap.xml'."))
        else:
            issues.append(issue("Informational", "ROBOTS_NOT_FOUND", "A readable robots.txt was not found or could not be accessed.", base_url.rstrip("/") + "/robots.txt", "This engine could not verify crawling restrictions from the standard location.", "Review the robots.txt configuration and server response.", "Serve /robots.txt as a public text file if crawling instructions are needed."))

        sitemap_data = crawl["sitemap"]
        if not sitemap_data["declared"]:
            discovered_sitemap = [url for url in sitemap_data["checked"]]
            if not discovered_sitemap:
                issues.append(issue("Low", "SITEMAP_NOT_FOUND", "No accessible XML sitemap was discovered.", base_url, "A sitemap can improve URL discovery, but a missing sitemap does not itself prove a page is missing from search.", "Create and declare an XML sitemap if the site has indexable public pages.", "Generate a valid XML sitemap, submit it to supported webmaster tools, and declare it in robots.txt."))
        for error in sitemap_data["errors"]:
            issues.append(issue("Medium", "SITEMAP_ERROR", error["description"], error["url"] or base_url, "Sitemap defects can prevent URL discovery or introduce incorrect crawl targets.", "Correct the sitemap or access response.", "Use valid XML and keep sitemap URLs on the audited domain without server errors."))

        if robots["exists"]:
            robots_parser = robotparser.RobotFileParser()
            robots_parser.parse(robots["content"].splitlines())
            for sitemap_url in crawl["sitemap_urls"]:
                if not robots_parser.can_fetch(crawl.get("user_agent", "RioOrganicSEO/1.0"), sitemap_url):
                    issues.append(issue("High", "SITEMAP_URL_BLOCKED", "A sitemap URL is blocked by robots.txt.", sitemap_url, "A sitemap URL can be discoverable while the target page is disallowed to the audit crawler.", "Resolve the robots conflict or remove the URL from the sitemap.", "Allow the public page in robots.txt, or remove intentionally blocked URLs from the sitemap."))

        for sitemap_url in crawl["sitemap_urls"]:
            if not same_domain(sitemap_url, base_url):
                issues.append(issue("High", "SITEMAP_WRONG_DOMAIN", "A sitemap URL points outside the audited domain.", sitemap_url, "Cross-domain sitemap entries may not be treated as valid by crawlers.", "Remove or move out-of-domain sitemap entries.", "Use only canonical URLs for the audited site in the sitemap."))
                continue
            sitemap_status = crawl["status_by_url"].get(sitemap_url)
            if sitemap_status is not None and sitemap_status >= 400:
                issues.append(issue("High", "SITEMAP_URL_ERROR", f"A sitemap URL returns HTTP {sitemap_status}.", sitemap_url, "An errored sitemap URL does not provide a useful crawlable public page.", "Remove the URL or restore the destination.", "Fix the server response or redirect obsolete URLs intentionally before keeping them in the sitemap."))

        page_results = []
        for page in crawl["pages"]:
            data = self.page_audit.audit(page, base_url, self.session)
            row = {"url": page["final_url"], "status": page["status"]}
            row.update(data)
            audited_pages.append(row)

            if page["status"] is None:
                issues.append(issue("High", "REQUEST_FAILED", "The page request failed.", page["url"], "The page could not be measured and may be unavailable to crawlers.", "Verify DNS, TLS, server availability, and request restrictions.", "Resolve the network or server error, then rerun the audit."))
            elif page["status"] >= 400:
                issues.append(issue("High", "HTTP_ERROR", f"The page returned HTTP {page['status']}.", page["final_url"], "An error response is not a normal indexable page response.", "Restore the page or redirect obsolete URLs intentionally.", "Fix server routing, or use a suitable 301 redirect when replacing a permanent URL."))
            elif 300 <= page["status"] < 400:
                issues.append(issue("Medium", "REDIRECT_RESPONSE", f"The page returned a redirecting HTTP status ({page['status']}).", page["final_url"], "Redirect chains or unnecessary redirects may waste crawl budget.", "Prefer one direct redirect to the final canonical URL.", "Replace internal redirect targets with their final URLs and remove chains."))

            if page["redirects"]:
                issues.append(issue("Low", "REDIRECT", f"The URL redirected to {row['url']}.", page["url"], "Redirects can add an extra request but are normal for canonicalization.", "Use a direct canonical URL when practical and avoid redirect chains.", "Update links and sitemap entries to the final URL, and consolidate unnecessary redirect hops."))

            if not data["title"]:
                issues.append(issue("High", "MISSING_TITLE", "The page has no title element.", row["url"], "Titles communicate the page topic to users and crawlers.", "Add a concise, unique, descriptive title.", "Add a <title> element inside <head>."))
            elif data["title_length"] > 60:
                issues.append(issue("Low", "LONG_TITLE", f"The title is {data['title_length']} characters long.", row["url"], "Long titles may be shortened in search-result displays.", "Keep the title concise while preserving the most important message.", "Shorten the title and avoid repetitive or keyword-stuffed text."))

            if not data["meta_description"]:
                issues.append(issue("Medium", "MISSING_META_DESCRIPTION", "The page has no meta description.", row["url"], "A meta description is not an indexing requirement, but it can provide useful SERP copy.", "Write a unique summary that accurately describes the page.", "Add <meta name=\"description\" content=\"...\"> inside <head>."))
            elif data["description_length"] > 160:
                issues.append(issue("Low", "LONG_META_DESCRIPTION", f"The meta description is {data['description_length']} characters long.", row["url"], "Long descriptions may be truncated or rewritten in search results.", "Keep the description concise and specific.", "Reduce the description to a practical length and retain the page's key value."))

            if not data["h1"]:
                issues.append(issue("Medium", "MISSING_H1", "The page has no H1 heading.", row["url"], "A clear H1 helps describe the primary content topic.", "Add one descriptive H1.", "Place a single primary <h1> near the start of the main content."))
            elif len(data["h1"]) > 1:
                issues.append(issue("Medium", "MULTIPLE_H1", f"The page has {len(data['h1'])} H1 headings.", row["url"], "Multiple H1s can make the primary page topic less clear, though HTML5 permits broader heading patterns.", "Use one primary H1 unless there is a strong semantic reason for more.", "Convert secondary H1 elements to H2 or other appropriate headings."))

            if not data["canonical"]:
                issues.append(issue("Medium", "MISSING_CANONICAL", "The page has no canonical tag.", row["url"], "Canonical guidance helps consolidate duplicate or parameterized versions.", "Add a self-referencing canonical or the approved preferred URL.", "Add <link rel=\"canonical\" href=\"https://example.com/page/\"> in <head>."))
            elif not same_domain(data["canonical"], base_url):
                issues.append(issue("High", "CANONICAL_WRONG_DOMAIN", "The canonical URL points outside the audited domain.", row["url"], "An external canonical may indicate misconfiguration or migration intent.", "Verify the canonical target and use the intended public URL.", "Set the canonical to the preferred URL for this page on the correct domain."))

            if data["noindex"]:
                issues.append(issue("Informational", "NOINDEX", "The page contains a noindex directive.", row["url"], "Noindex tells crawlers not to retain the page in search indexes, but it may affect only supported crawlers.", "Verify that the directive is intentional.", "Remove noindex from public pages that should be eligible for indexing, after separate indexing decisions are made."))
            if data["nofollow"]:
                issues.append(issue("Informational", "NOFOLLOW", "The page contains a nofollow directive.", row["url"], "Nofollow here limits crawlers' link-following instructions for the page's links.", "Verify whether the directive is needed.", "Remove or replace the directive if it does not match the page intent."))

            if not data["language"]:
                issues.append(issue("Low", "MISSING_LANGUAGE", "The HTML language declaration is missing.", row["url"], "A language declaration gives assistive technology and crawlers an explicit language signal.", "Declare the page language.", "Add lang=\"en\" or the appropriate language code to the <html> element."))
            if not data["viewport"]:
                issues.append(issue("Medium", "MISSING_VIEWPORT", "The mobile viewport meta declaration is missing.", row["url"], "A viewport declaration is important for proper mobile rendering.", "Add a standard viewport declaration.", "Add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">."))
            if not data["https"]:
                issues.append(issue("High", "NOT_HTTPS", "The final URL does not use HTTPS.", row["url"], "HTTPS is the modern secure transport baseline and avoids mixed/insecure delivery.", "Serve the page over HTTPS and redirect HTTP permanently.", "Install/configure TLS and canonicalize internal HTTP URLs to HTTPS."))

            url_parts = urlsplit(row["url"])
            if url_parts.query:
                issues.append(issue("Low", "URL_QUERY_PARAMETERS", "The crawled URL contains query parameters.", row["url"], "Parameter variants can create duplicate URLs or crawl configuration complexity.", "Verify whether the parameters change content and set canonical or routing rules.", "Use clean paths where appropriate and return a clear canonical URL for parameter variants."))
            if url_parts.path and ("_" in url_parts.path or any(character.isupper() for character in url_parts.path)):
                issues.append(issue("Low", "URL_STRUCTURE", "The URL uses uppercase characters or underscores.", row["url"], "Consistent, descriptive lower-case URL paths are easier to maintain and less prone to case-related duplicates.", "Standardize path conventions.", "Use lower-case hyphen-separated path segments and redirect legacy variants intentionally."))

            if not data["json_ld"]:
                issues.append(issue("Informational", "NO_JSON_LD", "No JSON-LD structured data was detected.", row["url"], "Structured data is optional and absence does not create a technical error.", "Add relevant, accurate structured data only where it describes visible content.", "Use supported Schema.org types with JSON-LD and validate the output; do not add markup for content that is not present."))

            for image in data["images"]:
                if image["missing_alt"]:
                    issues.append(issue("Medium", "IMAGE_MISSING_ALT", "An image is missing an ALT attribute or has an empty ALT value.", row["url"], "ALT text communicates image content to users and may affect accessible interpretation.", "Provide useful alternative text or mark decorative images intentionally.", "Set alt=\"descriptive text\" on meaningful images or alt=\"\" on decorative images."))

            for link in data["internal_links"]:
                status = crawl["status_by_url"].get(link["url"])
                if status is not None and status >= 400:
                    issues.append(issue("High", "BROKEN_INTERNAL_LINK", f"Internal link returns HTTP {status}.", row["url"], "Broken links create poor user experiences and wasted crawl paths.", "Remove or replace the broken link.", f"Update the link to a working page or redirect it intentionally: {link['url']}"))

        titles = Counter(page["title"] for page in audited_pages if page["title"])
        descriptions = Counter(page["meta_description"] for page in audited_pages if page["meta_description"])
        h1s = Counter(h for page in audited_pages for h in page["h1"])

        for value, count in titles.items():
            if count > 1:
                urls = [page["url"] for page in audited_pages if page["title"] == value]
                issues.append(issue("Medium", "DUPLICATE_TITLE", f"The title is duplicated across {count} audited pages.", ", ".join(urls), "Duplicate titles provide weaker page-topic distinction.", "Give each page a unique, descriptive title.", "Replace duplicate title text with unique page-specific titles."))
        for value, count in descriptions.items():
            if count > 1:
                urls = [page["url"] for page in audited_pages if page["meta_description"] == value]
                issues.append(issue("Low", "DUPLICATE_META_DESCRIPTION", f"The meta description is duplicated across {count} audited pages.", ", ".join(urls), "Duplicate descriptions can make repeated pages harder to distinguish in search results.", "Write unique descriptions for unique pages.", "Replace duplicate description text with summaries tailored to each page."))
        for value, count in h1s.items():
            if count > 1:
                urls = [page["url"] for page in audited_pages if value in page["h1"]]
                issues.append(issue("Low", "DUPLICATE_H1", f"The H1 text is duplicated across {count} audited pages.", ", ".join(urls), "Repeated H1 copy may signal template problems or low page differentiation.", "Make H1 text specific to the page's main content.", "Use page-specific H1 text instead of a repeated generic heading."))

        score = max(0, 100 - sum(SEVERITY_WEIGHT[item["severity"]] for item in issues))
        return {
            "pages": audited_pages,
            "issues": issues,
            "health_score": score,
            "health_score_explanation": "This is a Rio diagnostic metric: 100 minus weighted counts of detected findings (Critical 15, High 8, Medium 4, Low 2, Informational 1). It is not a Google ranking score.",
        }
