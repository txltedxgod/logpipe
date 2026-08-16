import asyncio
import re
from pathlib import Path
from datetime import datetime

# common log level patterns
LEVEL_PATTERNS = [
    (re.compile(r'\b(ERROR|ERR)\b', re.I), 'error'),
    (re.compile(r'\b(WARN|WARNING)\b', re.I), 'warning'),
    (re.compile(r'\b(INFO)\b', re.I), 'info'),
    (re.compile(r'\b(DEBUG)\b', re.I), 'debug'),
    (re.compile(r'\b(CRITICAL|FATAL)\b', re.I), 'critical'),
]


def detect_level(line: str) -> str:
    for pattern, level in LEVEL_PATTERNS:
        if pattern.search(line):
            return level
    return 'info'


class LogWatcher:
    def __init__(self, source_config: dict):
        self.name = source_config['name']
        self.path = Path(source_config['path'])
        self.subscribers = set()
        self._task = None

    async def start(self):
        self._task = asyncio.create_task(self._watch())

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def subscribe(self, queue: asyncio.Queue):
        self.subscribers.add(queue)

    def unsubscribe(self, queue: asyncio.Queue):
        self.subscribers.discard(queue)

    async def _watch(self):
        """Tail the log file and push new lines to all subscribers."""
        # wait for file to exist
        while not self.path.exists():
            await asyncio.sleep(2)

        with open(self.path, 'r') as f:
            # seek to end
            f.seek(0, 2)

            while True:
                line = f.readline()
                if line:
                    line = line.rstrip('\n')
                    if not line:
                        continue

                    msg = {
                        'source': self.name,
                        'line': line,
                        'level': detect_level(line),
                        'ts': datetime.utcnow().isoformat()
                    }
                    dead = set()
                    for q in self.subscribers:
                        try:
                            q.put_nowait(msg)
                        except asyncio.QueueFull:
                            dead.add(q)
                    self.subscribers -= dead
                else:
                    await asyncio.sleep(0.3)
