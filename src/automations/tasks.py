import asyncio
from datetime import date
from datetime import datetime
from datetime import timedelta
from functools import partial
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
from automations.utils import done_callback

_check_time = None
_running = False
_task_linky = None
_task_mqtt = None
_task_pressure = None

# logger initial setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def init():
    global _check_time
    global _task_linky
    global _task_mqtt
    global _task_pressure
    global _running

    _running = True

    if _task_linky  is None:
        _task_linky = asyncio.create_task(_linky_task())
        _task_linky.add_done_callback(partial(done_callback, logger))

    if _task_mqtt  is None:
        _task_mqtt = asyncio.create_task(_mqtt_task())
        _task_mqtt.add_done_callback(partial(done_callback, logger))

    if _task_pressure  is None:
        _task_pressure = asyncio.create_task(_pressure_task())
        _task_pressure.add_done_callback(partial(done_callback, logger))

    _check_time = datetime.strptime(config.linky.check_time, "%H:%M").time()


async def _send_email(subject: str, content: str):
    message = EmailMessage()
    message["From"] = config.secret.mail_from,
    message["To"] = config.secret.mail_to
    message["Subject"] = subject
    message.set_content(content)
    try:
        await aiosmtplib.send(
            message,
            hostname=config.smtp.hostname,
            port=config.smtp.port,
            username=config.secret.smtp_username,
            password=config.secret.smtp_password
        )
    except Exception as exc:
        logger.error(f"{exc}")


async def _mqtt_task():
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
                    if message.payload is None:
                        continue

                    payload = json.loads(message.payload.decode())
                    device = message.topic.value.split('/')[-1]

                    # store values in db
                    try:
                        await execute_query(
                            "INSERT INTO sonoff_snzb02p VALUES (?, ?, ?)",
                            device, payload["humidity"], payload["temperature"]
                        )

                        if payload["battery"] < 50:
                            logger.warning(f"{message.topic.value}: battery low")
                    except KeyError as exc:
                        logger.error(f"incomplete data: missing {exc} key")
                elif message.topic.matches("home/doorbell/pressed"):
                    await client.publish(
                        "home/doorbell/ring",
                        payload=json.dumps({"number": 5})
                    )
                    await _send_email("Ding dong !", "On sonne à la porte")

                    # store event in db
                    await execute_query(
                        "INSERT INTO on_off VALUES (?, ?)", "doorbell", True
                    )

        except (asyncio.CancelledError, KeyboardInterrupt):
            pass

    logger.debug("mqtt task stopped")


async def _linky_task():
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
                                "INSERT INTO linky VALUES (?, ?)",
                                data["east"], sinst
                            )

                            # check apparent power
                            check_datetime = datetime.combine(date.today(), _check_time)
                            if abs(datetime.now() - check_datetime) < timedelta(minutes=1):
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


async def _pressure_task():
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
                                "INSERT INTO pressure VALUES (?)", pressure
                            )
                        else:
                            logger.debug(f"bad status ({resp.status}) when getting pressure")

            await asyncio.sleep(1)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass

    logger.debug("pressure task stopped")


async def close():
    global _running
    global _task_linky
    global _task_mqtt
    global _task_pressure

    _running = False

    if _task_linky is not None:
        try:
            await _task_linky
        except Exception:
            # task exceptions are handled by the done callback
            pass
        _task_linky = None

    if _task_mqtt is not None:
        try:
            _task_mqtt.cancel()
            await _task_mqtt
        except Exception:
            # task exceptions are handled by the done callback
            pass
        _task_mqtt = None

    if _task_pressure is not None:
        try:
            await _task_pressure
        except Exception:
            # task exceptions are handled by the done callback
            pass
        _task_pressure = None
