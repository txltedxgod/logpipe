import asyncio
import json
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import load_config
from watcher import LogWatcher

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / 'static'


def create_app(cfg: dict | None = None) -> FastAPI:
    app_config = cfg if cfg is not None else load_config(BASE_DIR / 'config.yml')
    app_watchers: list[LogWatcher] = []

    @asynccontextmanager
    async def lifespan(fastapi_app: FastAPI):
        app_watchers.clear()
        for src in app_config.get('sources', []):
            w = LogWatcher(src)
            app_watchers.append(w)
            await w.start()
        yield
        for w in app_watchers:
            await w.stop()

    fastapi_app = FastAPI(title='logpipe', lifespan=lifespan)
    if STATIC_DIR.is_dir():
        fastapi_app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')

    @fastapi_app.get('/', include_in_schema=False)
    async def index():
        return FileResponse(STATIC_DIR / 'index.html')

    @fastapi_app.get('/health')
    async def health():
        return {'status': 'ok'}

    @fastapi_app.get('/api/sources')
    async def get_sources():
        return [{'name': w.name, 'path': str(w.path)} for w in app_watchers]

    @fastapi_app.websocket('/ws/logs')
    async def log_stream(ws: WebSocket):
        await ws.accept()
        queue: asyncio.Queue = asyncio.Queue(maxsize=500)

        for w in app_watchers:
            w.subscribe(queue)

        try:
            while True:
                msg = await queue.get()
                await ws.send_text(json.dumps(msg))
        except WebSocketDisconnect:
            pass
        finally:
            for w in app_watchers:
                w.unsubscribe(queue)
            with suppress(Exception):
                await ws.close()

    return fastapi_app


app = create_app()
