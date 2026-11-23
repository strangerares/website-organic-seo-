import xml.etree.ElementTree as ET

import requests


def parse_sitemap(url: str, session: requests.Session, timeout: float, user_agent: str, max_depth: int = 3):
    """Fetch a sitemap or sitemap index and return entries plus diagnostics."""
    entries = []
    diagnostics = {"urls_checked": [], "errors": [], "is_xml": False}

    def fetch(current: str, depth: int):
        if depth > max_depth:
            return
        diagnostics["urls_checked"].append(current)
        try:
            response = session.get(current, timeout=timeout, headers={"User-Agent": user_agent})
            if response.status_code >= 400:
                diagnostics["errors"].append({"url": current, "status": response.status_code, "description": "Sitemap could not be accessed"})
                return
            root = ET.fromstring(response.content)
            diagnostics["is_xml"] = True
        except (requests.RequestException, ET.ParseError) as exc:
            diagnostics["errors"].append({"url": current, "status": None, "description": str(exc)})
            return

        tag_name = root.tag.rsplit("}", 1)[-1]
        for child in root:
            child_name = child.tag.rsplit("}", 1)[-1]
            if child_name in ("url", "sitemap"):
                loc = next((node.text.strip() for node in child if node.tag.rsplit("}", 1)[-1] == "loc" and node.text), None)
                if loc:
                    if tag_name == "sitemapindex":
                        fetch(loc, depth + 1)
                    else:
                        entries.append(loc)

    fetch(url, 0)
    return list(dict.fromkeys(entries)), diagnostics
