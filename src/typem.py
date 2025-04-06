from dataclasses import dataclass


@dataclass
class DomotikConfig:
    hostname: str
    port: int


@dataclass
class GeneralConfig:
    pass


@dataclass
class LoggerConfig:
    level: int


@dataclass
class MqttConfig:
    hostname: str
    port: int


@dataclass
class PostgresqlConfig:
    hostname: str
    port: int
    username: str
    databasename: str


class SecretDataConfig:
    pass


@dataclass
class SmtpConfig:
    hostname: str
    port: int
