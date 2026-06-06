"""Text-to-Speech — converts text to spoken audio using gTTS."""

import io
import logging
from gtts import gTTS

logger = logging.getLogger(__name__)


class TextToSpeechEngine:
    LANG_MAP = {"hi": "hi", "mr": "mr", "en": "en"}

    def speak(self, text: str, lang: str = "hi") -> bytes:
        gtts_lang = self.LANG_MAP.get(lang, "hi")
        try:
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            logger.info(f"Generated speech for: '{text}' in {lang}")
            return audio_buffer.read()
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            raise RuntimeError(f"Text-to-speech failed: {e}")

    def speak_emergency(self, lang: str = "hi") -> bytes:
        messages = {
            "hi": "यह व्यक्ति बधिर है और उसे सहायता की आवश्यकता है। कृपया इनकी मदद करें।",
            "mr": "ही व्यक्ती कर्णबधिर आहे आणि त्यांना मदतीची गरज आहे. कृपया त्यांना मदत करा.",
            "en": "This person is deaf and needs help. Please assist them.",
        }
        text = messages.get(lang, messages["en"])
        return self.speak(text, lang)
