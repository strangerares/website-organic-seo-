import csv
from datetime import datetime, timezone
from typing import Iterable, Protocol
from urllib.parse import urlsplit

from seo_engine.utils.url_utils import normalize_url, validate_url


TARGET_URL = "https://rioprivatedriver.com"


class SearchProvider(Protocol):
    def search(self, query: str) -> Iterable[dict]: ...


class CSVSearchProvider:
    """Provider-independent search import adapter for CSV/API-exported rows."""

    def __init__(self, csv_path: str):
        self.csv_path = csv_path

    def search(self, query: str) -> Iterable[dict]:
        del query
        with open(self.csv_path, "r", newline="", encoding="utf-8-sig") as handle:
            yield from csv.DictReader(handle)


def generate_search_queries() -> list[str]:
    return [
        "Rio de Janeiro travel blog",
        "Brazil travel guide English USA",
        "Brazil travel guide English Canada",
        "USA travel agency Brazil Rio de Janeiro",
        "Canada travel agency Brazil Rio de Janeiro",
        "Rio de Janeiro tourism resources",
        "English language Brazil expat website Rio",
        "Rio de Janeiro hotel accommodation guide",
        "Rio airport transfer private transportation guide",
        "travel resource page Rio de Janeiro recommendations",
        "Rio de Janeiro guest post travel article",
        "Brazil travel partnership private transfer",
    ]


def normalized_domain(page_url: str) -> str:
    return (urlsplit(page_url).hostname or "").lower().rstrip(".")


def imported_prospect(url: str, source: str = "Manual import") -> dict:
    normalized = validate_url(url)
    return {
        "domain": normalized_domain(normalized),
        "page_url": normalize_url(normalized),
        "discovery_source": source,
        "date_discovered": datetime.now(timezone.utc).isoformat(),
    }


def import_csv(csv_path: str) -> list[dict]:
    with open(csv_path, "r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")

        url_columns = ("page_url", "url", "prospect_url", "Page URL", "URL")
        source_columns = ("source", "discovery_source", "Source", "Discovery Source")
        name_columns = ("website_name", "name", "Website Name", "Website")

        def first_value(row: dict, names: tuple[str, ...]):
            for name in names:
                if name in row and row[name]:
                    return str(row[name]).strip()
            return ""

        prospects = []
        for row in reader:
            raw_url = first_value(row, url_columns)
            if not raw_url:
                continue
            try:
                prospect = imported_prospect(raw_url, first_value(row, source_columns) or "CSV import")
            except ValueError:
                continue
            prospect["website_name"] = first_value(row, name_columns)
            prospects.append(prospect)
        return prospects
