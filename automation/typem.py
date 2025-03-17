from dataclasses import dataclass


@dataclass
class GeneralConfig:
    pass


@dataclass
class MailConfig:
    fromm: str
    to: str


@dataclass
class MqttConfig:
    host: str
    port: int


@dataclass
class SmtpConfig:
    host: str
    port: int
    username: str
    password: str
