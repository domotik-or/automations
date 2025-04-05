import asyncio
import json
import logging

import aiohttp
import aiomqtt
import aiosmtplib
from email.message import EmailMessage

import config

_running = False
_linky_task = None
_mqtt_task = None
_pressure_task = None

# logger initial setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def init():
    global _running
    global _pressure_task

    _running = True
    _linky_task = asyncio.create_task(_task_linky())
    _mqtt_task = asyncio.create_task(_task_mqtt())
    _pressure_task = asyncio.create_task(_task_pressure())


async def send_email(subject: str, content: str):
    message = EmailMessage()
    message["From"] = config.secret_data.mail_from,
    message["To"] = config.secret_data.mail_to
    message["Subject"] = subject
    message.set_content(content)
    try:
        await aiosmtplib.send(
            message,
            hostname=config.smtp.hostname,
            port=config.smtp.port,
            username=config.secret_data.smtp_username,
            password=config.secret_data.smtp_password
        )
    except Exception as exc:
        logger.error(f"{exc}")


async def _task_mqtt():
    logger.debug("mqtt task started")

    async with aiomqtt.Client(config.mqtt.hostname, config.mqtt.port) as client:
        await client.subscribe("home/#")
        await client.subscribe("zigbee2mqtt/sensor/#")
        try:
            async for message in client.messages:
                # logger.debug(
                #     f"mqtt message, topic: {message.topic.value}, "
                #     f"payload: {message.payload}"
                # )
                if message.topic.matches("zigbee2mqtt/sensor/sonoff/snzb-02p/#"):
                    payload = json.loads(message.payload.decode())
                    location = message.topic.value.split('/')[-1]
                    logger.debug(f"location: {location}, payload: {payload}")
                    if payload["battery"] < 50:
                        logger.warning(f"{message.topic.value}: battery low")
                elif message.topic.matches("home/doorbell/pressed"):
                    await client.publish("home/doorbell/ring")
                    await send_email("Ding dong !", "On sonne à la porte")
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass

    logger.debug("mqtt task stopped")


async def _task_linky():
    logger.debug("linky task started")

    count = 0
    try:
        while _running:
            count += 1
            if count == 15:
                count = 0

                async with aiohttp.ClientSession() as session:
                    url = f"http://{config.domotik.hostname}:{config.domotik.port}/linky"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            json = await resp.json()
                            east = json["data"]["east"]
                            logger.debug(f"east: {east}")
                        else:
                            logger.debug(f"bad status ({resp.status}) when getting linky")

            await asyncio.sleep(1)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass

    logger.debug("pressure task stopped")


async def _task_pressure():
    logger.debug("pressure task started")

    count = 0
    try:
        while _running:
            count += 1
            if count == 60:
                count = 0

                async with aiohttp.ClientSession() as session:
                    url = f"http://{config.domotik.hostname}:{config.domotik.port}/pressure"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            json = await resp.json()
                            pressure = json["data"]["pressure"]
                            pressure /= 100.0
                            logger.debug(f"pressure: {pressure:.2f}")
                        else:
                            logger.debug(f"bad status ({resp.status}) when getting pressure")

            await asyncio.sleep(1)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass

    logger.debug("pressure task stopped")


async def close():
    global _running
    global _linky_task
    global _mqtt_task
    global _pressure_task

    _running = False

    if _linky_task is not None:
        await _linky_task
        _linky_task = None

    if _mqtt_task is not None:
        try:
            _mqtt_task.cancel()
            await _mqtt_task
        except asyncio.CancelledError:
            pass
        _mqtt_task = None

    if _pressure_task is not None:
        await _pressure_task
        _pressure_task = None
