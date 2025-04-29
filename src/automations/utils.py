import asyncio
import dataclasses
import json


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


async def exec_cmd(cmd: str) -> tuple[int | None, str, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode(), stderr.decode()


class ValueFilter:
    def __init__(self, size: int):
        self.__size = size
        self.__list = []  # type: ignore[var-annotated]
        self.__mean = 0

    @property
    def size(self):
        return self.__size

    @property
    def value(self):
        return self.__mean

    @value.setter
    def value(self, v):
        self.__list.insert(0, v)
        if len(self.__list) > self.__size:
            self.__list.pop(-1)
        self.__mean = sum(self.__list) / len(self.__list)


def done_callback(logger, task):
    """This function enable logging exceptions in tasks. It must be overloaded
    as a partial function where the logger is imposed"""
    exc = task.exception()
    if exc is not None and not isinstance(exc, asyncio.exceptions.CancelledError):
        exc_info = (type(exc), exc, exc.__traceback__)
        logger.error(exc, exc_info=exc_info)
