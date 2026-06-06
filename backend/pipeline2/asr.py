"""Speech Recognition — converts audio to text using Vosk."""

import json
import logging

logger = logging.getLogger(__name__)

VOSK_AVAILABLE = False
try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    logger.warning("Vosk not installed.")


class SpeechRecognizer:
    def __init__(self):
        self.models = {}
        self.is_loaded = False

    def load_models(self):
        if not VOSK_AVAILABLE:
            logger.warning("Vosk not available — using mock")
            self.is_loaded = True
            return

        from config import VOSK_MODEL_HI, VOSK_MODEL_EN

        if VOSK_MODEL_HI.exists():
            try:
                self.models["hi"] = Model(str(VOSK_MODEL_HI))
                logger.info(f"Vosk Hindi model loaded from {VOSK_MODEL_HI}")
            except Exception as e:
                logger.error(f"Failed to load Hindi model: {e}")

        if VOSK_MODEL_EN.exists():
            try:
                self.models["en"] = Model(str(VOSK_MODEL_EN))
                logger.info(f"Vosk English model loaded from {VOSK_MODEL_EN}")
            except Exception as e:
                logger.error(f"Failed to load English model: {e}")

        self.is_loaded = True

    async def recognize(self, audio_bytes: bytes, language: str = "hi") -> dict:
        if not VOSK_AVAILABLE or language not in self.models:
            return {
                "text": "नमस्ते डॉक्टर" if language == "hi" else "hello doctor",
                "language": language,
                "confidence": 0.85,
                "source": "mock"
            }
        try:
            model = self.models[language]
            recognizer = KaldiRecognizer(model, 16000)
            recognizer.AcceptWaveform(audio_bytes)
            result = json.loads(recognizer.FinalResult())
            return {
                "text": result.get("text", ""),
                "language": language,
                "confidence": 0.85,
                "source": "vosk"
            }
        except Exception as e:
            logger.error(f"Speech recognition failed: {e}")
            return {"text": "", "language": language, "confidence": 0.0, "source": "error"}
