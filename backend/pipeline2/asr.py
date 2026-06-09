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
            
        if len(audio_bytes) < 1000:
            return {"text": "", "language": language, "confidence": 0.0, "source": "error", "error_msg": "Audio too short."}
            
        try:
            import av
            import io
            
            # Decode audio_bytes (likely WebM/Opus from browser) to raw PCM
            container = av.open(io.BytesIO(audio_bytes))
            stream = container.streams.audio[0]
            
            # Vosk requires 16000Hz, mono, 16-bit PCM
            resampler = av.AudioResampler(
                format='s16',
                layout='mono',
                rate=16000,
            )
            
            pcm_data = bytearray()
            for frame in container.decode(stream):
                resampled_frames = resampler.resample(frame)
                for r_frame in resampled_frames:
                    pcm_data.extend(r_frame.to_ndarray().tobytes())
                    
            model = self.models[language]
            recognizer = KaldiRecognizer(model, 16000)
            
            # Pass the raw PCM bytes to Vosk
            recognizer.AcceptWaveform(bytes(pcm_data))
            
            # Vosk sometimes stores the text in Result() if it detected an endpoint,
            # or in FinalResult() if it's the end of the stream.
            res1 = json.loads(recognizer.Result())
            res2 = json.loads(recognizer.FinalResult())
            
            text = res1.get("text", "")
            if not text:
                text = res2.get("text", "")
            
            return {
                "text": text,
                "language": language,
                "confidence": 0.85,
                "source": "vosk"
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Speech recognition failed: {e}")
            return {"text": "", "language": language, "confidence": 0.0, "source": "error", "error_msg": str(e)}

    def create_stream_recognizer(self, language: str = "hi"):
        """Returns a KaldiRecognizer instance for real-time streaming."""
        if not VOSK_AVAILABLE:
            logger.error("VOSK_AVAILABLE is False")
            return None
        if language not in self.models:
            logger.error(f"Language '{language}' not in self.models. Available: {list(self.models.keys())}")
            return None
            
        model = self.models[language]
        return KaldiRecognizer(model, 16000)
