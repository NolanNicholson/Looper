import json
import os.path as osp


DEFAULT_CONFIG_FILE = osp.abspath(osp.join(osp.dirname(__file__), 'config.json'))


class LooperConfig(object):
    __settings__ = {
        'backend': 'mpg123',
    }

    def __init__(self, **kwargs):
        self.update(**kwargs)

    @classmethod
    def load(cls, fn=DEFAULT_CONFIG_FILE, fallback=True):
        if not osp.exists(fn) and fallback:
            return cls()

        with open(fn, 'r') as f:
            content = json.load(f)
        return cls(**content)

    def save(self, fn=DEFAULT_CONFIG_FILE):
        content = {k: getattr(self, k) for k in self.__settings__}
        with open(fn, 'w') as f:
            json.dump(content, f, indent=2)

    def update(self, **kwargs):
        for k, v in self.__settings__.items():
            setattr(self, k, kwargs.get(k, v))

    def __str__(self):
        return str({k: getattr(self, k) for k in self.__settings__})
