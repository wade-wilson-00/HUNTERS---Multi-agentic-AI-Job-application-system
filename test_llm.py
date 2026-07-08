import asyncio
from agents.hunter import HunterAgent

async def test():
    hunter = HunterAgent()
    try:
        async for t in hunter.respond_stream("Hello"):
            print(t, end="")
    except Exception as e:
        print(f"Exception: {e}")

asyncio.run(test())
