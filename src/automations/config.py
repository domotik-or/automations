import logging
from os import getenv
from pathlib import Path
import sys
import tomllib

from dotenv import load_dotenv

from automations.typem import DomotikConfig
from automations.typem import GeneralConfig
from automations.typem import MqttConfig
from automations.typem import PeriodicityConfig
from automations.typem import PostgresqlConfig
from automations.typem import SecretDataConfig
from automations.typem import SmtpConfig

domotik = None
general = None
loggers = {}
mqtt = None
periodicity = None
postgresql = None
secret_data = None
smtp = None


def read(config_filename: str):
    config_file = Path(config_filename).expanduser()

    with open(config_file, "rb") as f:
        raw_config = tomllib.load(f)

    global general
    general = GeneralConfig(**raw_config["general"])

    global domotik
    domotik = DomotikConfig(**raw_config["domotik"])

    global loggers
    loggers = raw_config["logger"]

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
    load_dotenv(general.dotenv_filename)
    secret_data = SecretDataConfig()
    for v in (
        "MAIL_FROM", "MAIL_TO", "PGPASSWORD", "SMTP_USERNAME", "SMTP_PASSWORD"
    ):
        value = getenv(v)
        if value is None:
            sys.stderr.write(f"Missing environment variable {v}\n")
            sys.exit(1)
        setattr(secret_data, v.lower(), value)
