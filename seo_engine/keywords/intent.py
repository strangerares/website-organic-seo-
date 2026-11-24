def classify_intent(keyword: str) -> str:
    text = keyword.lower()
    informational_markers = (
        "how", "what", "why", "guide", "tips", "best", "things to do",
        "itinerary", "cost", "safety", "where", "can i", "is ",
    )
    navigational_markers = ("rio private driver", "website", "official", "login", "booking")
    transactional_markers = (
        "book", "booking", "hire", "reservation", "quote", "price", "cost",
        "transfer", "transportation", "driver", "private tours", "private tour",
    )
    commercial_markers = (
        "best", "top", "compare", "comparison", "company", "companies",
        "service", "services", "agency", "provider",
    )

    if "rio private driver" in text:
        return "Navigational"
    if any(marker in text for marker in transactional_markers):
        return "Transactional"
    if any(marker in text for marker in commercial_markers):
        return "Commercial"
    if any(marker in text for marker in informational_markers):
        return "Informational"
    return "Informational"


def is_long_tail(keyword: str) -> bool:
    return len(keyword.strip().split()) >= 4


def generate_questions(keyword: str) -> list[str]:
    root = keyword.strip()
    if not root:
        return []
    return [
        f"How much does {root} cost?",
        f"What is included with {root}?",
        f"How do I book {root}?",
        f"Is {root} suitable for English-speaking travelers?",
    ]
