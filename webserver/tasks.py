import asyncio
import aioredis


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
    


    # app['redis_listener'] = app.loop.create_task(listen_to_redis(app))


async def cleanup_background_tasks(app):
    app['redis'].close()
