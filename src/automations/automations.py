import asyncio
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from time import perf_counter
import json
import logging

import aiohttp
import aiomqtt
import aiosmtplib
from email.message import EmailMessage
from paho.mqtt.subscribeoptions import SubscribeOptions

import automations.config as config
from automations.db import execute_query

_check_time = None
_running = False
_linky_task = None
_mqtt_task = None
_pressure_task = None

# logger initial setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def init():
    global _check_time
    global _linky_task
    global _mqtt_task
    global _pressure_task
    global _running

    _running = True
    _linky_task = asyncio.create_task(_task_linky())
    _mqtt_task = asyncio.create_task(_task_mqtt())
    _pressure_task = asyncio.create_task(_task_pressure())

    _check_time = datetime.strptime(config.linky.check_time, "%H:%M").time()


async def _send_email(subject: str, content: str):
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
                    await client.publish(
                        "home/doorbell/ring",
                        payload=json.dumps({"number": 5})
                    )
                    await _send_email("Ding dong !", "On sonne à la porte")

                    # store event in db
                    await execute_query(
                        "INSERT INTO on_off VALUES ($1, $2)", "doorbell", True
                    )

        except (asyncio.CancelledError, KeyboardInterrupt):
            pass

    logger.debug("mqtt task stopped")


async def _task_linky():
    logger.debug("linky task started")

    power_alert = False

    start_time = perf_counter()
    try:
        while _running:
            if perf_counter() - start_time >= config.periodicity.linky:
                start_time = perf_counter()

                async with aiohttp.ClientSession() as session:
                    url = f"http://{config.domio.hostname}:{config.domio.port}/linky"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = (await resp.json())["data"]
                            sinst = data["sinsts"]

                            # store values in db
                            await execute_query(
                                "INSERT INTO linky VALUES ($1, $2)",
                                data["east"], sinst
                            )

                            # check apparent power
                            check_datetime = datetime.combine(date.today(), _check_time)
                            if abs(datetime.now() - check_datetime)  < timedelta(minutes=1):
                                if sinst > config.linky.apparent_power_alert:
                                    if not power_alert:
                                        logger.warning("apparent power alert!")

                                        # ring the bell once
                                        async with aiomqtt.Client(
                                            config.mqtt.hostname, config.mqtt.port,
                                            protocol=aiomqtt.ProtocolVersion.V5
                                        ) as client:
                                            await client.publish(
                                                "home/doorbell/ring",
                                                payload=json.dumps({"number": 1})
                                            )

                                        # and send an email
                                        await _send_email(
                                            "Alerte consommation !",
                                            "Consommation électrique inhabituelle"
                                        )

                                        power_alert = True
                                else:
                                    power_alert = False
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
                    url = f"http://{config.domio.hostname}:{config.domio.port}/pressure"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = (await resp.json())["data"]
                            pressure = data["pressure"]
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
