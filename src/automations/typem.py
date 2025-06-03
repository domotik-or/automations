from dataclasses import dataclass


@dataclass
class DomioConfig:
    hostname: str
    port: int


@dataclass
class GeneralConfig:
    dotenv_filename: str


@dataclass
class LinkyConfig:
    apparent_power_alert: int
    check_time: str

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


class SecretConfig:
    pass


@dataclass
class SmtpConfig:
    hostname: str
    port: int
