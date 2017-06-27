import json
import asyncio
from functools import reduce
from random import randint

SIZE_X = 512
SIZE_Y = 512
SIZE = (SIZE_X, SIZE_Y)
AREA_X = 32 / 2
AREA_Y = 32 / 2


def random_point():
    return (randint(0, SIZE_X - 1), randint(0, SIZE_Y - 1))


async def get_users_in_area(redis, cell):
    X, Y = key2cell(cell)
    for key in await redis.keys('*:cell-'):
        x, y = key2cell(key)
        if (abs(X - x) < AREA_X) and (abs(Y - y) < AREA_Y):
            username, cell = key.split(':')
            yield username, cell


def key2cell(key):
    if ':cell-' in key:
        cell = key.split(':cell-')[1].split('x')
    else:
        cell = key.split('x')
    x, y = map(int, cell)  # player-25:cell-23x45
    return x, y


class Timer():
    user = None
    timeout = None

    def __init__(self, redis, user):
        self.redis = redis
        self.user = user

    async def start(self, timeout, name=None):
        if await self.user.get_timers_count() == 4:
            return
        timer_key = ''.join([self.user.name, ':timer-', name or str(timeout)])
        self.timeout = timeout
        self.redis.set(timer_key, self.timeout)
        while self.timeout > 0:
            self.redis.set(timer_key, self.timeout)
            self.timeout -= 1
            await asyncio.sleep(1)
        self.redis.delete(timer_key)

    def remove(self):
        self.timeout = 0


class User():
    uid = None
    name = 'player-'
    cell = ()
    timers = {}

    def __init__(self, redis, uid):
        self.redis = redis
        self.uid = uid
        self.name += str(uid)

    async def _get_all_data(self):
        data = getattr(self, 'redis_data', None)
        if not data:
            keys = await self.redis.keys(self.name + '*')
            pipe = self.redis.pipeline()
            for key in keys:
                pipe.get(key)
            values = await pipe.execute()
            keys = list(map(lambda s: s.decode("utf-8"), keys))
            values = list(map(lambda s: s.decode("utf-8"), values))
            data = dict(zip(keys, values))
            self.redis_data = data
            print(data)
        return data

    async def get_timers_count(self):
        data = await self._get_all_data()
        length = reduce(
            lambda x, key: x + 1 if ':timer-' in key else 0,
            data.keys(),
            0  # initializer
        )
        return length

    async def get_timers(self):
        data = await self._get_all_data()
        filtered = filter(lambda x: ':timer-' in x[0], data.items())
        return dict(filtered)

    async def move_to(self, direction):
        cell = await self.get_cell()
        DIRECTION = {
            "UP": lambda x, y: (x, str(int(y) - 1)),
            "DOWN": lambda x, y: (x, str(int(y) + 1)),
            "RIGHT": lambda x, y: (str(int(x) + 1), y),
            "LEFT": lambda x, y: (str(int(x) - 1), y)
        }
        new_cell = DIRECTION[direction](*cell.split('x'))
        old_key = self.name + ':cell-' + cell
        del self.redis_data[old_key]
        self.redis.delete(old_key)
        new_cell = 'x'.join(map(str, new_cell))
        print('move %s from %s to %s' % (direction, cell, new_cell))
        cell_key = self.name + ':cell-' + new_cell
        self.redis.set(cell_key, "*")
        self.redis_data[cell_key] = None

    async def get_cell(self):
        data = await self._get_all_data()
        filtered = filter(lambda x: ':cell-' in x[0], data.items())
        try:
            key = next(filtered)[0]
        except Exception as e:  # indexerror indicates new users with no cell
            print(e)
            cell = 'x'.join(map(str, [randint(1, SIZE_X), randint(1, SIZE_Y)]))
            cell_key = self.name + ':cell-' + cell
            # redis on windows limited from HSCAN etc
            # that is why cell value in the title
            self.redis.set(cell_key, "*")
            return cell
        return key.split(':cell-')[1]

    async def get_field_of_view(self):
        cell = await self.get_cell()
        players = []
        async for username, cell in get_users_in_area(self.redis, cell):
            players.append({"name": username, "cell": cell})
        return players

    async def to_json(self):
        data = {
            'uid': self.uid,
            'name': self.name,
            'cell': await self.get_cell(),
            'timers': await self.get_timers(),
            'field_of_view': await self.get_field_of_view(),
        }
        return json.dumps(data)
