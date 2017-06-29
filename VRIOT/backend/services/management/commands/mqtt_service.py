import time

from django.conf import settings
from django.core.management.base import BaseCommand

from services.integration.mqtt.mqtt import MQTTClient

mqtt_log = settings.MQTT_LOGGER


class Command(BaseCommand):
    def __init__(self):
        super(Command, self).__init__()
        self.retries = 0

    def handle(self, *args, **options):
        try:
            self.retries = 0
            with MQTTClient() as mqtt_client:
                mqtt_client.receive_loop()
        except Exception:
            self.retries += 1
            seconds = 5
            mqtt_log.critical("MQTT Subscribe service failed. Retrying {} time "
                              "in {} seconds".format(self.retries, seconds),
                              exc_info=True)
            time.sleep(seconds)
            self.handle()
