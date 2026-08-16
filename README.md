# logpipe

Lightweight real-time log viewer. Tail multiple log files from your server, filter by level, search — all in a terminal-style web UI.

## How it works

1. Configure log file paths in `config.yml`
2. logpipe tails each file and streams new lines via WebSocket
3. The browser UI receives lines in real-time, parses log levels, and lets you filter/search

## Quick start

```bash
# copy and edit config
cp config.example.yml config.yml

# run
pip install -r requirements.txt
uvicorn server:app --reload
```

Open http://localhost:8000

## Config

```yaml
sources:
  - name: app
    path: ./logs/app.log
  - name: nginx
    path: /var/log/nginx/access.log

max_lines: 1000
```

## Features

- Multi-source log tailing
- Auto-detect log levels (ERROR, WARN, INFO, DEBUG, CRITICAL)
- Real-time WebSocket streaming
- Filter by source and level
- Full-text search
- Auto-scroll toggle
- Terminal-style dark UI

## Docker

```bash
docker build -t logpipe .
docker run -v /var/log:/app/logs -p 8000:8000 logpipe
```

## Stack

- FastAPI + WebSocket
- asyncio file tailing
- Vanilla JS
