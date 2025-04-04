import asyncio
import json
import logging

import aiohttp
import aiomqtt

import config

_running = False
_task_handle_doorbell = None
_task_handle_linky = None
_task_handle_mqtt = None
_task_handle_pressure = None

# logger initial setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def init():
    global _running
    global _task_handle_doorbell
    global _task_handle_pressure

    _running = True
    _task_handle_doorbell = asyncio.create_task(_task_doorbell())
    _task_handle_linky = asyncio.create_task(_task_linky())
    _task_handle_mqtt = asyncio.create_task(_task_mqtt())
    _task_handle_pressure = asyncio.create_task(_task_pressure())


async def _task_doorbell():
    logger.debug("doorbell task started")

    try:
        async with aiomqtt.Client(config.mqtt.hostname, config.mqtt.port) as client:
            await client.subscribe("home/doorbell/button")
            async for message in client.messages:
                if message.payload.decode() == "pressed":
                    await client.publish("home/doorbell/bell")

                    message = EmailMessage()
                    message["From"] = config.secrets.mail_from,
                    message["To"] = config.secrets.mail_to
                    message["Subject"] = "Ding dong !"
                    message.set_content("On sonne à la porte")
                    try:
                        await aiosmtplib.send(
                            message,
                            hostname=config.smtp.host,
                            port=config.smtp.port,
                            username=config.secrets.smtp_username,
                            password=config.secrets.smtp_password
                        )
                    except Exception as exc:
                        logger.error(f"{exc}")
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass

    logger.debug("doorbell task stopped")


async def _task_mqtt():
    logger.debug("mqtt task started")

    try:
        async with aiomqtt.Client(config.mqtt.hostname, config.mqtt.port) as client:
            await client.subscribe("zigbee2mqtt/#")
            async for message in client.messages:
                if message.topic.value in ["zigbee2mqtt/sonoff_sejour", "zigbee2mqtt/sonoff_chambre_haut"]:
                    payload = json.loads(message.payload.decode())
                    print(f"payload: {payload}")
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
    global _task_handle_doorbell
    global _task_handle_linky
    global _task_handle_mqtt
    global _task_handle_pressure

    _running = False

    if _task_handle_doorbell is not None:
        try:
            _task_handle_doorbell.cancel()
            await _task_handle_doorbell
        except asyncio.CancelledError:
            pass
        _task_handle_doorbell = None

    if _task_handle_linky is not None:
        await _task_handle_linky
        _task_handle_linky = None

    if _task_handle_mqtt is not None:
        await _task_handle_mqtt
        _task_handle_mqtt = None

    if _task_handle_pressure is not None:
        await _task_handle_pressure
        _task_handle_pressure = None
