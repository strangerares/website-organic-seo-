import json
import os
from typing import Optional

import requests


class OpportunityEvaluator:
    def __init__(self, session=None):
        self.session = session or requests.Session()

    def evaluate(self, prospect: dict) -> dict:
        ai_result = self._evaluate_with_ai(prospect)
        if ai_result:
            ai_result = normalize_evaluation(ai_result)
            ai_result["score"] = max(0, min(100, int(ai_result["score"])))
            return ai_result
        return self._evaluate_heuristically(prospect)

    def _evaluate_heuristically(self, prospect: dict) -> dict:
        text = " ".join(
            str(prospect.get(field, "") or "")
            for field in (
                "page_title", "meta_description", "content_summary",
                "website_category", "opportunity_type",
            )
        ).lower()

        score = 25
        if "rio de janeiro" in text:
            score += 25
        if "brazil" in text:
            score += 15
        if any(term in text for term in ("usa", "united states", "canada", "english")):
            score += 15
        if any(term in text for term in ("travel", "tourism", "tour", "hotel", "expat", "guide")):
            score += 10
        if any(term in text for term in ("transfer", "transport", "private driver", "airport")):
            score += 10
        if prospect.get("public_email"):
            score += 5

        score = min(score, 100)
        if score >= 75:
            priority = "High"
        elif score >= 50:
            priority = "Medium"
        else:
            priority = "Low"

        concerns = []
        if not prospect.get("content_summary"):
            concerns.append("Limited publicly accessible content was available")
        if not prospect.get("public_email"):
            concerns.append("No public email was found; use a published contact page")
        if score < 50:
            concerns.append("Topical relevance is uncertain and should be verified manually")

        return {
            "score": score,
            "reasoning": "Rule-based relevance assessment from publicly accessible page metadata and content.",
            "outreach_angle": "Suggest Rio Private Driver as a useful English-speaking private transportation resource for Rio travelers.",
            "suggested_target_page": "https://rioprivatedriver.com/",
            "potential_concerns": "; ".join(concerns) if concerns else "No immediate concerns from accessible page data.",
            "priority": priority,
        }

    def _evaluate_with_ai(self, prospect: dict) -> Optional[dict]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        endpoint = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
        model = os.getenv("OPENAI_API_MODEL", "gpt-4o-mini")
        prompt = (
            "Evaluate this prospect for legitimate editorial backlinks to Rio Private Driver. "
            "Score 0-100 and return JSON only with keys score, reasoning, outreach_angle, "
            "suggested_target_page, potential_concerns, priority (High/Medium/Low). "
            "Do not reward spam, directories, paid-link schemes, or irrelevant sites.\n"
            + json.dumps(prospect, ensure_ascii=False)
        )
        try:
            response = self.session.post(
                endpoint,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except (requests.RequestException, KeyError, ValueError, json.JSONDecodeError):
            return None


def normalize_evaluation(result: dict) -> dict:
    concerns = result.get("potential_concerns", "")
    if isinstance(concerns, list):
        concerns = "; ".join(str(item) for item in concerns)
    return {
        "score": int(result.get("score", 0)),
        "reasoning": str(result.get("reasoning", "")),
        "outreach_angle": str(result.get("outreach_angle", "")),
        "suggested_target_page": str(result.get("suggested_target_page", "https://rioprivatedriver.com/")),
        "potential_concerns": str(concerns),
        "priority": str(result.get("priority", "Low")).title(),
    }
