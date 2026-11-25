"""
Tests for Intent Classification and Agricultural Entity Extraction.
"""

import pytest
from backend.services.intent_classifier import IntentClassifier


@pytest.fixture
def classifier():
    return IntentClassifier()


def test_classify_mandi_prices_hindi(classifier):
    res = classifier.classify("पुणे मंडी में प्याज का भाव क्या है?", lang="hi")
    assert res["intent"] == "mandi_prices"
    assert res["entities"]["commodity"] == "Onion"
    assert res["entities"]["location"] == "Pune"


def test_classify_mandi_prices_marathi(classifier):
    res = classifier.classify("नाशिक मार्केटमध्ये कांद्याचे बाजारभाव काय आहेत?", lang="mr")
    assert res["intent"] == "mandi_prices"
    assert res["entities"]["commodity"] == "Onion"
    assert res["entities"]["location"] == "Nashik"


def test_classify_weather_hindi(classifier):
    res = classifier.classify("कल नागपुर में बारिश होगी क्या?", lang="hi")
    assert res["intent"] == "weather"
    assert res["entities"]["location"] == "Nagpur"


def test_classify_weather_marathi(classifier):
    res = classifier.classify("औरंगाबाद जिल्ह्याचे हवामान कसे राहील?", lang="mr")
    assert res["intent"] == "weather"
    assert res["entities"]["location"] == "Aurangabad"


def test_classify_pest_disease_marathi(classifier):
    res = classifier.classify("सोयाबीन पिकावर अळीचा प्रादुर्भाव झाला आहे, औषध सांगा", lang="mr")
    assert res["intent"] == "pest_disease"
    assert res["entities"]["crop"] == "Soybean"


def test_classify_crop_advice_hindi(classifier):
    res = classifier.classify("गेहूं की बुवाई के लिए कौन सी खाद सबसे अच्छी है?", lang="hi")
    assert res["intent"] == "crop_advice"
    assert res["entities"]["crop"] == "Wheat"


def test_classify_government_schemes_hindi(classifier):
    res = classifier.classify("पीएम किसान सम्मान निधि योजना के नियम क्या हैं?", lang="hi")
    assert res["intent"] == "government_schemes"
