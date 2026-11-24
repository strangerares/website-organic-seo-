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


def map_keyword(cluster: str, keyword: str) -> tuple[str, str, str]:
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
