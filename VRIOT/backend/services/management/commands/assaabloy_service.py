import codecs
import json
import time
import os

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand

from services.integration.assa_abloy.aa_sdk import AASDK
from services.integration.mqtt.mqtt import MQTTConnector

aa_log = settings.ASSA_ABLOY_LOGGER


class Command(BaseCommand):

    def __init__(self):
        super(Command, self).__init__()
        self.retries = 0

    def handle(self, *args, **options):
        try:
            newpid = os.fork()
            if newpid == 0:
                self.aa_longpoll()
            else:
                self.aa_registration()
        except Exception as e:
            aa_log.critical(str(e), exc_info=True)

    def event_callback(self, topic, message):
        self.message = json.loads(message)
        aa_log.debug(
            "Sending data to Visionline via tunnel {}".format(str(message)))
        try:
            if self.message and isinstance(self.message, dict):
                device_euid = self.message.get("device_euid")
                gateway_euid = self.message.get("gateway_euid")
                attributes = self.message.get("attributes")
                if attributes:
                    for attribute in attributes:
                        data = codecs.encode(codecs.decode(
                            attribute["value"].replace(" ", ""), "hex"),
                            "base64").decode().replace("\n", "")
                        request_data = {
                            "items": [{
                                "data": data,
                                "extId": device_euid
                            }]
                        }
                    (attribute["status"],
                        attribute["resource"]) = AASDK().send_request(
                        "POST", "/tunnel", body=request_data)
                    aa_log.debug(
                        "Received response from Visionline {}"
                        "".format(str(attribute)))
        except Exception as e:
            aa_log.critical(str(e), exc_info=True)

    def aa_registration(self):
        pub_topics = settings.MQTT_SETTINGS["assaabloy"]["pubtopics"]
        sub_topics = settings.MQTT_SETTINGS["assaabloy"]["subtopics"]
        callbacks = {}
        for topics in sub_topics:
            # For each subtopic a callback function to be assigned. Construct
            # dict of topics (pub) and associated call backs (for sub). These
            # can be read from settings or any other mechanism. Depends on the
            # SDK developer.
            if topics[0] == "AA_gateway/device/function/attribute":
                callbacks.update({topics[0]: self.event_callback})

        # Need to register with MQTT API Layer through MQTTConnector object.
        # handle() **options can get the security creds and pass it on to init.
        try:
            self.retries = 0
            with MQTTConnector(
                    mode="assaabloy", pub=pub_topics,
                    sub=sub_topics, cb=callbacks) as mqtt_conn:
                mqtt_conn.receive_loop()
        except Exception as e:
            self.retries += 1
            seconds = 5
            aa_log.critical(
                "Assaabloy Registration service failed."
                "Retrying {}time in {} seconds".format(
                    self.retries, seconds), exc_info=True)
            time.sleep(seconds)
            # Need to stop recursive loop and handle it at calling function.
            self.aa_registration()

    def aa_longpoll(self):
        # This is required to query visionline server for any queued up events.
        try:
            pub_topics = settings.MQTT_SETTINGS["assaabloy"]["pubtopics"]
            self.mqtt_publish = MQTTConnector(mode="assaabloy", pub=pub_topics)
            self.retries = 0
            request_body = {
                "resources": {
                    "tunnel": {}
                }
            }
            is_callback_expired = True
            while True:
                if is_callback_expired:
                    (status, resource) = AASDK().send_request(
                        "POST", "/callback", body=request_body)
                    if 'id' in resource:
                        aa_log.debug(
                            "Call Back registered. Call back ID: {}"
                            "".format(resource["id"]))
                        is_callback_expired = False

                (status1, resource1) = AASDK().send_request(
                    "GET", "/callback/" + resource['id'])
                if not resource1['resources']:
                    (status2, resource2) = AASDK().send_request(
                        "DELETE", "/callback/" + resource['id'])
                    is_callback_expired = True
                    continue
                if 'resources' in resource1:
                    aa_log.debug(
                        "Tunnel Data Received {}".format(str(resource1)))
                    if "tunnel" in resource1["resources"]:
                        for tunnel_data in resource1["resources"]["tunnel"]:
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
                            aa_log.info("Request ID processed ID: {}"
                                        "".format(request_id))
                            self.mqtt_publish.on_sdk_publish(
                                "AA_controller/gateway/device/commands",
                                message)
        except Exception:
            self.retries += 1
            seconds = 5
            cache.delete(settings.AA_CACHE_KEY)
            aa_log.critical("AA Long Poll service failed. Retrying {} time in "
                            "{} seconds".format(self.retries, seconds),
                            exc_info=True)
            time.sleep(seconds)
            # Need to stop recursive loop and handle it at calling function.
            self.aa_longpoll()
