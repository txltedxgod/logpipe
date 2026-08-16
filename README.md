# logpipe

> Real-time streaming log viewer with WebSocket support, level filtering, and search.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![WebSocket](https://img.shields.io/badge/WebSocket-Realtime-blueviolet?style=flat-square)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

`#log-viewer` `#log-tail` `#websockets` `#fastapi` `#observability` `#devops` `#monitoring`

---

## Features

- **Multi-Source Log Tailing:** Tail multiple log files concurrently from your server.
- **Auto-Detect Log Levels:** Automatically classifies `ERROR`, `WARN`, `INFO`, `DEBUG`, and `CRITICAL`.
- **Real-Time Streaming:** Pushes new log lines to connected browsers instantly via WebSockets.
- **Search & Filter:** Filter logs by origin source, minimum severity level, or substring query.
- **Terminal UI:** Dark terminal-style interface with auto-scroll and line buffering.

## Quick Start

```bash
# 1. Copy config
cp config.example.yml config.yml

# 2. Install & Run
pip install -r requirements.txt
uvicorn server:app --reload
```

Open `http://localhost:8000` in your browser.

## Docker

```bash
docker build -t logpipe .
docker run -v /var/log:/app/logs -p 8000:8000 logpipe
```

## Configuration (`config.yml`)

```yaml
sources:
  - name: app
    path: ./logs/app.log
  - name: nginx
    path: /var/log/nginx/access.log

max_lines: 1000
host: 0.0.0.0
port: 8000
```
