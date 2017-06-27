import asyncio
import aioredis
import models
from random import randint

T10SEC = 10
T10MIN = 10 * 60


async def listen_to_redis(app):
    try:
        sub = await aioredis.create_redis(('localhost', 6379), loop=app.loop)
        ch, *_ = await sub.subscribe('news')
        async for msg in ch.iter(encoding='utf-8'):
            # Forward message to all connected websockets:
            for ws in app['websockets']:
                ws.send_str('{}: {}'.format(ch.name, msg))
    except asyncio.CancelledError:
        pass
    finally:
        await sub.unsubscribe(ch.name)
        await sub.quit()


async def start_background_tasks(app):
    redis_connection = await aioredis.create_connection(('localhost', 6379))
    redis = app['redis'] = aioredis.Redis(redis_connection)
    users = {}
    for key in await redis.keys('*:timer-*'):
        username, timername = key.decode('utf-8').split(':')
        user = users.get(username, None)
        if user is None:
            uid = int(username.split('-')[1])
            users[username] = user = models.User(redis, uid)

        timer = models.Timer(redis, user)
        timer_size = timername.split('-')[1]
        timer_size = timer_size if timer_size != 'None' else 0
        timer_size = int(timer_size)
        timer_left = int(await redis.get(key) or 0)
        asyncio.ensure_future(timer.start(timer_left, timer_size))

    if len(users) < 2000:
        for _ in range(2000 - len(users)):
            uid = await redis.incr('client_count')
            print('new user', uid)
            user = models.User(redis, uid)
            asyncio.ensure_future(user.get_cell())
            for _ in range(randint(1, 4)):
                timer = models.Timer(redis, user)
                asyncio.ensure_future(timer.start(randint(T10SEC, T10MIN)))

    # app['redis_listener'] = app.loop.create_task(listen_to_redis(app))


async def cleanup_background_tasks(app):
    app['redis'].close()
