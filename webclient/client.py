import aiohttp
import asyncio
import time
from random import randint, choice

URL = "http://localhost:8080/"
chance_list = [0, 0, 30, 50, 30, 50, 50]

DIRECTIONS = ["UP", "DOWN", "LEFT", "RIGHT"]


async def create_client():
    with aiohttp.ClientSession() as session:
        while True:
            chance = chance_list.pop(0) if chance_list else randint(1, 100)
            if chance < 20:
                async with session.post(URL) as resp:
                    print(await resp.json())
            elif chance < 40:
                data = {"move": choice(DIRECTIONS)}
                async with session.put(URL, json=data) as resp:
                    print(await resp.json())
            else:
                async with session.get(URL) as resp:
                    print(await resp.json())
            time.sleep(5)


loop = asyncio.get_event_loop()
loop.run_until_complete(create_client())
loop.close()
