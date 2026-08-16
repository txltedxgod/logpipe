import yaml
from pathlib import Path

DEFAULT_CONFIG = {
    'sources': [
        {
            'name': 'app',
            'path': '/var/log/app.log',
            'format': 'auto'
        }
    ],
    'max_lines': 1000,
    'host': '0.0.0.0',
    'port': 8000
}


def load_config(path='config.yml'):
    config_path = Path(path)
    if config_path.exists():
        with open(config_path) as f:
            user_config = yaml.safe_load(f) or {}
        # merge with defaults
        merged = {**DEFAULT_CONFIG, **user_config}
        return merged
    return DEFAULT_CONFIG.copy()
