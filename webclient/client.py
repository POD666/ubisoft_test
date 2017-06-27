import aiohttp
import asyncio
from itertools import cycle
from random import choice, shuffle

URL = "http://localhost:8080/"
chance_list = [0, 0, 30, 50, 30, 50, 50]

DIRECTIONS = ["UP", "DOWN", "LEFT", "RIGHT"]


async def silent_client():
    async with aiohttp.ClientSession() as session:
        shuffle(chance_list)
        for chance in cycle(chance_list):
            if chance < 20:
                async with session.post(URL) as resp:
                    await resp.json()
                    pass
            elif chance < 40:
                data = {"move": choice(DIRECTIONS)}
                async with session.put(URL, json=data) as resp:
                    await resp.json()
                    pass
            else:
                async with session.get(URL) as resp:
                    await resp.json()
                    pass
            await asyncio.sleep(5)


async def create_client():
    async with aiohttp.ClientSession() as session:
        shuffle(chance_list)
        for chance in cycle(chance_list):
            if chance < 20:
                async with session.post(URL) as resp:
                    print(await resp.json())
            elif chance < 40:
                data = {"move": choice(DIRECTIONS)}
                async with session.put(URL, json=data) as resp:
                    print(await resp.json())
            else:
                async with session.get(URL+'?all=True') as resp:
                    print(await resp.json())
            await asyncio.sleep(5)


loop = asyncio.get_event_loop()
tasks = [create_client(), ] + list(map(lambda i: silent_client(), range(20)))
loop.run_until_complete(asyncio.wait(tasks))
loop.close()
