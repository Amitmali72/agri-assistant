"""
Tests for SafetyService 4-way Confidence & Decision Gate (Modules 10 & 12).
"""

import pytest
from backend.services.safety_service import SafetyService


@pytest.fixture
def safety():
    return SafetyService(min_confidence_score=0.28, min_stt_confidence=0.35)


def test_safe_crop_query(safety):
    res = safety.check_query_safety("गव्हाच्या पेरणीची माहिती द्या", lang="mr")
    assert res["safe"] is True
    assert res["decision"] == "ANSWER"


def test_stt_confidence_gate(safety):
    low = safety.check_stt_confidence(0.20, lang="mr")
    assert low["safe"] is False
    assert low["decision"] == "CLARIFY"

    ok = safety.check_stt_confidence(0.82, lang="hi")
    assert ok["safe"] is True


def test_off_topic_refuse(safety):
    res = safety.check_query_safety("कल क्रिकेट मैच में कौन जीता?", lang="hi")
    assert res["safe"] is False
    assert res["decision"] == "REFUSE"


def test_dangerous_chemical_refer(safety):
    res = safety.check_query_safety("Monocrotophos poison spray", lang="en")
    assert res["safe"] is False
    assert res["decision"] == "REFER"


def test_vague_query_clarify(safety):
    res = safety.check_query_safety("कीड", lang="mr")
    assert res["safe"] is False
    assert res["decision"] == "CLARIFY"


def test_missing_entity_clarify(safety):
    res = safety.check_query_safety("आज हवामान कसे आहे", lang="mr", intent="weather", missing_entities=["location"])
    assert res["safe"] is False
    assert res["decision"] == "CLARIFY"


def test_unapproved_or_low_score_retrieval_gate(safety):
    empty = safety.check_retrieval_confidence("test", [], intent="crop_advice", lang="mr")
    assert empty["safe"] is False
    assert empty["decision"] == "REFUSE"

    unapproved = safety.check_retrieval_confidence(
        "test",
        [{"text": "sample", "score": 0.9, "metadata": {"approval_status": "pending"}}],
        intent="crop_advice",
        lang="mr",
    )
    assert unapproved["safe"] is False
    assert unapproved["decision"] == "REFUSE"

    low = safety.check_retrieval_confidence(
        "test",
        [{"text": "irrelevant", "score": 0.12, "metadata": {"approval_status": "approved"}}],
        intent="crop_advice",
        lang="hi",
    )
    assert low["safe"] is False
    assert low["decision"] == "REFER"
