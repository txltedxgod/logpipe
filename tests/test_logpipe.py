import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from config import DEFAULT_CONFIG, load_config
from server import create_app
from watcher import LogWatcher, detect_level


def _append_bytes(path: Path, data: bytes) -> None:
    with open(path, 'ab') as f:
        f.write(data)
        f.flush()


def test_detect_level_and_config_loading(tmp_path):
    assert detect_level('2026-11-11 ERROR database timeout') == 'error'
    assert detect_level('warn: disk at 85%') == 'warning'
    assert detect_level('FATAL panic') == 'critical'
    assert detect_level('started server') == 'info'

    missing_cfg = load_config(tmp_path / 'missing.yml')
    missing_cfg['sources'].append({'name': 'extra', 'path': '/tmp/x.log'})
    assert len(DEFAULT_CONFIG['sources']) == 1

    cfg_path = tmp_path / 'config.yml'
    cfg_path.write_text("port: 9001\nsources:\n  - name: api\n    path: ./api.log\n", encoding='utf-8')
    loaded = load_config(cfg_path)
    assert loaded['port'] == 9001
    assert loaded['sources'][0]['name'] == 'api'


@pytest.mark.asyncio
async def test_log_watcher_handles_append_invalid_utf8_and_truncation(tmp_path):
    log_file = tmp_path / 'app.log'
    log_file.write_text('initial\n', encoding='utf-8')

    watcher = LogWatcher({'name': 'app', 'path': str(log_file)})
    q: asyncio.Queue = asyncio.Queue()
    watcher.subscribe(q)
    await watcher.start()
    try:
        await asyncio.sleep(0.2)
        _append_bytes(log_file, b'INFO boot\xffbad\n')
        msg1 = await asyncio.wait_for(q.get(), timeout=2.0)
        assert msg1['level'] == 'info'
        assert 'INFO boot' in msg1['line']

        # Simulate log truncation/rotation
        log_file.write_text('', encoding='utf-8')
        await asyncio.sleep(0.25)
        _append_bytes(log_file, b'ERROR rotated line\n')
        msg2 = await asyncio.wait_for(q.get(), timeout=2.0)
        assert msg2['level'] == 'error'
        assert msg2['line'] == 'ERROR rotated line'
    finally:
        await watcher.stop()


def test_server_http_routes_and_websocket_stream(tmp_path):
    log_file = tmp_path / 'srv.log'
    log_file.write_text('', encoding='utf-8')

    app = create_app({'sources': [{'name': 'srv', 'path': str(log_file)}]})
    with TestClient(app) as client:
        assert client.get('/health').json() == {'status': 'ok'}
        assert client.get('/').status_code == 200
        assert client.get('/api/sources').json() == [{'name': 'srv', 'path': str(log_file)}]

        with client.websocket_connect('/ws/logs') as ws:
            _append_bytes(log_file, b'WARN high latency\n')
            payload = ws.receive_json()
            assert payload['source'] == 'srv'
            assert payload['level'] == 'warning'
            assert payload['line'] == 'WARN high latency'
