import asyncio
import io
import wave
import math
import aiohttp

async def generate_tone_and_test():
    # 1. Generate 16kHz PCM WAV with a 440Hz tone
    sample_rate = 16000
    duration = 2.0
    num_samples = int(sample_rate * duration)
    
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        
        # Write "hello" or just a tone. 
        # A pure tone won't be recognized as words. Let's just test if it crashes.
        data = bytearray()
        for i in range(num_samples):
            val = int(math.sin(2 * math.pi * 440 * i / sample_rate) * 32767)
            data.extend(val.to_bytes(2, 'little', signed=True))
        wav.writeframes(data)
    
    buf.seek(0)
    audio_bytes = buf.read()
    
    # 2. Test the local ASR directly
    from pipeline2.asr import SpeechRecognizer
    asr = SpeechRecognizer()
    asr.load_models()
    res = await asr.recognize(audio_bytes, "en")
    print("Local ASR Result:", res)
    
    # 3. Test via HTTP to see if the server is throwing an error
    form = aiohttp.FormData()
    form.add_field('audio', audio_bytes, filename='speech.wav', content_type='audio/wav')
    
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:8000/listen?language=en', data=form) as response:
            print("HTTP Status:", response.status)
            print("HTTP Response:", await response.json())

if __name__ == "__main__":
    asyncio.run(generate_tone_and_test())
