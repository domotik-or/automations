from dataclasses import dataclass


@dataclass
class GeneralConfig:
    pass


@dataclass
class MqttConfig:
    host: str
    port: int


@dataclass
class SmtpConfig:
    host: str
    port: int
