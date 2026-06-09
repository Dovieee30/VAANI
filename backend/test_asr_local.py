import asyncio
import logging
logging.basicConfig(level=logging.DEBUG)

from pipeline2.asr import SpeechRecognizer

async def test():
    # 1. Initialize and load
    asr = SpeechRecognizer()
    asr.load_models()
    print("Models loaded:", asr.is_loaded)
    print("Available languages:", asr.models.keys())
    
    # 2. Try to recognize with a mock wav or webm buffer
    # We can just pass some dummy bytes to trigger PyAV to see if it fails on initialization
    dummy_bytes = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    
    res = await asr.recognize(dummy_bytes, language="en")
    print("Result:", res)

if __name__ == "__main__":
    asyncio.run(test())
