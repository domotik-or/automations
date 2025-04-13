import logging
from os import getenv
from pathlib import Path
import sys
import tomllib

from dotenv import load_dotenv

from typem import DomotikConfig
from typem import GeneralConfig
from typem import LoggerConfig
from typem import MqttConfig
from typem import PeriodicityConfig
from typem import PostgresqlConfig
from typem import SecretDataConfig
from typem import SmtpConfig


domotik = None
general = None
loggers = {}
mqtt = None
periodicity = None
postgresql = None
secret_data = None
smtp = None


class Secrets:
    pass


def read(config_filename: str):
    config_file = Path(config_filename)
    with open(config_file, "rb") as f:
        raw_config = tomllib.load(f)

    global general
    general = GeneralConfig(**raw_config["general"])

    global loggers
    for lg in raw_config["logger"]:
        level_str = raw_config["logger"][lg]
        level = getattr(logging, level_str)
        loggers[lg] = LoggerConfig(level)

    global domotik
    domotik = DomotikConfig(**raw_config["domotik"])

    global mqtt
    mqtt = MqttConfig(**raw_config["mqtt"])

    global periodicity
    periodicity = PeriodicityConfig(**raw_config["periodicity"])

    global postgresql
    postgresql = PostgresqlConfig(**raw_config["postgresql"])

    global smtp
    smtp = SmtpConfig(**raw_config["smtp"])

    # store secrets in memory
    global secret_data
    load_dotenv()
    secret_data = SecretDataConfig()
    for v in (
        "MAIL_FROM", "MAIL_TO", "PGPASSWORD", "SMTP_USERNAME", "SMTP_PASSWORD"
    ):
        value = getenv(v)
        if value is None:
            sys.stderr.write(f"Missing environment variable {v}\n")
            sys.exit(1)
        setattr(secret_data, v.lower(), value)
