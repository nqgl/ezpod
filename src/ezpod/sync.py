from ezpod.pod import Pod


from patchwork.transfers import rsync
from fabric import Connection


class LocalKwarger:
    def __init__(self, c: Connection, **kwargs):
        self.__c = c
        self.__kwargs = kwargs

    def __getattribute__(self, name: str):
        if name.startswith("_LocalKwarger__"):
            return super().__getattribute__(name)
        if name == "local":
            return lambda x: self.__c.local(x, **self.__kwargs)
        else:
            return self.__c.__getattribute__(name)


def asyncrsync(c, *a, **k):
    c = LocalKwarger(c, asynchronous=True)
    return rsync(c, *a, **k)
