import asyncio
import io
import aiohttp
import av

async def test_webm():
    # Let's see if we can create a simple WebM or just rely on a known good WebM bytes.
    # Actually, if the ASR returns {"text": ""}, it could be that the speech was too short,
    # or Vosk needs `recognizer.Result()` instead of just `FinalResult()`.
    
    # Wait! In Vosk, `AcceptWaveform` returns True if silence is detected and a result is ready.
    # To get the final text, you usually do:
    # recognizer.AcceptWaveform(data)
    # result = json.loads(recognizer.FinalResult())
    
    from pipeline2.asr import SpeechRecognizer
    asr = SpeechRecognizer()
    asr.load_models()
    
    # What if we pass empty bytes?
    res = await asr.recognize(b"", "en")
    print("Empty bytes result:", res)

if __name__ == "__main__":
    asyncio.run(test_webm())
