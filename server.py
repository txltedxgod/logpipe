from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from config import load_config
from watcher import LogWatcher
from contextlib import asynccontextmanager
import asyncio
import json

config = load_config()
watchers: list[LogWatcher] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    # start all watchers
    for src in config['sources']:
        w = LogWatcher(src)
        watchers.append(w)
        await w.start()
    yield
    for w in watchers:
        await w.stop()

app = FastAPI(title='logpipe', lifespan=lifespan)
app.mount('/static', StaticFiles(directory='static'), name='static')


@app.get('/')
async def index():
    return FileResponse('static/index.html')


@app.get('/api/sources')
async def get_sources():
    return [{'name': w.name, 'path': str(w.path)} for w in watchers]


@app.websocket('/ws/logs')
async def log_stream(ws: WebSocket):
    await ws.accept()
    queue = asyncio.Queue(maxsize=500)

    # subscribe to all watchers
    for w in watchers:
        w.subscribe(queue)

    try:
        while True:
            msg = await queue.get()
            await ws.send_text(json.dumps(msg))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        for w in watchers:
            w.unsubscribe(queue)
