"""
VAANI — FastAPI Backend Server
================================

THIS IS THE HEART OF THE APP.

WHAT IS FastAPI?
FastAPI is a Python web framework (like Express.js for Node.js).
It lets you create "endpoints" — URLs that your frontend can call.

Example:
    Frontend sends: POST http://localhost:8000/predict {landmarks data}
    Backend returns: {"sign": "hello", "confidence": 0.94}

WHAT IS AN ENDPOINT?
An endpoint is a URL + HTTP method that does something specific:
    GET  /health    → Returns server status (read-only, no data sent)
    POST /predict   → Sends landmark data, gets back a prediction
    POST /speak     → Sends text, gets back audio
    
    GET  = "give me information" (like opening a webpage)
    POST = "here's some data, process it" (like submitting a form)

WHAT IS CORS?
CORS = Cross-Origin Resource Sharing.
Your frontend runs on http://localhost:5173 (Vite)
Your backend runs on http://localhost:8000 (FastAPI)
By default, browsers BLOCK requests between different ports (security).
CORS middleware tells the browser: "It's okay, allow these requests."

HOW TO RUN THIS SERVER:
    cd backend
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

    --reload  = auto-restarts when you change code (for development)
    --port    = which port to listen on
    main:app  = look in main.py for the variable called 'app'
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel

from config import CORS_ORIGINS, CONFIDENCE_THRESHOLD, ISIGN_CSV_PATH
from utils.preprocessing import validate_sequence, normalize_landmarks
from pipeline1.recognizer import ISLRecognizer
from pipeline1.tts import TextToSpeechEngine
from pipeline2.asr import SpeechRecognizer
from pipeline2.translator import Translator
from pipeline2.isign_lookup import ISignLookup

# ── Logging Setup ──────────────────────────────────────────
# Logging = printing messages about what the server is doing.
# Useful for debugging. Shows up in your terminal.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)s │ %(name)s │ %(message)s"
)
logger = logging.getLogger("vaani")

# ── Global Model Instances ──────────────────────────────────
# These are created ONCE when the server starts, then reused for every request.
# Loading models is slow (seconds), but using them is fast (milliseconds).
recognizer = ISLRecognizer()
tts_engine = TextToSpeechEngine()
asr_engine = SpeechRecognizer()
translator = Translator()
isign_lookup = ISignLookup()


# ── Lifespan (Startup / Shutdown) ──────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    WHAT IS LIFESPAN?
    Code that runs when the server starts up and shuts down.
    
    STARTUP: Load all AI models into memory (RAM).
    SHUTDOWN: Clean up resources.
    """
    import threading
    # ── STARTUP ──
    logger.info("=" * 60)
    logger.info("  VAANI Backend Starting Up...")
    logger.info("=" * 60)
    
    # CRITICAL: Import torch in the MAIN thread before starting the background thread.
    # If torch is imported for the first time inside a worker thread on Windows, 
    # it can cause an indefinite deadlock in C++ multi-threading initialization.
    try:
        import torch
        logger.info("Torch pre-imported successfully in main thread.")
    except ImportError:
        pass
    
    def load_models_bg():
        try:
            # Load ISL recognition model
            logger.info("Loading ISL recognizer (INCLUDE model) in background...")
            recognizer.load_model()
            
            # Load speech recognition models
            logger.info("Loading speech recognition (Vosk) in background...")
            asr_engine.load_models()
            
            # Load iSign video index
            logger.info("Loading iSign video index in background...")
            isign_lookup.load_index(str(ISIGN_CSV_PATH))
            
            logger.info("=" * 60)
            logger.info("  All models loaded successfully! ✅")
            logger.info("=" * 60)
        except Exception as e:
            logger.error(f"Error loading models in background: {e}")

    # Start loading models in a separate daemon thread to avoid blocking server or deadlocking
    t = threading.Thread(target=load_models_bg, daemon=True)
    t.start()
    
    logger.info("  VAANI Backend Ready! (Models are loading in the background)")
    logger.info("  → API docs: http://localhost:8000/docs")
    logger.info("=" * 60)
    
    yield  # Server is running — handle requests
    
    # ── SHUTDOWN ──
    logger.info("VAANI Backend shutting down...")


