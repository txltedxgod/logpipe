import asyncio
import contextlib
import re
from datetime import UTC, datetime
from pathlib import Path

LEVEL_PATTERNS = [
    (re.compile(r'\b(ERROR|ERR)\b', re.IGNORECASE), 'error'),
    (re.compile(r'\b(WARN|WARNING)\b', re.IGNORECASE), 'warning'),
    (re.compile(r'\b(INFO)\b', re.IGNORECASE), 'info'),
    (re.compile(r'\b(DEBUG)\b', re.IGNORECASE), 'debug'),
    (re.compile(r'\b(CRITICAL|FATAL)\b', re.IGNORECASE), 'critical'),
]


def detect_level(line: str) -> str:
    for pattern, level in LEVEL_PATTERNS:
        if pattern.search(line):
            return level
    return 'info'


def build_log_message(source: str, line: str) -> dict[str, str]:
    return {
        'source': source,
        'line': line,
        'level': detect_level(line),
        'ts': datetime.now(UTC).isoformat(),
    }


class LogWatcher:
    def __init__(self, source_config: dict):
        self.name = source_config['name']
        self.path = Path(source_config['path'])
        self.subscribers: set[asyncio.Queue] = set()
        self._task: asyncio.Task | None = None
        self._offset: int | None = None

    async def start(self):
        self._task = asyncio.create_task(self._watch())

    async def stop(self):
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    def subscribe(self, queue: asyncio.Queue):
        self.subscribers.add(queue)

    def unsubscribe(self, queue: asyncio.Queue):
        self.subscribers.discard(queue)

    def _publish(self, line: str) -> None:
        msg = build_log_message(self.name, line)
        dead = set()
        for q in self.subscribers:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                dead.add(q)
        self.subscribers -= dead

    def _read_new_lines(self) -> list[str]:
        if not self.path.exists():
            return []

        size = self.path.stat().st_size
        if self._offset is None:
            self._offset = size
            return []
        if size < self._offset:
            self._offset = 0

        if size == self._offset:
            return []

        with open(self.path, 'rb') as f:
            f.seek(self._offset)
            chunk = f.read()
            self._offset = f.tell()

        text = chunk.decode('utf-8', errors='replace')
        return [line for line in (raw.rstrip('\r\n') for raw in text.splitlines()) if line]

    async def _watch(self):
        """Tail the log file safely (including truncation/rotation) and broadcast lines."""
        while True:
            lines = await asyncio.to_thread(self._read_new_lines)
            for line in lines:
                self._publish(line)
            await asyncio.sleep(0.15)
