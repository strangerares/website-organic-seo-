import csv
from datetime import datetime, timezone
from pathlib import Path


SEED_KEYWORDS = (
    "Private driver Rio de Janeiro",
    "Rio de Janeiro airport transfer",
    "GIG airport private transfer",
    "SDU airport transfer",
    "Rio to Búzios private transfer",
    "Rio to Cabo Frio private transfer",
    "Rio to Arraial do Cabo private transfer",
    "English-speaking driver Rio de Janeiro",
    "Private transportation Rio de Janeiro",
    "Rio de Janeiro private tours",
)

METRIC_FIELDS = ("search_volume", "keyword_difficulty", "cpc", "competition")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def normalize_keyword(value: str) -> str:
    return " ".join(str(value or "").strip().split()).lower()


def make_manual_keyword(keyword: str) -> dict:
    normalized = normalize_keyword(keyword)
    if not normalized:
        raise ValueError("Keyword cannot be empty")
    now = utc_now()
    return {
        "keyword": normalized,
        "country": "US/Canada",
        "language": "English",
        "search_volume": "Unavailable",
        "keyword_difficulty": "Unavailable",
        "cpc": "Unavailable",
        "competition": "Unavailable",
        "source": "Manual entry",
        "data_type": "Manually entered",
        "date_retrieved": now,
        "created_at": now,
    }


def import_keyword_csv(path: str, default_source: str = "CSV import") -> list[dict]:
    rows = []
    with open(path, "r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")

        def first(row, names):
            for name in names:
                if name in row and str(row[name]).strip():
                    return str(row[name]).strip()
            return ""

        for row in reader:
            keyword = first(row, ("keyword", "Keyword", "search_term", "Search Term", "query"))
            if not keyword:
                continue
            now = utc_now()
            metric_source = first(row, ("source", "Source", "provider", "Provider")) or default_source
            data_type = first(row, ("data_type", "Data Type", "metric_type")) or "Imported provider data"
            date_retrieved = first(row, ("date_retrieved", "Date Retrieved", "date", "Date")) or now

            def metric(names):
                value = first(row, names)
                return value if value else "Unavailable"

            rows.append({
                "keyword": normalize_keyword(keyword),
                "country": first(row, ("country", "Country", "geo")) or "Unavailable",
                "language": first(row, ("language", "Language")) or "Unavailable",
                "search_volume": metric(("search_volume", "Search Volume", "volume")),
                "keyword_difficulty": metric(("keyword_difficulty", "Keyword Difficulty", "difficulty", "KD")),
                "cpc": metric(("cpc", "CPC")),
                "competition": metric(("competition", "Competition")),
                "source": metric_source,
                "data_type": data_type,
                "date_retrieved": date_retrieved,
                "related_keywords": first(row, ("related_keywords", "Related Keywords")),
                "created_at": now,
            })
    return rows


def seed_keywords() -> list[dict]:
    return [make_manual_keyword(keyword) for keyword in SEED_KEYWORDS]
