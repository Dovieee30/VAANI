import asyncio
import websockets

async def test():
    try:
        async with websockets.connect('ws://localhost:8000/ws/listen?language=en') as ws:
            print("OPEN")
            await ws.close()
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(test())
