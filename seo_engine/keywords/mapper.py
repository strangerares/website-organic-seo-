import re
import unicodedata
from typing import Optional
from urllib.parse import urlsplit

from seo_engine.auditor.page_audit import PageAudit
from seo_engine.utils.url_utils import same_domain


PAGE_MAP = (
    ("GIG Airport", "https://rioprivatedriver.com/gig-airport-transfer/", "Create GIG airport transfer landing page"),
    ("SDU Airport", "https://rioprivatedriver.com/sdu-airport-transfer/", "Create SDU airport transfer landing page"),
    ("Búzios", "https://rioprivatedriver.com/rio-to-buzios-transfer/", "Create Rio to Búzios transfer landing page"),
    ("Cabo Frio", "https://rioprivatedriver.com/rio-to-cabo-frio-transfer/", "Create Rio to Cabo Frio transfer landing page"),
    ("Arraial do Cabo", "https://rioprivatedriver.com/rio-to-arraial-do-cabo-transfer/", "Create Rio to Arraial do Cabo transfer landing page"),
    ("Private Tours", "https://rioprivatedriver.com/our-services/", "Target existing private-tour or add a dedicated tours page"),
    ("English-Speaking Service", "https://rioprivatedriver.com/", "Create or optimize an English-speaking private driver page"),
    ("Airport Transfers", "https://rioprivatedriver.com/our-services/", "Create a dedicated airport transfer landing page"),
    ("Private Drivers", "https://rioprivatedriver.com/", "Create a Rio private driver service landing page"),
    ("Rio Transportation", "https://rioprivatedriver.com/our-services/", "Create or optimize a private transportation service page"),
)


STOP_WORDS = {"a", "an", "and", "at", "by", "de", "do", "da", "for", "from", "in", "of", "on", "the", "to", "with"}


def _tokens(value: str) -> set[str]:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return {token for token in re.findall(r"[a-z0-9]+", without_accents) if token not in STOP_WORDS}


def _live_page_match(keyword: str, pages: list[dict], site_url: str):
    keyword_tokens = _tokens(keyword)
    if not keyword_tokens:
        return None

    candidates = []
    for page in pages:
        if page.get("status") is None or page["status"] >= 400:
            continue
        final_url = page.get("final_url") or page.get("url", "")
        if not final_url or not same_domain(final_url, site_url):
            continue

        audited = PageAudit().audit(page, site_url)
        canonical = audited["canonical"]
        if audited["noindex"] or (canonical and not same_domain(canonical, site_url)):
            continue
        target_url = canonical or final_url
        if not same_domain(target_url, site_url):
            continue

        parts = urlsplit(target_url)
        fields = (
            (audited["title"], 4),
            (" ".join(audited["h1"]), 3),
            (" ".join(audited["h2"]), 2),
            (audited["meta_description"], 1),
            (parts.path.replace("-", " ").replace("/", " "), 2),
        )
        field_tokens = [(_tokens(text), weight) for text, weight in fields]
        matched_weight = sum(
            max((weight for tokens, weight in field_tokens if token in tokens), default=0)
            for token in keyword_tokens
        )
        matches = sum(
            any(token in tokens for tokens, _ in field_tokens)
            for token in keyword_tokens
        )
        coverage = matched_weight / (4 * len(keyword_tokens))
        minimum_matches = min(2, len(keyword_tokens))
        if matches >= minimum_matches and coverage >= 0.5:
            candidates.append((coverage, matched_weight, target_url))

    if candidates:
        return max(candidates)[2]
    return None


def map_keyword(
    cluster: str,
    keyword: str,
    crawled_pages: Optional[list[dict]] = None,
    site_url: str = "https://rioprivatedriver.com/",
) -> tuple[str, str, str]:
    if crawled_pages:
        live_page = _live_page_match(keyword, crawled_pages, site_url)
        if live_page:
            return live_page, "", ""

    for rule_cluster, target, missing in PAGE_MAP:
        if cluster == rule_cluster:
            existing = rule_cluster in ("Private Tours", "Airport Transfers", "Rio Transportation")
            return target, missing if not existing else "", ""

    if "rio private driver" in keyword.lower():
        return "https://rioprivatedriver.com/", "", ""
    return "https://rioprivatedriver.com/our-services/", "Create or optimize a private transportation service landing page", ""


def recommend_article(cluster: str, keyword: str) -> str:
    text = keyword.lower()
    if "transfer" in text or "airport" in text:
        return f"Article: Complete guide to {keyword} for English-speaking visitors"
    if "tour" in text:
        return f"Article: Best ways to plan {keyword} in Rio"
    if "buzios" in text or "búzios" in text:
        return "Article: Rio to Búzios private transfer planning guide"
    if "cabo frio" in text:
        return "Article: Rio to Cabo Frio private transfer guide"
    if "arraial" in text:
        return "Article: Rio to Arraial do Cabo private transfer guide"
    return f"Article: {cluster} guide for Rio visitors"
