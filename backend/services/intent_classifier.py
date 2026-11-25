"""
Intent Classifier & Entity Extraction Service (Module 3).
Supports Marathi (mr), Hindi (hi), English (en), and code-mixed Hinglish/Marathi-English queries.

Supported intents:
- crop_advice
- pest_info
- disease_info
- pest_disease (alias preserved for backward compatibility when mixed)
- government_schemes
- mandi_prices
- weather
- general_agriculture
- out_of_scope

Extracted entities:
- crop, pest_or_disease, location, state, season, commodity, mandi
"""

from typing import Dict, Any, List


class IntentClassifier:
    """Multilingual agricultural intent classifier and entity extractor."""

    CROPS = {
        "wheat": ["wheat", "गेहूं", "गहू", "गेहू", "गव्हा", "गव्हाच्या", "gehu", "gahu"],
        "rice": ["rice", "paddy", "चावल", "भात", "धान", "तांदूळ", "भाता", "chawal", "bhat"],
        "cotton": ["cotton", "कपास", "कापूस", "कापसा", "कापसाच्या", "kapus", "kapas"],
        "soybean": ["soybean", "soya", "सोयाबीन", "सोया"],
        "onion": ["onion", "प्याज", "कांदा", "कांद्या", "कांद्याचे", "kanda", "pyaz"],
        "potato": ["potato", "आलू", "बटाटा", "बटाट्या"],
        "tomato": ["tomato", "टमाटर", "टोमॅटो"],
        "sugarcane": ["sugarcane", "गन्ना", "ऊस", "उसाच्या", "ganna", "oos"],
        "maize": ["maize", "corn", "मक्का", "मका"],
        "gram": ["gram", "chickpea", "चना", "हरभरा"],
        "tur": ["tur", "arhar", "तूर", "अरहर"],
        "groundnut": ["groundnut", "peanut", "मूंगफली", "भुईमूग", "शेंगदाणे"],
        "garlic": ["garlic", "लहसुन", "लसूण"],
        "ginger": ["ginger", "अदरक", "आले"],
        "chilli": ["chilli", "chili", "मिर्च", "मिरची"],
    }

    PEST_OR_DISEASE_ENTITIES = {
        "aphids": ["aphid", "aphids", "मावा", "माहू", "चेपा", "mava"],
        "bollworm": ["bollworm", "बोंड अळी", "अळी", "सुंडी", "इल्ली", "ghati aali", "spodoptera"],
        "whitefly": ["whitefly", "पांढरी माशी", "सफेद मक्खी"],
        "yellow_spots_chlorosis": ["पिवळे डाग", "पाने पिवळी", "पीले पत्ते", "पीलापन", "yellow spot", "yellow leaf", "yellow leaves", "yellowing", "chlorosis"],
        "rust": ["rust", "तांबेरा", "गेरुआ", "गेरूआ", "रतुआ"],
        "blight": ["blight", "करपा", "झुलसा", "डाग", "धब्बे", "spots"],
        "wilt": ["wilt", "मर रोग", "उकठा", "मुरझान"],
    }

    MANDI_KEYWORDS = [
        "भाव", "दाम", "कीमत", "रेट", "मंडी", "बाजार", "एपीएमसी", "मंडी भाव", "बाजार भाव", "क्विंटल",
        "दर", "बाजारभाव", "मार्केट", "आवक", "किंमत", "बाजार",
        "mandi", "price", "prices", "rate", "rates", "market", "apmc", "quintal", "bhav", "bajarbhav",
    ]

    WEATHER_KEYWORDS = [
        "मौसम", "बारिश", "बरसात", "तापमान", "हवा", "आंधी", "तूफान", "बादल", "ठंड", "पाला", "ओले", "ओलावृष्टि",
        "हवामान", "पाऊस", "तापमान", "गारपीट", "ढग", "थंडी", "वादळ", "आर्द्रता", "अंदाज", "पाऊस पडेल",
        "weather", "rain", "rainfall", "temperature", "climate", "forecast", "humidity", "storm", "hail", "barish", "mausam",
    ]

    PEST_KEYWORDS = [
        "कीट", "कीड़े", "इल्ली", "सुंडी", "माहू", "मावा", "अळी", "कीड", "तुडतुडे", "पांढरी माशी",
        "सफेद मक्खी", "कीटनाशक", "कीटकनाशक", "insect", "pest", "aphid", "bollworm", "caterpillar", "keeda", "keed",
    ]

    DISEASE_KEYWORDS = [
        "रोग", "बीमारी", "फफूंद", "फंगस", "धब्बा", "धब्बे", "सड़न", "पीले पत्ते", "पीलापन",
        "बुरशी", "पाने पिवळी", "पिवळे डाग", "मर रोग", "करपा", "तांबेरा", "लक्षण", "कारण",
        "disease", "fungus", "blight", "rust", "rot", "yellow", "spots", "infection", "wilt", "chlorosis",
    ]

    PEST_DISEASE_SHARED = [
        "छिड़काव", "दवाई", "दवा", "फवारणी", "औषध", "spray", "pesticide", "fungicide", "control", "उपाय",
    ]

    SCHEME_KEYWORDS = [
        "योजना", "सब्सिडी", "अनुदान", "पीएम किसान", "किसान क्रेडिट कार्ड", "केसीसी", "बीमा", "फसल बीमा",
        "सरकारी", "मुआवजा", "कर्ज माफी", "पात्रता", "सन्मान निधी", "सम्मान निधि",
        "पीक विमा", "कर्जमाफी", "शासकीय", "मदत", "नुकसान भरपाई",
        "scheme", "subsidy", "pm kisan", "pm-kisan", "pmfby", "insurance", "government", "grant",
        "kcc", "compensation", "loan waiver", "eligibility", "yojana",
    ]

    CROP_ADVICE_KEYWORDS = [
        "खेती", "बुवाई", "बुआई", "खाद", "उर्वरक", "सिंचाई", "पैदावार", "कटाई", "किस्म", "बीज", "तैयारी", "दूरी", "यूरिया", "डीएपी",
        "लागवड", "पेरणी", "खत", "खते", "पाणी", "उत्पादन", "कापणी", "वाण", "बियाणे", "जमीन", "मशागत", "मात्रा", "खत व्यवस्थापन",
        "cultivation", "sowing", "fertilizer", "irrigation", "yield", "variety", "seed", "harvest", "spacing", "npk", "urea", "manure", "khad",
    ]

    OUT_OF_SCOPE_KEYWORDS = [
        "cricket", "ipl", "match", "movie", "film", "song", "cinema",
        "bitcoin", "crypto", "stock market", "share market", "sensex", "nifty",
        "politics", "election", "vote", "क्रिकेट", "चित्रपट", "गाणे", "शेअर बाजार",
        "निवडणूक", "राजकारण", "सामना", "फिल्म", "गाना", "शेयर बाजार", "चुनाव", "राजनीति", "मैच", "आईपीएल",
    ]

    LOCATIONS = {
        "Maharashtra": [
            "maharashtra", "महाराष्ट्र", "pune", "पुणे", "nashik", "नाशिक", "nagpur", "नागपुर", "नागपूर",
            "aurangabad", "chhatrapati sambhajinagar", "संभाजीनगर", "औरंगाबाद",
            "solapur", "सोलापूर", "सोलापुर", "kolhapur", "कोल्हापूर", "कोल्हापुर", "amravati", "अमरावती",
            "ahmednagar", "अहमदनगर", "jalgaon", "जळगाव", "जलगांव", "satara", "सातारा",
            "sangli", "सांगली", "latur", "लातूर", "nanded", "नांदेड", "akola", "अकोला", "yavatmal", "यवतमाल", "wardha", "वर्धा",
        ],
        "Madhya Pradesh": ["madhya pradesh", "मध्य प्रदेश", "indore", "इन्दौर", "इंदौर", "bhopal", "भोपाल", "ujjain", "उज्जैन"],
        "Uttar Pradesh": ["uttar pradesh", "उत्तर प्रदेश", "lucknow", "लखनऊ", "kanpur", "कानपुर"],
        "Punjab": ["punjab", "पंजाब", "ludhiana", "लुधियाना", "amritsar", "अमृतसर"],
        "Haryana": ["haryana", "हरियाणा", "karnal", "करनाल"],
    }

    LOCATION_CANONICAL = {
        "pune": "Pune", "पुणे": "Pune",
        "nashik": "Nashik", "नाशिक": "Nashik",
        "nagpur": "Nagpur", "नागपुर": "Nagpur", "नागपूर": "Nagpur",
        "aurangabad": "Aurangabad", "औरंगाबाद": "Aurangabad",
        "chhatrapati sambhajinagar": "Aurangabad", "संभाजीनगर": "Aurangabad",
        "solapur": "Solapur", "सोलापूर": "Solapur", "सोलापुर": "Solapur",
        "kolhapur": "Kolhapur", "कोल्हापूर": "Kolhapur", "कोल्हापुर": "Kolhapur",
        "amravati": "Amravati", "अमरावती": "Amravati",
        "ahmednagar": "Ahmednagar", "अहमदनगर": "Ahmednagar",
        "jalgaon": "Jalgaon", "जळगाव": "Jalgaon", "जलगांव": "Jalgaon",
        "satara": "Satara", "सातारा": "Satara",
        "sangli": "Sangli", "सांगली": "Sangli",
        "latur": "Latur", "लातूर": "Latur",
        "nanded": "Nanded", "नांदेड": "Nanded",
        "akola": "Akola", "अकोला": "Akola",
        "yavatmal": "Yavatmal", "यवतमाल": "Yavatmal",
        "wardha": "Wardha", "वर्धा": "Wardha",
        "indore": "Indore", "इन्दौर": "Indore", "इंदौर": "Indore",
        "bhopal": "Bhopal", "भोपाल": "Bhopal",
        "ujjain": "Ujjain", "उज्जैन": "Ujjain",
        "lucknow": "Lucknow", "लखनऊ": "Lucknow",
        "kanpur": "Kanpur", "कानपुर": "Kanpur",
        "ludhiana": "Ludhiana", "लुधियाना": "Ludhiana",
        "amritsar": "Amritsar", "अमृतसर": "Amritsar",
        "karnal": "Karnal", "करनाल": "Karnal",
    }

    def extract_entities(self, text: str) -> Dict[str, Any]:
        lower_text = text.lower()
        entities: Dict[str, Any] = {
            "crop": None,
            "commodity": None,
            "pest_or_disease": None,
            "location": None,
            "mandi": None,
            "state": "Maharashtra",
            "state_explicit": False,
            "season": None,
        }

        for standard_crop, aliases in self.CROPS.items():
            if any(alias.lower() in lower_text for alias in aliases):
                entities["crop"] = standard_crop.capitalize()
                entities["commodity"] = standard_crop.capitalize()
                break

        for issue_name, aliases in self.PEST_OR_DISEASE_ENTITIES.items():
            if any(alias.lower() in lower_text for alias in aliases):
                entities["pest_or_disease"] = issue_name
                break

        for state, place_names in self.LOCATIONS.items():
            for place in place_names:
                if place.lower() in lower_text:
                    canonical = self.LOCATION_CANONICAL.get(place.lower(), place.title())
                    if canonical.lower() != state.lower():
                        entities["location"] = canonical
                        entities["mandi"] = canonical
                    entities["state"] = state
                    entities["state_explicit"] = True
                    break
            if entities["location"] or entities["state_explicit"]:
                break

        for kw in ["खरीफ", "खरीप", "kharif", "monsoon"]:
            if kw in lower_text:
                entities["season"] = "Kharif"
                break
        if not entities["season"]:
            for kw in ["रबी", "रब्बी", "rabi", "winter"]:
                if kw in lower_text:
                    entities["season"] = "Rabi"
                    break
        if not entities["season"]:
            for kw in ["जायद", "उन्हाळी", "summer", "zaid"]:
                if kw in lower_text:
                    entities["season"] = "Summer"
                    break

        return entities

    def classify(self, text: str, lang: str = "hi") -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "intent": "general_agriculture",
                "intent_detail": "general_agriculture",
                "entities": self.extract_entities(""),
                "missing_entities": ["query"],
                "confidence": 0.0,
            }

        lower_text = text.lower()
        entities = self.extract_entities(text)

        # Out-of-scope check first
        if any(kw in lower_text for kw in self.OUT_OF_SCOPE_KEYWORDS):
            return {
                "intent": "out_of_scope",
                "intent_detail": "out_of_scope",
                "entities": entities,
                "missing_entities": [],
                "confidence": 0.95,
            }

        scores = {
            "mandi_prices": 0.0,
            "weather": 0.0,
            "pest_info": 0.0,
            "disease_info": 0.0,
            "government_schemes": 0.0,
            "crop_advice": 0.0,
            "general_agriculture": 0.0,
        }

        for kw in self.MANDI_KEYWORDS:
            if kw in lower_text:
                scores["mandi_prices"] += 2.0

        for kw in self.WEATHER_KEYWORDS:
            if kw in lower_text:
                scores["weather"] += 2.0

        for kw in self.PEST_KEYWORDS:
            if kw in lower_text:
                scores["pest_info"] += 2.2

        for kw in self.DISEASE_KEYWORDS:
            if kw in lower_text:
                scores["disease_info"] += 2.2

        for kw in self.PEST_DISEASE_SHARED:
            if kw in lower_text:
                scores["pest_info"] += 1.0
                scores["disease_info"] += 1.0

        for kw in self.SCHEME_KEYWORDS:
            if kw in lower_text:
                scores["government_schemes"] += 2.2

        for kw in self.CROP_ADVICE_KEYWORDS:
            if kw in lower_text:
                scores["crop_advice"] += 1.5

        if entities["crop"] and max(scores.values()) == 0:
            scores["crop_advice"] += 1.0

        detailed_intent = max(scores, key=scores.get)
        max_score = scores[detailed_intent]

        if max_score == 0:
            detailed_intent = "general_agriculture"

        # Normalize pest_info / disease_info to pest_disease for unified RAG routing while preserving intent_detail
        canonical_intent = (
            "pest_disease" if detailed_intent in ("pest_info", "disease_info") else detailed_intent
        )

        # Missing essential entities check for clarification logic
        missing: List[str] = []
        if canonical_intent == "mandi_prices" and not entities["commodity"]:
            missing.append("commodity")
        if canonical_intent == "weather" and not entities["location"]:
            missing.append("location")

        if max_score >= 4:
            confidence = 0.95
        elif max_score >= 2:
            confidence = 0.85
        elif max_score > 0:
            confidence = 0.70
        else:
            confidence = 0.50

        return {
            "intent": canonical_intent,
            "intent_detail": detailed_intent,
            "entities": entities,
            "missing_entities": missing,
            "confidence": confidence,
        }
