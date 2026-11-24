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


def cluster_keyword(keyword: str) -> str:
    text = keyword.lower()
    for cluster, markers in CLUSTER_RULES:
        if any(marker in text for marker in markers):
            return cluster
    return "Rio Private Transportation"


def cluster_keywords(keywords: list[dict]) -> dict[str, list[dict]]:
    clusters = {}
    for keyword in keywords:
        cluster = cluster_keyword(keyword["keyword"])
        clusters.setdefault(cluster, []).append(keyword)
    return clusters
