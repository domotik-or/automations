import asyncio
from time import perf_counter
import json
import logging

import aiohttp
import aiomqtt
import aiosmtplib
from email.message import EmailMessage
from paho.mqtt.subscribeoptions import SubscribeOptions

import config
from db import execute_query

_running = False
_linky_task = None
_mqtt_task = None
_pressure_task = None

# logger initial setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def init():
    global _linky_task
    global _mqtt_task
    global _pressure_task
    global _running

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

    async with aiomqtt.Client(
        config.mqtt.hostname, config.mqtt.port, protocol=aiomqtt.ProtocolVersion.V5
    ) as client:
        options = SubscribeOptions(qos=1, noLocal=True)
        await client.subscribe("home/#", options=options)
        await client.subscribe("zigbee2mqtt/sensor/#")
        try:
            async for message in client.messages:
                logger.debug(
                    f"mqtt message, topic: {message.topic.value}, "
                    f"payload: {message.payload}"
                )
                if message.topic.matches("zigbee2mqtt/sensor/sonoff/snzb02p/#"):
                    payload = json.loads(message.payload.decode())
                    device = message.topic.value.split('/')[-1]

                    # store values in db
                    await execute_query(
                        "INSERT INTO sonoff_snzb02p VALUES ($1, $2, $3)",
                        device, payload["humidity"], payload["temperature"]
                    )

                    if payload["battery"] < 50:
                        logger.warning(f"{message.topic.value}: battery low")
                elif message.topic.matches("home/doorbell/pressed"):
                    await client.publish("home/doorbell/ring")
                    await send_email("Ding dong !", "On sonne à la porte")

                    # store event in db
                    await execute_query(
                        "INSERT INTO on_off VALUES ($1, $2)", "doorbell", True
                    )

        except (asyncio.CancelledError, KeyboardInterrupt):
            pass

    logger.debug("mqtt task stopped")


async def _task_linky():
    logger.debug("linky task started")

    start_time = perf_counter()
    try:
        while _running:
            if perf_counter() - start_time >= config.periodicity.linky:
                start_time = perf_counter()

                async with aiohttp.ClientSession() as session:
                    url = f"http://{config.domotik.hostname}:{config.domotik.port}/linky"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            json = await resp.json()

                            # store values in db
                            await execute_query(
                                "INSERT INTO linky VALUES ($1, $2)",
                                json["data"]["east"], json["data"]["sinsts"]
                            )
                        else:
                            logger.debug(f"bad status ({resp.status}) when getting linky")

            await asyncio.sleep(1)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass

    logger.debug("pressure task stopped")


async def _task_pressure():
    logger.debug("pressure task started")

    start_time = perf_counter()
    try:
        while _running:
            if perf_counter() - start_time >= config.periodicity.pressure:
                start_time = perf_counter()

                async with aiohttp.ClientSession() as session:
                    url = f"http://{config.domotik.hostname}:{config.domotik.port}/pressure"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            json = await resp.json()
                            pressure = json["data"]["pressure"]
                            pressure /= 100.0  # convert to hPa

                            # store values in db
                            await execute_query(
                                "INSERT INTO pressure VALUES ($1)", pressure
                            )
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
