"""
VAANI Backend Configuration
All paths, thresholds, and constants in one place.
"""

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent

# AI4Bharat INCLUDE model
INCLUDE_MODEL_DIR = BASE_DIR / "models" / "include"
INCLUDE_WEIGHTS_PATH = INCLUDE_MODEL_DIR / "weights"

# Vosk speech recognition models
VOSK_MODEL_HI = BASE_DIR / "data" / "vosk-model-small-hi" / "vosk-model-hi"
VOSK_MODEL_EN = BASE_DIR / "data" / "vosk-model-en"

# iSign dataset
ISIGN_CSV_PATH = BASE_DIR / "data" / "isign" / "isign_index.csv"
ISIGN_VIDEO_DIR = BASE_DIR / "data" / "isign" / "videos"

# Temporary audio files
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

# ── Model Parameters ──────────────────────────────────────
NUM_FRAMES = 30              # Frames per sign sequence
NUM_LANDMARKS = 543          # MediaPipe Holistic landmarks
LANDMARK_DIMS = 1662         # 33*4 + 468*3 + 21*3 + 21*3
INCLUDE_CLASSES = 263        # INCLUDE vocabulary size
CONFIDENCE_THRESHOLD = 0.5   # Minimum confidence to accept prediction

# ── Server ─────────────────────────────────────────────────
CORS_ORIGINS = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:4173",   # Vite preview
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "capacitor://localhost",   # Capacitor Android
    "http://localhost",        # Capacitor iOS
]

# ── TTS ────────────────────────────────────────────────────
DEFAULT_TTS_LANG = "hi"      # Default text-to-speech language
SUPPORTED_LANGUAGES = ["hi", "mr", "en"]

# ── INCLUDE 263 Word Labels ───────────────────────────────
# This will be populated when the INCLUDE model is loaded.
# For now, a placeholder list. Replace with actual labels
# from the INCLUDE dataset after cloning.
INCLUDE_LABELS = []
