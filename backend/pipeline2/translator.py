"""Translator — Hindi/Marathi ↔ English using a built-in dictionary."""

import logging

logger = logging.getLogger(__name__)


class Translator:
    def __init__(self):
        self.dictionary = self._build_dictionary()
        self.is_loaded = True

    def _build_dictionary(self) -> dict:
        return {
            "hello": {"hi": "नमस्ते", "mr": "नमस्कार"},
            "thank_you": {"hi": "धन्यवाद", "mr": "धन्यवाद"},
            "please": {"hi": "कृपया", "mr": "कृपया"},
            "sorry": {"hi": "माफ़ करें", "mr": "माफ करा"},
            "yes": {"hi": "हाँ", "mr": "हो"},
            "no": {"hi": "नहीं", "mr": "नाही"},
            "good": {"hi": "अच्छा", "mr": "चांगले"},
            "bad": {"hi": "बुरा", "mr": "वाईट"},
            "water": {"hi": "पानी", "mr": "पाणी"},
            "food": {"hi": "खाना", "mr": "जेवण"},
            "help": {"hi": "मदद", "mr": "मदत"},
            "bathroom": {"hi": "शौचालय", "mr": "शौचालय"},
            "medicine": {"hi": "दवाई", "mr": "औषध"},
            "pain": {"hi": "दर्द", "mr": "वेदना"},
            "hospital": {"hi": "अस्पताल", "mr": "रुग्णालय"},
            "doctor": {"hi": "डॉक्टर", "mr": "डॉक्टर"},
            "emergency": {"hi": "आपातकालीन", "mr": "आणीबाणी"},
            "mother": {"hi": "माँ", "mr": "आई"},
            "father": {"hi": "पिता", "mr": "वडील"},
            "family": {"hi": "परिवार", "mr": "कुटुंब"},
            "friend": {"hi": "दोस्त", "mr": "मित्र"},
            "name": {"hi": "नाम", "mr": "नाव"},
            "come": {"hi": "आना", "mr": "ये"},
            "go": {"hi": "जाना", "mr": "जा"},
            "today": {"hi": "आज", "mr": "आज"},
            "tomorrow": {"hi": "कल", "mr": "उद्या"},
            "morning": {"hi": "सुबह", "mr": "सकाळ"},
            "evening": {"hi": "शाम", "mr": "संध्याकाळ"},
            "happy": {"hi": "खुश", "mr": "आनंदी"},
            "sad": {"hi": "दुखी", "mr": "दुःखी"},
            "love": {"hi": "प्यार", "mr": "प्रेम"},
            "home": {"hi": "घर", "mr": "घर"},
            "school": {"hi": "स्कूल", "mr": "शाळा"},
            "work": {"hi": "काम", "mr": "काम"},
            "police": {"hi": "पुलिस", "mr": "पोलीस"},
            "teacher": {"hi": "शिक्षक", "mr": "शिक्षक"},
            "money": {"hi": "पैसा", "mr": "पैसे"},
            "phone": {"hi": "फ़ोन", "mr": "फोन"},
            "sleep": {"hi": "सोना", "mr": "झोपणे"},
            "eat": {"hi": "खाना", "mr": "खाणे"},
            "drink": {"hi": "पीना", "mr": "पिणे"},
        }

    def translate(self, text: str, source: str = "en", target: str = "hi") -> str:
        if source == target:
            return text
        normalized = text.lower().strip().replace(" ", "_")

        if source == "en" and normalized in self.dictionary:
            translation = self.dictionary[normalized].get(target)
            if translation:
                return translation

        if target == "en":
            for en_word, translations in self.dictionary.items():
                if translations.get(source) == text:
                    return en_word.replace("_", " ")

        return text
