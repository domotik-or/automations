import importlib
import logging
import sys

logger = logging.getLogger()
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter("%(asctime)s %(module)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def _set_loggers_level(config_loggers: dict):
    # set log level of modules logger
    for log in config_loggers:
        module = log["module"]
        level = log["level"]
        try:
            importlib.import_module(module)
        except ModuleNotFoundError:
            logger.warning(f"module {module} not found")
            continue

        if module in logging.Logger.manager.loggerDict.keys():
            logging.getLogger(module).setLevel(level)
        else:
            raise Exception("incorrect type")


def init(loggers: dict):
    _set_loggers_level(loggers)


def close():
    pass
