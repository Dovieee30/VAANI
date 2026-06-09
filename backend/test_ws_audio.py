import asyncio
import websockets
import json
import wave
import sys
import os

async def test_ws_audio():
    # Find a test audio file or create dummy
    # We will generate a sine wave if no speech file exists, but sine wave won't be recognized as speech.
    print("Testing websocket with silence...")
    try:
        async with websockets.connect("ws://localhost:8000/ws/listen?language=en") as ws:
            print("Connected!")
            
            # Send 2 seconds of dummy data
            for _ in range(20):
                await ws.send(b'\x00' * 3200)
                await asyncio.sleep(0.1)
                try:
                    res = await asyncio.wait_for(ws.recv(), timeout=0.1)
                    print("Received:", res)
                except asyncio.TimeoutError:
                    pass
            
            print("Done sending. Closing.")
            await ws.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test_ws_audio())
