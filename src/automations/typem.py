from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    path: str


@dataclass
class DomioConfig:
    hostname: str
    port: int


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
    outdoor: int
    pressure: int


class SecretConfig:
    pass


@dataclass
class SmtpConfig:
    hostname: str
    port: int
