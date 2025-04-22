from dataclasses import dataclass


@dataclass
class DomotikConfig:
    hostname: str
    port: int


@dataclass
class GeneralConfig:
    dotenv_filename: str


@dataclass
class MqttConfig:
    hostname: str
    port: int


@dataclass
class PeriodicityConfig:
    linky: int
    pressure: int


@dataclass
class PostgresqlConfig:
    hostname: str
    port: int
    username: str
    databasename: str


class SecretsConfig:
    pass


@dataclass
class SmtpConfig:
    hostname: str
    port: int
