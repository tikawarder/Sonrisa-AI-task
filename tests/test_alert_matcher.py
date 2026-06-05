import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.matching.matcher import AlertConfig, AlertMatch, AlertMatcher, KeywordMatcher, LLMRelevanceScorer
from src.sources.base import Event


def make_event(title: str, description: str = "") -> Event:
    return Event(
        title=title,
        description=description,
        url="https://example.com/news/1",
        published_at=datetime(2026, 6, 5, 10, 0, tzinfo=timezone.utc),
        source="Test Feed",
    )


def make_alert(**kwargs) -> AlertConfig:
    defaults = dict(id=uuid.uuid4(), keywords=[], use_llm=False, threshold=0.7)
    return AlertConfig(**{**defaults, **kwargs})


# --- KeywordMatcher ---

def test_keyword_match_in_title():
    matcher = KeywordMatcher()
    event = make_event("Earthquake hits Turkey")
    assert matcher.matches(event, ["earthquake"]) is True


def test_keyword_match_case_insensitive():
    matcher = KeywordMatcher()
    event = make_event("EARTHQUAKE HITS TURKEY")
    assert matcher.matches(event, ["earthquake"]) is True


def test_keyword_match_in_description():
    matcher = KeywordMatcher()
    event = make_event("Breaking news", "A 6.5 magnitude earthquake struck the region")
    assert matcher.matches(event, ["earthquake"]) is True


def test_keyword_no_match():
    matcher = KeywordMatcher()
    event = make_event("Stock market rises")
    assert matcher.matches(event, ["earthquake", "flood"]) is False


def test_keyword_empty_keywords_returns_false():
    matcher = KeywordMatcher()
    assert matcher.matches(make_event("Anything"), []) is False


# --- AlertMatcher: keyword path ---

def test_matcher_returns_match_on_keyword():
    matcher = AlertMatcher()
    events = [make_event("Flood warning issued in Germany")]
    alerts = [make_alert(keywords=["flood"])]

    results = matcher.match(events, alerts)
    assert len(results) == 1
    assert results[0].matched_by == "keyword"
    assert results[0].relevance_score is None


def test_matcher_skips_inactive_alerts():
    matcher = AlertMatcher()
    events = [make_event("Earthquake in Japan")]
    alerts = [make_alert(keywords=["earthquake"], is_active=False)]

    assert matcher.match(events, alerts) == []


def test_matcher_no_match_returns_empty():
    matcher = AlertMatcher()
    events = [make_event("Local sports results")]
    alerts = [make_alert(keywords=["earthquake", "flood"])]

    assert matcher.match(events, alerts) == []


def test_matcher_multiple_alerts_multiple_events():
    matcher = AlertMatcher()
    events = [make_event("Flood in Italy"), make_event("Fire in California")]
    alerts = [make_alert(keywords=["flood"]), make_alert(keywords=["fire"])]

    results = matcher.match(events, alerts)
    assert len(results) == 2


# --- AlertMatcher: LLM path ---

def test_matcher_uses_llm_when_keyword_misses():
    mock_scorer = MagicMock(spec=LLMRelevanceScorer)
    mock_scorer.score.return_value = 0.85

    matcher = AlertMatcher(llm_scorer=mock_scorer)
    events = [make_event("Severe weather disrupts travel")]
    alerts = [make_alert(keywords=[], use_llm=True, topic="natural disasters", threshold=0.7)]

    results = matcher.match(events, alerts)
    assert len(results) == 1
    assert results[0].matched_by == "llm"
    assert results[0].relevance_score == 0.85


def test_matcher_llm_below_threshold_no_match():
    mock_scorer = MagicMock(spec=LLMRelevanceScorer)
    mock_scorer.score.return_value = 0.4

    matcher = AlertMatcher(llm_scorer=mock_scorer)
    events = [make_event("Mild weather expected this weekend")]
    alerts = [make_alert(keywords=[], use_llm=True, topic="natural disasters", threshold=0.7)]

    assert matcher.match(events, alerts) == []


def test_matcher_llm_not_called_if_keyword_matches():
    mock_scorer = MagicMock(spec=LLMRelevanceScorer)

    matcher = AlertMatcher(llm_scorer=mock_scorer)
    events = [make_event("Earthquake hits Turkey")]
    alerts = [make_alert(keywords=["earthquake"], use_llm=True, topic="disasters")]

    results = matcher.match(events, alerts)
    assert len(results) == 1
    assert results[0].matched_by == "keyword"
    mock_scorer.score.assert_not_called()


# --- LLMRelevanceScorer ---

@patch("src.matching.matcher.genai")
def test_llm_scorer_clamps_to_valid_range(mock_genai):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = "1.5"
    mock_genai.Client.return_value = mock_client

    scorer = LLMRelevanceScorer(api_key="fake-key")
    score = scorer.score(make_event("Test"), "disasters")
    assert score == 1.0


@patch("src.matching.matcher.genai")
def test_llm_scorer_returns_zero_on_invalid_response(mock_genai):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = "not a number"
    mock_genai.Client.return_value = mock_client

    scorer = LLMRelevanceScorer(api_key="fake-key")
    score = scorer.score(make_event("Test"), "disasters")
    assert score == 0.0
