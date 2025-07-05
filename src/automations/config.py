from os import getenv
from pathlib import Path
import sys
import tomllib

from dotenv import load_dotenv

from automations.typem import DatabaseConfig
from automations.typem import DomioConfig
from automations.typem import LinkyConfig
from automations.typem import MqttConfig
from automations.typem import PeriodicityConfig
from automations.typem import SecretConfig
from automations.typem import SmtpConfig

database = None
domio = None
linky = None
loggers = {}
mqtt = None
periodicity = None
secret = None
smtp = None


def read(config_filename: str):
    config_file = Path(config_filename).expanduser()

    with open(config_file, "rb") as f:
        raw_config = tomllib.load(f)

    global database
    database = DatabaseConfig(**raw_config["database"])

    global domio
    domio = DomioConfig(**raw_config["domio"])

    global linky
    linky = LinkyConfig(**raw_config["linky"])

    global loggers
    loggers = raw_config["logger"]

    global mqtt
    mqtt = MqttConfig(**raw_config["mqtt"])

    global periodicity
    periodicity = PeriodicityConfig(**raw_config["periodicity"])

    global smtp
    smtp = SmtpConfig(**raw_config["smtp"])

    # store secrets data in config class
    global secret
    load_dotenv(raw_config["secret"]["env_path"])
    secret = SecretConfig()
    for v in raw_config["secret"]["env_names"]:
        value = getenv(v)
        if value is None:
            # not logging system configured yet!
            sys.stderr.write(f"Missing environment variables {v}\n")
        setattr(secret, v.lower(), value)


if __name__ == "__main__":
    read("config.toml")
