import re


def classify_intent(keyword: str) -> str:
    text = " ".join(re.findall(r"[a-z0-9]+", keyword.casefold()))
    words = set(text.split())

    if "rio private driver" in text:
        return "Navigational"
    if (
        text.startswith(("how ", "what ", "why ", "where ", "when ", "who "))
        or words.intersection({"guide", "guides", "tips", "itinerary", "itineraries", "safety"})
        or "things to do" in text
        or text.startswith(("can i ", "is ", "are "))
    ):
        return "Informational"
    if words.intersection({
        "best", "top", "compare", "comparison", "vs", "versus", "company",
        "companies", "service", "services", "agency", "provider", "providers",
        "cost", "price", "prices",
    }):
        return "Commercial"
    if words.intersection({"book", "booking", "hire", "reservation", "reservations", "quote", "quotes"}):
        return "Transactional"
    if words.intersection({"transfer", "transfers", "transportation", "driver", "drivers", "tour", "tours"}):
        return "Transactional"
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
