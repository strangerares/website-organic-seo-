import json
import os

import requests

from .intent import classify_intent, is_long_tail, generate_questions


class KeywordEvaluator:
    def __init__(self, session=None):
        self.session = session or requests.Session()

    def enrich(self, keyword: dict) -> dict:
        text = keyword["keyword"]
        intent = classify_intent(text)
        long_tail = is_long_tail(text)
        score = 35
        if intent in ("Transactional", "Commercial"):
            score += 30
        elif intent == "Navigational":
            score += 15
        else:
            score += 10
        if long_tail:
            score += 20
        if any(term in text.lower() for term in ("private", "transfer", "airport", "tours", "transportation", "driver")):
            score += 10
        score = min(score, 100)

        result = dict(keyword)
        result.update({
            "search_intent": intent,
            "long_tail": int(long_tail),
            "opportunity_score": score,
            "related_keywords": "; ".join(generate_questions(text)),
            "ai_suggestion": 0,
        })
        return result

    def ai_expand(self, seed_keywords: list[str]) -> list[dict]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return []
        endpoint = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
        model = os.getenv("OPENAI_API_MODEL", "gpt-4o-mini")
        prompt = (
            "Generate SEO keyword suggestions for Rio Private Driver. Return JSON only with key keywords, "
            "an array of objects containing keyword, search_intent, long_tail, cluster, recommended_target_page, "
            "missing_page, article_opportunity, and reasoning. These are AI suggestions, not verified demand. "
            "Do not invent search volume, CPC, difficulty, competition, rankings, or business facts.\nSeeds: "
            + json.dumps(seed_keywords)
        )
        try:
            response = self.session.post(
                endpoint,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "temperature": 0, "response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": prompt}]},
                timeout=60,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            payload = json.loads(content)
            return payload.get("keywords", [])
        except (requests.RequestException, KeyError, ValueError, json.JSONDecodeError):
            return []


def ai_suggestion_record(item: dict) -> dict:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    keyword = " ".join(str(item.get("keyword", "")).strip().split()).lower()
    if not keyword:
        return {}
    return {
        "keyword": keyword,
        "country": "US/Canada",
        "language": "English",
        "search_intent": str(item.get("search_intent", "Informational")).title(),
        "search_volume": "Unavailable",
        "keyword_difficulty": "Unavailable",
        "cpc": "Unavailable",
        "competition": "Unavailable",
        "source": "OpenAI-compatible AI",
        "data_type": "AI-generated suggestion",
        "date_retrieved": now,
        "related_keywords": "",
        "recommended_target_page": item.get("recommended_target_page") or "https://rioprivatedriver.com/",
        "opportunity_score": None,
        "long_tail": int(bool(item.get("long_tail", False))),
        "topic_cluster": item.get("cluster") or "Rio Private Transportation",
        "ai_suggestion": 1,
        "ai_reasoning": item.get("reasoning") or "",
        "missing_page": item.get("missing_page") or "",
        "article_opportunity": item.get("article_opportunity") or "",
        "created_at": now,
    }
