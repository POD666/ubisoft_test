# ubisoft_test

```
python3 -m venv env
env\Scripts\activate.bat
pip install -r requirenments.in
```

# server

```
cd webserver
adev runserver main.py
```

# client

```
cd webclient
python client.py
```


# TODO

1. websokets (task require http: The client-server communication has to be done using HTTP(s) protocol only.)
1.1 pubnup api probably is not allowed to)
2. make smth with timers
2.1 now its possible to have few workers for timer at 1 time
2.1.1 'In case they have already reached the maximum number of tasks started, they have to wait until they are finished to start a new one.'
2.1.2 dummy check only limits to 4 timers, user shouldn't wait until they all finished.
2.2 each tick -> write to redis
2.3 there is no way to stop worker(or add one more call to redis on each tick - read {'player-*:timer-*':'STOP'})
2.4 queue's? not sure it will fit the task - all task should run in parallels(or not...)
3. move_to not limited to board size
4. select user by area is dummy, mongodb $geoIntersects can probably solve it.
5. each cell can be done with redis pubsub:
5.1 register each of 512x512 cell as publishers
5.2 each user subscribes to 32x32 cells
5.3 each user write state to his current cell
6. dummy routes 
7. ways to increase performance: uvloop, ujson, re-check if I used async|await correclty as its new for me.
8. 'The refresh on the client should be as often as possible to keep the synchronization with the server to the
maximum without killing the server processing power/db.' - can be reached #5 + request to check if smth changed or get new state
9. 