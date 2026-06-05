import logging
import uuid
from dataclasses import dataclass, field

from google import genai

from src.sources.base import Event

logger = logging.getLogger(__name__)


@dataclass
class AlertConfig:
    id: uuid.UUID
    keywords: list[str] = field(default_factory=list)
    topic: str | None = None
    use_llm: bool = False
    threshold: float = 0.7
    is_active: bool = True


@dataclass
class AlertMatch:
    alert_id: uuid.UUID
    event: Event
    matched_by: str  # "keyword" or "llm"
    relevance_score: float | None = None


class KeywordMatcher:
    def matches(self, event: Event, keywords: list[str]) -> bool:
        if not keywords:
            return False
        text = f"{event.title} {event.description}".lower()
        return any(kw.lower() in text for kw in keywords)


class LLMRelevanceScorer:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def score(self, event: Event, topic: str) -> float:
        prompt = (
            f'Rate the relevance of this news article to the topic "{topic}" '
            f"on a scale of 0.0 to 1.0.\n"
            f"Return only a decimal number, nothing else.\n\n"
            f"Title: {event.title}\n"
            f"Description: {event.description}"
        )
        try:
            response = self._client.models.generate_content(
                model=self._model, contents=prompt
            )
            return max(0.0, min(1.0, float(response.text.strip())))
        except (ValueError, AttributeError) as e:
            logger.warning("LLM scoring failed, defaulting to 0.0: %s", e)
            return 0.0
        except Exception as e:
            logger.error("Unexpected LLM error: %s", e)
            return 0.0


class AlertMatcher:
    def __init__(self, llm_scorer: LLMRelevanceScorer | None = None):
        self._keyword = KeywordMatcher()
        self._llm = llm_scorer

    def match(self, events: list[Event], alerts: list[AlertConfig]) -> list[AlertMatch]:
        return [
            m
            for alert in alerts
            if alert.is_active
            for event in events
            for m in [self._check(event, alert)]
            if m is not None
        ]

    def _check(self, event: Event, alert: AlertConfig) -> AlertMatch | None:
        if self._keyword.matches(event, alert.keywords):
            return AlertMatch(alert_id=alert.id, event=event, matched_by="keyword")

        if alert.use_llm and self._llm and alert.topic:
            score = self._llm.score(event, alert.topic)
            if score >= alert.threshold:
                return AlertMatch(
                    alert_id=alert.id,
                    event=event,
                    matched_by="llm",
                    relevance_score=score,
                )
        return None
