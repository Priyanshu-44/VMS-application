"""Manual WS smoke test: connects to /ws/events and prints whatever arrives for 20s."""
import asyncio
import websockets


async def main():
    uri = "ws://127.0.0.1:8000/ws/events"
    async with websockets.connect(uri) as ws:
        print("connected, listening for 20s...")
        try:
            async with asyncio.timeout(20):
                count = 0
                async for message in ws:
                    count += 1
                    print(f"[{count}] {message[:200]}")
        except TimeoutError:
            print(f"done, received {count} message(s)")


asyncio.run(main())
