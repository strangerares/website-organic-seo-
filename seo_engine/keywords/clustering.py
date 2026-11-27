import re
import unicodedata


CLUSTER_RULES = (
    ("GIG Airport", ("gig", "gal. da costa e silva", "galeao", "galeão")),
    ("SDU Airport", ("sdu", "santos dumont")),
    ("Búzios", ("buzios", "búzios")),
    ("Cabo Frio", ("cabo frio",)),
    ("Arraial do Cabo", ("arraial do cabo",)),
    ("Private Tours", ("private tour", "private tours", "sightseeing")),
    ("English-Speaking Service", ("english-speaking", "english speaking")),
    ("Airport Transfers", ("airport transfer", "airport private transfer", "airport transportation")),
    ("Private Drivers", ("private driver", "private drivers", "chauffeur")),
    ("Rio Transportation", ("private transportation", "transportation in rio")),
)


def _normalized_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", without_accents).strip()


def cluster_keyword(keyword: str) -> str:
    text = f" {_normalized_text(keyword)} "
    for cluster, markers in CLUSTER_RULES:
        if any(f" {_normalized_text(marker)} " in text for marker in markers):
            return cluster
    return "Rio Private Transportation"


def cluster_keywords(keywords: list[dict]) -> dict[str, list[dict]]:
    clusters = {}
    for keyword in keywords:
        cluster = cluster_keyword(keyword["keyword"])
        clusters.setdefault(cluster, []).append(keyword)
    return clusters
