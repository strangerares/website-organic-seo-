import json

from bs4 import BeautifulSoup

from seo_engine.utils.url_utils import absolute_url, same_domain


class PageAudit:
    def audit(self, page: dict, base_url: str, session=None, timeout=15.0):
        soup = BeautifulSoup(page.get("html", "") or "", "html.parser")
        title_tag = soup.find("title")
        title = title_tag.get_text(" ", strip=True) if title_tag else ""

        description = ""
        for meta in soup.find_all("meta"):
            if (meta.get("name") or meta.get("property") or "").lower() == "description":
                description = meta.get("content", "").strip()
                if description:
                    break

        h1 = [tag.get_text(" ", strip=True) for tag in soup.find_all("h1")]
        h2 = [tag.get_text(" ", strip=True) for tag in soup.find_all("h2")]
        h3 = [tag.get_text(" ", strip=True) for tag in soup.find_all("h3")]

        canonical = ""
        for link in soup.find_all("link", rel=True):
            rel = " ".join(link.get("rel", [])).lower()
            if "canonical" in rel:
                canonical = absolute_url(page["final_url"], link.get("href", ""))
                break

        meta_robots = ""
        noindex = False
        nofollow = False
        for meta in soup.find_all("meta"):
            if (meta.get("name") or "").lower() == "robots":
                meta_robots = meta.get("content", "").strip()
                directives = {part.strip().lower() for part in meta_robots.split(",")}
                noindex = noindex or "noindex" in directives
                nofollow = nofollow or "nofollow" in directives

        internal_links = []
        external_links = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            resolved = absolute_url(page["final_url"], href)
            if not resolved:
                continue
            item = {"url": resolved, "text": anchor.get_text(" ", strip=True)}
            if same_domain(resolved, base_url):
                internal_links.append(item)
            else:
                external_links.append(item)

        images = []
        for image in soup.find_all("img"):
            src = absolute_url(page["final_url"], image.get("src", ""))
            if not src:
                continue
            alt = image.get("alt")
            file_size = None
            if session is not None and same_domain(src, base_url):
                try:
                    response = session.head(src, timeout=timeout, allow_redirects=True)
                    value = response.headers.get("Content-Length")
                    if value and value.isdigit():
                        file_size = int(value)
                except Exception:
                    pass
            images.append({
                "src": src,
                "alt": alt,
                "missing_alt": alt is None or not alt.strip(),
                "width": image.get("width"),
                "height": image.get("height"),
                "file_size_bytes": file_size,
            })

        json_ld = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                json_ld.append(json.loads(script.string or ""))
            except (json.JSONDecodeError, TypeError):
                json_ld.append({"parse_error": True})

        html_tag = soup.find("html")
        language = html_tag.get("lang", "") if html_tag else ""
        viewport = ""
        for meta in soup.find_all("meta"):
            if (meta.get("name") or "").lower() == "viewport":
                viewport = meta.get("content", "")
                break

        x_robots = page.get("headers", {}).get("X-Robots-Tag", "")
        return {
            "title": title,
            "title_length": len(title),
            "meta_description": description,
            "description_length": len(description),
            "h1": h1,
            "h2": h2,
            "h3": h3,
            "canonical": canonical,
            "meta_robots": meta_robots,
            "x_robots_tag": x_robots,
            "noindex": noindex or "noindex" in x_robots.lower(),
            "nofollow": nofollow or "nofollow" in x_robots.lower(),
            "internal_links": internal_links,
            "external_links": external_links,
            "images": images,
            "json_ld": json_ld,
            "language": language,
            "viewport": viewport,
            "https": str(page["final_url"]).lower().startswith("https://"),
        }
