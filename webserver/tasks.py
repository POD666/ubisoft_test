import asyncio
import aioredis
import models


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
            users['username'] = user = models.User(redis, uid)

        timer = models.Timer(redis, user)
        timer_size = timername.split('-')[1]
        timer_size = timer_size if timer_size != 'None' else 0
        timer_size = int(timer_size)
        timer_left = int(await redis.get(key))
        asyncio.ensure_future(timer.start(timer_left, timer_size))

    # app['redis_listener'] = app.loop.create_task(listen_to_redis(app))


async def cleanup_background_tasks(app):
    app['redis'].close()
