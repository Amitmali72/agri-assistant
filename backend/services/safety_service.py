"""
Safety, Privacy & Confidence Gate Service (Modules 10 & 12).

Implements the 4-way decision engine:
1. ANSWER  - Sufficient approved evidence, passes safety checks
2. CLARIFY - Missing essential parameters (crop, commodity, location) or vague query
3. REFUSE  - Off-topic, lethal/banned chemical, or insufficient evidence
4. REFER   - Requires certified agricultural expert / KVK / Kisan Call Centre (1800-180-1551)
"""

import re
from typing import Dict, Any, List, Optional


class SafetyService:
    """Dedicated decision gate and agricultural safety guardrail layer."""

    OFF_TOPIC_KEYWORDS = [
        "cricket", "ipl", "match", "movie", "film", "song", "cinema",
        "bitcoin", "crypto", "stock market", "share market", "sensex", "nifty",
        "politics", "election", "vote", "narendra modi", "rahul gandhi",
        "क्रिकेट", "चित्रपट", "गाणे", "शेअर बाजार", "निवडणूक", "राजकारण", "सामना",
        "फिल्म", "गाना", "शेयर बाजार", "चुनाव", "राजनीति", "मैच", "आईपीएल",
    ]

    DANGEROUS_CHEMICAL_KEYWORDS = [
        "monocrotophos", "phorate", "endosulfan", "paraquat", "celphos", "aluminium phosphide",
        "ddt", "carbofuran", "methyl parathion", "poison", "suicide", "विष", "आत्महत्या", "जहर", "घातक",
    ]

    DOSAGE_INQUIRY_KEYWORDS = [
        "dosage", "dose", "ml per liter", "how much spray", "concentration",
        "प्रमाण", "डोस", "किती फवारावे", "मिली प्रति लिटर", "मात्रा",
        "कितना छिड़काव", "प्रति लीटर", "कितनी दवा", "किती औषध",
    ]

    DISCLAIMERS = {
        "mr": "टीप: ही माहिती अधिकृत कृषी मार्गदर्शनावर आधारित आहे. रासायनिक फवारणीपूर्वी लेबल व कृषी तज्ज्ञांचा सल्ला अवश्य घ्या.",
        "hi": "सूचना: यह जानकारी आधिकारिक कृषि दिशानिर्देशों पर आधारित है। किसी भी रसायन के उपयोग से पहले लेबल और कृषि विशेषज्ञ की सलाह अवश्य लें।",
        "en": "Disclaimer: Information is grounded in agricultural reference documents. Verify chemical labels and consult a local KVK officer before field application.",
    }

    FALLBACK_MESSAGES = {
        "mr": {
            "insufficient_context": (
                "माफ करा, या विषयावर मान्यताप्राप्त कृषी दस्तऐवजांमध्ये पुरेशी खात्रीशीर माहिती उपलब्ध नाही. "
                "अचूक मार्गदर्शनासाठी कृपया आपल्या जवळच्या कृषी विज्ञान केंद्रास (KVK) भेट द्या "
                "किंवा राष्ट्रीय किसान कॉल सेंटरच्या टोल-फ्री क्रमांक 1800-180-1551 वर संपर्क साधा."
            ),
            "unsafe_chemical": (
                "सावधान: कीटकनाशक किंवा रासायनिक औषधांची अचूक मात्रा पिकांच्या व मानवी आरोग्याच्या सुरक्षेसाठी अत्यंत महत्त्वाची असते. "
                "मान्यताप्राप्त अधिकृत स्त्रोतामध्ये या औषधाच्या अचूक मात्रेचा उल्लेख नसल्यामुळे मी अंदाज लावून मात्रा सांगू शकत नाही. "
                "कृपया जवळच्या कृषी विज्ञान केंद्रातील (KVK) तज्ज्ञांशी किंवा किसान कॉल सेंटर (1800-180-1551) शी संपर्क साधा."
            ),
            "off_topic": (
                "मी कृषीमित्र (KrishiMitra) आहे. मी फक्त शेती, पिके, कीड-रोग, बाजारभाव, "
                "हवामान आणि शासकीय कृषी योजनांविषयी मदत करू शकतो. कृपया शेतीशी संबंधित प्रश्न विचारा."
            ),
            "clarification_needed": (
                "तुमचा प्रश्न अपूर्ण किंवा अस्पष्ट वाटत आहे. कृपया पिकाचे नाव, लक्षणे किंवा आपला जिल्हा/तालुका "
                "स्पष्ट सांगा जेणेकरून मी अचूक माहिती देऊ शकेन."
            ),
            "clarify_location": (
                "हवामानाची अचूक माहिती देण्यासाठी कृपया आपला जिल्हा किंवा गावाचे नाव सांगा (उदा. पुणे, नाशिक, नागपूर)."
            ),
            "clarify_commodity": (
                "बाजारभाव तपासण्यासाठी कृपया कोणत्या पिकाचा (उदा. कापूस, कांदा, गहू, सोयाबीन) आणि कोणत्या बाजारपेठेचा भाव हवा आहे ते सांगा."
            ),
            "low_stt_confidence": (
                "आवाज स्पष्ट ओळखता आला नाही. कृपया शांत वातावरणात पुन्हा स्पष्टपणे बोला किंवा आपला प्रश्न टाइप करा."
            ),
            "banned_chemical": (
                "हा रासायनिक घटक अत्यंत विषारी किंवा प्रतिबंधित असू शकतो. मानवी आरोग्य व शेताच्या सुरक्षेसाठी "
                "याचा वापर करू नका आणि कृषी विज्ञान केंद्रातील (KVK) तज्ज्ञांचा सल्ला घ्या (किसान कॉल सेंटर: 1800-180-1551)."
            ),
        },
        "hi": {
            "insufficient_context": (
                "क्षमा करें, इस विषय पर स्वीकृत आधिकारिक कृषि दस्तावेजों में पर्याप्त विश्वसनीय जानकारी उपलब्ध नहीं है। "
                "सटीक मार्गदर्शन के लिए कृपया अपने नजदीकी कृषि विज्ञान केंद्र (KVK) से संपर्क करें "
                "या राष्ट्रीय किसान कॉल सेंटर के टोल-फ्री नंबर 1800-180-1551 पर कॉल करें।"
            ),
            "unsafe_chemical": (
                "सावधानी: कीटनाशक अथवा रासायनिक दवाओं की सही मात्रा फसल और मानव स्वास्थ्य के लिए अत्यंत महत्वपूर्ण है। "
                "स्वीकृत दस्तावेजी प्रमाण के बिना दवा की खुराक का अनुमान लगाना सुरक्षित नहीं है। "
                "कृपया स्थानीय कृषि विज्ञान केंद्र (KVK) के विशेषज्ञ या किसान कॉल सेंटर (1800-180-1551) से सलाह लें।"
            ),
            "off_topic": (
                "मैं एक समर्पित कृषि सहायक (KrishiMitra) हूँ। मैं केवल खेती, फसल सुरक्षा, खाद-पानी, "
                "मंडी भाव, मौसम और सरकारी कृषि योजनाओं से जुड़े सवालों के उत्तर दे सकता हूँ। कृपया कृषि से संबंधित प्रश्न पूछें।"
            ),
            "clarification_needed": (
                "आपका प्रश्न अधूरा या अस्पष्ट लग रहा है। कृपया फसल का नाम, समस्या के लक्षण या अपना जिला/स्थान "
                "स्पष्ट रूप से लिखकर या बोलकर पूछें ताकि मैं सही सहायता कर सकूँ।"
            ),
            "clarify_location": (
                "सटीक मौसम जानकारी के लिए कृपया अपने शहर या जिले का नाम बताएं (जैसे: पुणे, नासिक, नागपुर, इंदौर)।"
            ),
            "clarify_commodity": (
                "मंडी भाव जानने के लिए कृपया फसल का नाम बताएं (जैसे: कपास, गेहूं, प्याज, सोयाबीन)।"
            ),
            "low_stt_confidence": (
                "आपकी आवाज़ स्पष्ट रूप से समझ नहीं आई। कृपया शांत स्थान से दोबारा बोलें या अपना प्रश्न लिखकर भेजें।"
            ),
            "banned_chemical": (
                "यह रसायन अत्यधिक विषैला या प्रतिबंधित हो सकता है। स्वास्थ्य और फसल सुरक्षा के लिए इसका उपयोग न करें "
                "और कृषि विज्ञान केंद्र (KVK) या किसान कॉल सेंटर (1800-180-1551) से प्रमाणित सलाह लें।"
            ),
        },
        "en": {
            "insufficient_context": (
                "Sorry, sufficient verified agricultural documentation is not available for this query. "
                "For reliable guidance, please consult your nearest Krishi Vigyan Kendra (KVK) "
                "or call the National Kisan Call Centre toll-free at 1800-180-1551."
            ),
            "unsafe_chemical": (
                "Warning: Accurate pesticide dosage is critical for crop and human safety. "
                "Without an approved official source containing verified dosage data, I cannot guess a chemical dosage. "
                "Please consult a KVK agricultural scientist or call 1800-180-1551."
            ),
            "off_topic": (
                "I am KrishiMitra, an agricultural assistant. I can only assist with farming, crops, pests, "
                "mandi prices, weather, and government schemes. Please ask an agriculture-related question."
            ),
            "clarification_needed": (
                "Your question appears incomplete or ambiguous. Please provide the crop name, symptoms, or your district/location."
            ),
            "clarify_location": "Please specify your city or district name to fetch local weather.",
            "clarify_commodity": "Please specify the crop/commodity name to look up live mandi prices.",
            "low_stt_confidence": "Voice input could not be recognized clearly. Please speak again or type your question.",
            "banned_chemical": "This chemical is highly toxic or restricted. Avoid use and contact KVK / Kisan Call Centre (1800-180-1551).",
        },
    }

    def __init__(self, min_confidence_score: float = 0.28, min_stt_confidence: float = 0.35):
        self.min_confidence_score = min_confidence_score
        self.min_stt_confidence = min_stt_confidence

    def get_fallback_message(self, action: str, lang: str = "hi") -> str:
        lang_key = lang if lang in self.FALLBACK_MESSAGES else "hi"
        return self.FALLBACK_MESSAGES[lang_key].get(
            action,
            self.FALLBACK_MESSAGES[lang_key]["insufficient_context"],
        )

    def get_disclaimer(self, lang: str = "hi") -> str:
        return self.DISCLAIMERS.get(lang, self.DISCLAIMERS["hi"])

    def check_stt_confidence(self, stt_confidence: Optional[float], lang: str = "hi") -> Dict[str, Any]:
        if stt_confidence is not None and stt_confidence < self.min_stt_confidence:
            return {
                "safe": False,
                "decision": "CLARIFY",
                "action": "low_stt_confidence",
                "reason": f"STT confidence {stt_confidence:.2f} below threshold {self.min_stt_confidence}",
                "message": self.get_fallback_message("low_stt_confidence", lang),
            }
        return {"safe": True, "decision": "ANSWER", "action": "proceed", "reason": "STT OK", "message": ""}

    def check_query_safety(
        self,
        query: str,
        lang: str = "hi",
        intent: Optional[str] = None,
        missing_entities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Pre-retrieval safety & ambiguity check.
        Returns decision in {ANSWER (proceed), CLARIFY, REFUSE, REFER}.
        """
        clean_q = (query or "").strip().lower()
        words = [w for w in clean_q.split() if w.strip()]

        if len(words) < 2 and len(clean_q) < 10:
            return {
                "safe": False,
                "decision": "CLARIFY",
                "action": "clarification_needed",
                "reason": "Query is too brief or ambiguous",
                "message": self.get_fallback_message("clarification_needed", lang),
            }

        for banned in self.DANGEROUS_CHEMICAL_KEYWORDS:
            if banned in clean_q:
                return {
                    "safe": False,
                    "decision": "REFER",
                    "action": "banned_chemical",
                    "reason": f"Detected reference to dangerous or restricted chemical: {banned}",
                    "message": self.get_fallback_message("banned_chemical", lang),
                }

        if intent == "out_of_scope" or any(off in clean_q for off in self.OFF_TOPIC_KEYWORDS):
            return {
                "safe": False,
                "decision": "REFUSE",
                "action": "off_topic",
                "reason": "Query is outside agricultural domain",
                "message": self.get_fallback_message("off_topic", lang),
            }

        if missing_entities:
            if intent == "weather" and "location" in missing_entities:
                return {
                    "safe": False,
                    "decision": "CLARIFY",
                    "action": "clarify_location",
                    "reason": "Missing location entity for weather forecast",
                    "message": self.get_fallback_message("clarify_location", lang),
                }
            if intent == "mandi_prices" and "commodity" in missing_entities:
                return {
                    "safe": False,
                    "decision": "CLARIFY",
                    "action": "clarify_commodity",
                    "reason": "Missing commodity entity for mandi lookup",
                    "message": self.get_fallback_message("clarify_commodity", lang),
                }

        return {"safe": True, "decision": "ANSWER", "action": "proceed", "reason": "Query passed safety check", "message": ""}

    def check_retrieval_confidence(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        intent: str,
        lang: str = "hi",
    ) -> Dict[str, Any]:
        """
        Post-retrieval confidence & grounding gate.
        """
        if intent in ["weather", "mandi_prices"]:
            return {"safe": True, "decision": "ANSWER", "action": "proceed", "reason": "Live data tool", "message": ""}

        if not retrieved_chunks:
            return {
                "safe": False,
                "decision": "REFUSE",
                "action": "insufficient_context",
                "reason": "No approved relevant documents found in knowledge base",
                "message": self.get_fallback_message("insufficient_context", lang),
            }

        approved_chunks = [
            c for c in retrieved_chunks
            if c.get("metadata", {}).get("approval_status", "approved") == "approved"
        ]
        if not approved_chunks:
            return {
                "safe": False,
                "decision": "REFUSE",
                "action": "insufficient_context",
                "reason": "Retrieved chunks are not from approved documents",
                "message": self.get_fallback_message("insufficient_context", lang),
            }

        scores = [chunk.get("score", 0.0) for chunk in approved_chunks]
        best_score = max(scores) if scores else 0.0

        if best_score < self.min_confidence_score:
            return {
                "safe": False,
                "decision": "REFER",
                "action": "insufficient_context",
                "reason": f"Best retrieval score ({best_score:.3f}) below threshold ({self.min_confidence_score})",
                "message": self.get_fallback_message("insufficient_context", lang),
            }

        lower_q = query.lower()
        is_dosage_query = any(kw in lower_q for kw in self.DOSAGE_INQUIRY_KEYWORDS)
        if is_dosage_query:
            dosage_patterns = ("ml per", "gm per", "g/l", "ml/l", "kg per", "kg/ha", "लिटर", "लीटर", "ग्राम", "मिली")
            has_dosage = any(
                any(pat in c.get("text", "").lower() for pat in dosage_patterns)
                for c in approved_chunks
            )
            if not has_dosage:
                return {
                    "safe": False,
                    "decision": "REFER",
                    "action": "unsafe_chemical",
                    "reason": "Chemical dosage asked without verified dosage data in approved sources",
                    "message": self.get_fallback_message("unsafe_chemical", lang),
                }

        return {
            "safe": True,
            "decision": "ANSWER",
            "action": "proceed",
            "reason": f"Confidence gate passed (score: {best_score:.3f})",
            "message": "",
        }