# ── Create FastAPI App ─────────────────────────────────────
app = FastAPI(
    title="VAANI ISL Recognition API",
    description="Real-time ISL ↔ Speech translation for 4.5 million ISL users",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Middleware ────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,       # Which frontends can call us
    allow_credentials=True,
    allow_methods=["*"],               # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],               # Allow all headers
)


# ══════════════════════════════════════════════════════════
#  REQUEST / RESPONSE MODELS
# ══════════════════════════════════════════════════════════
# These are "schemas" — they define WHAT data the API expects
# and WHAT it returns. Pydantic validates the data automatically.

class PredictRequest(BaseModel):
    """
    What the frontend sends to /predict.
    
    WHAT IS PYDANTIC?
    Pydantic is a library that validates data. If the frontend sends
    wrong data (e.g., a string instead of a list), Pydantic will
    automatically return a clear error message. You don't need to
    write validation code yourself.
    """
    sequence: list  # [[1662 floats] × 30 frames]


class SpeakRequest(BaseModel):
    """What the frontend sends to /speak."""
    text: str       # The text to speak aloud
    lang: str = "hi"  # Language: "hi", "mr", or "en"


class TranslateRequest(BaseModel):
    """What the frontend sends to /translate."""
    text: str
    source: str = "en"   # Source language
    target: str = "hi"   # Target language


class LookupRequest(BaseModel):
    """What the frontend sends to /lookup."""
    text: str  # The text to find ISL videos for


# ══════════════════════════════════════════════════════════
#  PIPELINE 1 ENDPOINTS — Deaf → Hearing (Sign to Speech)
# ══════════════════════════════════════════════════════════

@app.post("/predict")
async def predict(request: PredictRequest):
    """
    PIPELINE 1, STEP 3: Recognize ISL from landmarks.
    
    Frontend captures 30 frames of MediaPipe landmarks → sends here.
    We run the INCLUDE model → return the predicted word.
    
    INPUT:  { "sequence": [[1662 floats] × 30 frames] }
    OUTPUT: { "sign": "hello", "confidence": 0.94, "source": "include" }
    """
    try:
        # Step 1: Validate and preprocess the landmarks
        sequence = validate_sequence(request.sequence)
        sequence = normalize_landmarks(sequence)
        
        # Step 2: Run the INCLUDE model
        word, confidence = recognizer.predict(sequence)
        
        # Step 3: Check confidence threshold
        if confidence < CONFIDENCE_THRESHOLD:
            # TODO: In the future, fall through to iSign LSTM here
            return {
                "sign": word,
                "confidence": confidence,
                "source": "include",
                "warning": "Low confidence — prediction may be inaccurate"
            }
        
        return {
            "sign": word,
            "confidence": confidence,
            "source": "include"
        }
        
    except ValueError as e:
        # Invalid input data
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"/predict error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")


@app.post("/speak")
async def speak(request: SpeakRequest):
    """
    PIPELINE 1, STEP 6: Convert text to speech audio.
    
    INPUT:  { "text": "नमस्ते", "lang": "hi" }
    OUTPUT: MP3 audio file (streamed directly to the frontend)
    
    WHAT IS 'media_type'?
    It tells the browser what kind of data we're sending back.
    "audio/mpeg" = MP3 audio. The browser knows to play it as sound.
    """
    try:
        audio_bytes = tts_engine.speak(request.text, request.lang)
        
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3"
            }
        )
    except Exception as e:
        logger.error(f"/speak error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")


