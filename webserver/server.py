from aiohttp import web
from threading import Thread
import asyncio
import time
import uuid

loop = asyncio.get_event_loop()

async def countdown(redis, key, seconds):
    while seconds > 0:
        value = await redis.get(key)
        if value == 'STOP':
            break
        else:
            redis.set(key, value)
        seconds -= 1
        await asyncio.sleep(1)
    redis.delete(key)


def long_blocking_thing(sleep):
    time.sleep(sleep)
    return 42


async def worker(q):
    await q.put(b'coroutine: hello')
    for i in range(1, 11):
        await asyncio.sleep(1)
        await q.put(b'coroutine: ping %d' % i)
    await q.put(b'The end!')
    await q.put(None)


def start_background_work(q=None):
    if q is None:
        q = asyncio.Queue()
    def _thread():
        # you can run non-asyncio code in a separate thread
        # but use run_coroutine_threadsafe to fill in the queue
        result = long_blocking_thing(5)
        asyncio.run_coroutine_threadsafe(
            q.put(b'thread: hello %d' % result), loop)
    Thread(target=_thread).start()
    loop.create_task(worker(q))
    return q


# stupid session implementation
session_store = {}


async def longpoll(request):
    response = web.Response()

    session_key = request.cookies.get('aio-session')
    if session_key is None:
        session_key = str(uuid.uuid4())
        response.set_cookie('aio-session', session_key)

    q = session_store.get(session_key)
    if q is None:
        # new session start some background work
        q = start_background_work()
        session_store[session_key] = q
    msg = await q.get()
    if msg is None:
        # coroutines are done now
        del session_store[session_key]
        return web.Response(status=204)

    response.body = msg + b'\n'   # newline for curl :)
    return response


async def sse_handler(request):
    if request.headers.get('accept') != 'text/event-stream':
        return web.Response(status=406)
    stream = web.StreamResponse()
    stream.headers['Content-Type'] = 'text/event-stream'
    stream.headers['Cache-Control'] = 'no-cache'
    stream.headers['Connection'] = 'keep-alive'
    stream.enable_chunked_encoding()
    await stream.prepare(request)

    q = start_background_work()

    while True:
        msg = await q.get()
        if msg is None:
            break
        stream.write(b"data: %s\r\n\r\n" % msg)

    await stream.write_eof()
    return stream


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    q = start_background_work()

    while True:
        msg = await q.get()
        # or done, pending = await asyncio.wait([q.get(), ws.receive()],
        # return_when=asyncio.FIRST_COMPLETED)
        if msg is None:
            break
        else:
            ws.send_bytes(msg)

    await ws.close()
    return ws

app = web.Application()
app.router.add_route('GET', '/', longpoll)
app.router.add_route('GET', '/ws', websocket_handler)
app.router.add_route('GET', '/sse', sse_handler)


async def init(loop):
    handler = app.make_handler()
    srv = await loop.create_server(handler, '0.0.0.0', 8080)
    print('serving on', srv.sockets[0].getsockname())
    return srv


def main():
    loop.run_until_complete(init(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass


main()
