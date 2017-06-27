import asyncio
from aiohttp import web
from aiohttp_session import get_session
from random import randint
import models

T10SEC = 10
T10MIN = 10 * 60


async def index(request):
    redis = request.app['redis']
    session = await get_session(request)
    uid = session.get('uid', None)
    if uid is None:
        uid = await redis.incr('client_count')
        session['uid'] = uid
    user = models.User(redis, uid)

    if request.method == 'POST':  # create timer
        timer = models.Timer(redis, user)
        asyncio.ensure_future(timer.start(randint(T10SEC, T10MIN)))
    if request.method == 'PUT':  # move player
        action = await request.json()
        await user.move_to(action['move'])
    if request.method == 'GET':
        parameters = request.rel_url.query
        if parameters.get('all', None):
            data = await user.to_json(show_all=True)
            print('all')
            return web.json_response(data)
    data = await user.to_json()
    return web.json_response(data)
