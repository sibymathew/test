import codecs
import json
import time

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand

from services.integration.assa_abloy.aa_sdk import AASDK
from services.tasks import async_mqtt_publish

aa_log = settings.ASSA_ABLOY_LOGGER


class Command(BaseCommand):
    def __init__(self):
        super(Command, self).__init__()
        self.retries = 0

    def handle(self, *args, **options):
        try:
            aa_topic = "AA_controller/gateway/device/commands"
            request_body = {
                "resources": {
                    "tunnel": {}
                }
            }
            while True:
                (status, resource) = AASDK().send_request(
                    "POST", "/callback", body=request_body)
                if 'id' in resource:
                    aa_log.debug(
                        "Call Back registered. Call back ID: {}".format(
                            resource["id"]))
                    self.retries = 0
                    (status1, resource1) = AASDK().send_request(
                        "GET", "/callback/" + resource['id'])
                    if 'resources' in resource1:
                        aa_log.debug(resource1)
                        # resetting timer
                        # send data on the mqtt channel
                        if "tunnel" in resource1["resources"]:
                            aa_log.debug(
                                "Tunnel Data Received {}".format(str(
                                    resource1["resources"]["tunnel"])))
                            for tunnel_data in resource1["resources"][
                                "tunnel"]:
                                device_euid = tunnel_data["extId"]
                                device_value = tunnel_data["data"]
                                request_id = tunnel_data["reqId"]
                                hex_value = codecs.decode(
                                    codecs.encode(device_value),
                                    "base64").hex()
                                message = {
                                    "device_euid": device_euid,
                                    "commands": [{
                                        "command": "AA_TUNNEL_DATA",
                                        "value": hex_value
                                    }]
                                }
                                payload = {
                                    "topic": aa_topic,
                                    "payload": json.dumps(message)
                                }
                                aa_log.info("Request ID processed ID: {}"
                                            "".format(request_id))
                                aa_log.debug("Sending MQTT to gateways "
                                             "with payload: {}".format(
                                    str(message)))
                                async_mqtt_publish.apply_async((payload,))
        except Exception:
            self.retries += 1
            seconds = 5
            cache.delete(settings.AA_CACHE_KEY)
            aa_log.critical("AA Long Poll service failed. Retrying {} time in "
                            "{} seconds".format(self.retries, seconds),
                            exc_info=True)
            time.sleep(seconds)
            self.handle()