@app.post("/speak/emergency")
async def speak_emergency(lang: str = "hi"):
    """
    EMERGENCY BUTTON: Speaks a pre-defined help message.
    "This person is deaf and needs help. Please assist them."
    """
    try:
        audio_bytes = tts_engine.speak_emergency(lang)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Emergency TTS failed: {e}")


# ══════════════════════════════════════════════════════════
#  PIPELINE 2 ENDPOINTS — Hearing → Deaf (Speech to ISL)
# ══════════════════════════════════════════════════════════

@app.post("/listen")
async def listen(audio: UploadFile = File(...), language: str = "hi"):
    """
    PIPELINE 2, STEP 1: Convert speech audio to text.
    
    INPUT:  Audio file (WAV) uploaded via multipart form
    OUTPUT: { "text": "नमस्ते डॉक्टर", "language": "hi" }
    
    WHAT IS UploadFile?
    FastAPI's way of receiving file uploads. The frontend sends an
    audio recording, and we receive it as a file object we can read.
    """
    try:
        audio_bytes = await audio.read()
        result = await asr_engine.recognize(audio_bytes, language)
        return result
    except Exception as e:
        logger.error(f"/listen error: {e}")
        raise HTTPException(status_code=500, detail=f"Speech recognition failed: {e}")


@app.post("/translate")
async def translate(request: TranslateRequest):
    """
    PIPELINE 1 & 2: Translate between Hindi, Marathi, and English.
    
    INPUT:  { "text": "water", "source": "en", "target": "hi" }
    OUTPUT: { "translated": "पानी", "source": "en", "target": "hi" }
    """
    try:
        translated = translator.translate(
            request.text,
            source=request.source,
            target=request.target
        )
        return {
            "translated": translated,
            "source": request.source,
            "target": request.target
        }
    except Exception as e:
        logger.error(f"/translate error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {e}")


@app.post("/lookup")
async def lookup(request: LookupRequest):
    """
    PIPELINE 2, STEP 4: Find ISL videos for given text.
    
    Implements the 4-level fallback chain:
    Level 1: Full sentence → one video
    Level 2: Word by word → video sequence
    Level 3: INCLUDE vocab → show text
    Level 4: Fingerspell → A-Z alphabet videos
    
    INPUT:  { "text": "hello doctor" }
    OUTPUT: { "level": 2, "results": [...], "fallback_used": false }
    """
    try:
        result = isign_lookup.find(request.text)
        return result
    except Exception as e:
        logger.error(f"/lookup error: {e}")
        raise HTTPException(status_code=500, detail=f"Lookup failed: {e}")


# ══════════════════════════════════════════════════════════
#  UTILITY ENDPOINTS
# ══════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    """
    Health check — tells you if the server and all models are working.
    
    This is the FIRST thing you should test:
    Open http://localhost:8000/health in your browser.
    """
    return {
        "status": "ok",
        "app": "VAANI ISL Recognition API",
        "models": {
            "include_recognizer": recognizer.is_loaded,
            "tts_engine": True,
            "speech_recognizer": asr_engine.is_loaded,
            "translator": translator.is_loaded,
            "isign_lookup": isign_lookup.is_loaded,
        }
    }


@app.get("/vocab")
async def vocab():
    """
    Returns the list of words the model can recognize.
    Useful for the frontend to show "supported words" to the user.
    """
    return {
        "include_words": recognizer.labels,
        "include_count": len(recognizer.labels),
        "isign_words": list(isign_lookup.word_index.keys())[:50],  # First 50
        "isign_count": len(isign_lookup.word_index),
    }


# ══════════════════════════════════════════════════════════
#  AUTO-GENERATED API DOCS
# ══════════════════════════════════════════════════════════
# FastAPI automatically generates interactive API documentation!
# After starting the server, visit:
#   http://localhost:8000/docs    ← Swagger UI (pretty, interactive)
#   http://localhost:8000/redoc   ← ReDoc (detailed, readable)
#
# You can TEST every endpoint directly in the browser! 🎉
