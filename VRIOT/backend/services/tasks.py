import random

from django.conf import settings
from paho.mqtt import publish

from services.integration.celery.celery import async_worker
from services.integration.mqtt.subscribe_function import MQTTSubscribeFunction

vriot_log = settings.VRIOT_LOGGER


@async_worker.task(ignore_result=True, queue="mqtt_normal")
def async_mqtt_subscribe(topic, message):
    try:
        MQTTSubscribeFunction(topic=topic, message=message)
    except Exception:
        vriot_log.critical("Subscriber Async Failed", exc_info=True)


@async_worker.task(ignore_result=True, queue="mqtt_priority")
def async_mqtt_publish(payload):
    try:
        host = settings.MQTT_SETTINGS[settings.ENVIRONMENT]["host"]
        port = settings.MQTT_SETTINGS[settings.ENVIRONMENT]["port"]
        client = "vriot_mqtt_publish/" + "".join(random.choice(
            "0123456789ADCDEF") for _ in range(23 - 5))
        if isinstance(payload, dict):
            payload = [payload]
        if isinstance(payload, list):
            publish.multiple(payload[::-1], hostname=host, port=port,
                             keepalive=60, client_id=client)
    except Exception:
        vriot_log.critical("Publisher Async Failed", exc_info=True)
