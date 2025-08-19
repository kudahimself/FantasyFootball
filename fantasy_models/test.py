import asyncio
import aiohttp
from fpl import FPL

async def main_function():
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        # Your code to retrieve data here...
        player = await fpl.get_player(123, include_summary=True)
        print(player.history)

if __name__ == "__main__":
    asyncio.run(main_function())