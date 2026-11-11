import copy
from pathlib import Path

import yaml

DEFAULT_CONFIG = {
    'sources': [
        {
            'name': 'app',
            'path': '/var/log/app.log',
            'format': 'auto',
        }
    ],
    'max_lines': 1000,
    'host': '0.0.0.0',
    'port': 8000,
}


def load_config(path: str | Path = 'config.yml') -> dict:
    config_path = Path(path)
    base = copy.deepcopy(DEFAULT_CONFIG)
    if config_path.exists():
        with open(config_path, encoding='utf-8') as f:
            user_config = yaml.safe_load(f) or {}
        if not isinstance(user_config, dict):
            raise ValueError('config YAML root must be a mapping')
        return {**base, **user_config}
    return base
