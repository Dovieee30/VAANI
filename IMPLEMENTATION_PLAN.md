# VAANI — Implementation Plan (Online + FastAPI)

## Architecture

```
┌─────────────────────────────┐           ┌─────────────────────────────────┐
│   CAPACITOR / BROWSER       │           │   FASTAPI BACKEND (Python)      │
│   (Existing Vite Frontend)  │   HTTP    │                                 │
│                             │ ◄────────►│   POST /predict    (sign→word)  │
│   • MediaPipe landmarks    │           │   POST /speak      (text→audio) │
│   • Camera + Mic UI         │           │   POST /listen     (audio→text) │
│   • Video player            │           │   POST /translate  (hi↔en)      │
│   • Chat history            │           │   POST /lookup     (text→video) │
│                             │           │   GET  /health                  │
└─────────────────────────────┘           └─────────────────────────────────┘
```

---

## Project Structure (What Gets Built)

```
VAANI/
├── frontend/                              # ✅ EXISTS — minor changes only
│   ├── index.html                         # Landing page (no changes)
│   ├── app.html                           # [MODIFY] Add Pipeline 2 UI
│   ├── core/
│   │   └── mediapipe_extractor.js         # ✅ EXISTS — no changes
│   ├── js/
│   │   └── demo.js                        # [MODIFY] Wire to backend API
│   ├── css/                               # ✅ EXISTS — no changes
│   ├── package.json
│   └── vite.config.js
│
├── backend/                               # [NEW] — Everything below is new
│   ├── requirements.txt                   # Python dependencies
│   ├── main.py                            # FastAPI server (all endpoints)
│   ├── config.py                          # Paths, thresholds, constants
│   │
│   ├── pipeline1/                         # Sign → Speech
│   │   ├── __init__.py
│   │   ├── recognizer.py                  # INCLUDE model wrapper
│   │   └── tts.py                         # gTTS text-to-speech
│   │
│   ├── pipeline2/                         # Speech → Sign
│   │   ├── __init__.py
│   │   ├── asr.py                         # Vosk speech recognition
│   │   ├── translator.py                  # IndicTrans2 wrapper
│   │   └── isign_lookup.py                # iSign CSV search + fallback
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   └── preprocessing.py               # Landmark normalization
│   │
│   ├── models/
│   │   └── include/                        # ← User clones INCLUDE repo here
│   │
│   └── data/
│       ├── vosk-model-hi/                  # ← User downloads Vosk Hindi model
│       ├── vosk-model-en/                  # ← User downloads Vosk English model
│       └── isign/                          # ← User downloads iSign CSV + videos
│
└── README.md
```

---

## API Endpoints (Detailed)

### `POST /predict` — Pipeline 1: Sign → Word
```
Request:  { "sequence": [[1662 floats] × 30 frames] }
Response: { "sign": "namaste", "confidence": 0.94, "source": "include" }
```

### `POST /speak` — Text → Audio
```
Request:  { "text": "नमस्ते", "lang": "hi" }
Response: audio/mp3 file stream
```

### `POST /listen` — Audio → Text
```
Request:  multipart/form-data with audio file
Response: { "text": "hello doctor", "language": "en" }
```

### `POST /translate` — Hindi ↔ English
```
Request:  { "text": "पानी", "source": "hi", "target": "en" }
Response: { "translated": "water" }
```

### `POST /lookup` — Text → ISL Video URLs
```
Request:  { "text": "hello doctor" }
Response: {
    "level": 2,
    "results": [
        { "word": "hello", "type": "video", "url": "/videos/hello.mp4" },
        { "word": "doctor", "type": "video", "url": "/videos/doctor.mp4" }
    ],
    "fallback_used": false
}
```

### `GET /health`
```
Response: { "status": "ok", "models": { "include": true, "vosk": true, "indictrans": true } }
```

---

## Build Order — Step by Step

### Phase 1: Backend Scaffold (I build, you run)

**I create**: `requirements.txt`, `main.py`, `config.py`, `utils/preprocessing.py`

**You run**:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Test**: Open `http://localhost:8000/health` in browser → should see `{"status": "ok"}`

---

### Phase 2: Pipeline 1 — Sign → Speech (I build, you clone model)

**I create**: `pipeline1/recognizer.py`, `pipeline1/tts.py`

**You run**:
```bash
git clone https://github.com/AI4Bharat/INCLUDE.git backend/models/include
```

**Test**: Frontend camera → sign → see predicted word → hear it spoken

---

### Phase 3: Wire Frontend to Backend (I build)

**I modify**: `frontend/js/demo.js`, `frontend/app.html`

**Test**: Open `http://localhost:5173` → Start Interpreter → sign → word appears + spoken aloud

---

### Phase 4: Pipeline 2 — Speech → Sign (I build, you download data)

**I create**: `pipeline2/asr.py`, `pipeline2/translator.py`, `pipeline2/isign_lookup.py`

**You download**:
```bash
# Vosk Hindi model (~50MB)
# iSign dataset from HuggingFace
```

**Test**: Speak in Hindi/English → see ISL video on screen

---

### Phase 5: Capacitor Mobile Wrapper (I set up)

```bash
npm install @capacitor/core @capacitor/cli
npx cap init VAANI com.vaani.app
npx cap add android
npx cap sync
npx cap open android
```

---

## What I Build vs What You Do

| **I build (code)** | **You do (data/models)** |
|---|---|
| All backend Python files | `git clone` INCLUDE repo |
| All API endpoints | Download Vosk Hindi/English models |
| Frontend wiring to backend | Download iSign CSV + videos from HuggingFace |
| Capacitor setup | Run `pip install` and `uvicorn` |
| TTS, ASR, translation wrappers | Test on phone |

---

## Verification

| Test | Expected Result |
|------|----------------|
| `curl localhost:8000/health` | `{"status": "ok", ...}` |
| Sign "namaste" at camera | Text shows "namaste (94%)", voice says "नमस्ते" |
| Say "पानी दो" into mic | ISL video for "water" + "give" plays on screen |
| Word not in iSign | Fingerspelling fallback A-Z plays |
| Backend down | Frontend shows "Server not reachable" gracefully |


