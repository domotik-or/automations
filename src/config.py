import logging
from pathlib import Path
import tomllib

from src.typem import GeneralConfig
from src.typem import LoggerConfig
from src.typem import MqttConfig
from src.typem import SmtpConfig

loggers = {}

general = None
mqtt = None
smtp = None

_module = []


def read(config_filename: str):
    config_file = Path(config_filename)
    with open(config_file, "rb") as f:
        raw_config = tomllib.load(f)

    global general
    general = GeneralConfig(**raw_config["general"])

    global loggers
    for lg in raw_config["logger"]:
        level_str = raw_config["logger"][lg]["level"]
        level = getattr(logging, level_str)
        loggers[lg] = LoggerConfig(level)


    global mqtt
    mqtt = MqttConfig(**raw_config["mqtt"])

    global smtp
    smtp = SmtpConfig(**raw_config["smtp"])
