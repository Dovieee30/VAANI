import asyncio
import websockets
import json

async def test_ws():
    try:
        async with websockets.connect("ws://localhost:8000/ws/listen?language=en") as ws:
            print("Connected to WebSocket!")
            
            # Send dummy 16-bit PCM data (e.g. 4000 bytes)
            dummy_pcm = b'\x00' * 4000
            await ws.send(dummy_pcm)
            
            # Receive response
            res = await ws.recv()
            print("Received:", res)
    except Exception as e:
        print("Error connecting to WS:", e)

if __name__ == "__main__":
    asyncio.run(test_ws())
