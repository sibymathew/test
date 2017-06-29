import random
import json

import paho.mqtt.client as mqtt
from django.conf import settings

from services.tasks import async_mqtt_publish
from services.tasks import async_mqtt_subscribe

mqtt_log = settings.MQTT_LOGGER


class MQTTConnector(object):
    # For backward compatibility MQTTClient Class is existing. Eventually
    # MQTTClient should be dimissed and this instance should be used. API Keys
    # or some other security mechanism to be implemented later.
    def __init__(self, api_key=None, api_secret=None, **kwargs):
        global aa_log, mode, sub_topics, callbacks
        self.mqtt_client = None
        self.host = settings.MQTT_SETTINGS[settings.ENVIRONMENT]["host"]
        self.port = settings.MQTT_SETTINGS[settings.ENVIRONMENT]["port"]
        aa_log = settings.ASSA_ABLOY_LOGGER
        if kwargs is not None:
            for k, v in kwargs.items():
                if k == "mode":
                    mode = v
                elif k == "pub":
                    self.pub_topics = v
                elif k == "sub":
                    sub_topics = v
                elif k == "cb":
                    callbacks = v

        # As part of MQTT Dynamic subscription, pub_topics can be provided
        # to Gateway. With sub_topics we can create a new receive_loop.
        # Callbacks will be used when message is received on the sub topic.

    def __enter__(self):
        self.mqtt_client = mqtt.Client(client_id="vriot_mqtt_subscribe/" +
                                                 "".join(random.choice(
                                                     "0123456789ADCDEF") for x
                                                         in range(23 - 5)))
        # when message is received
        self.mqtt_client.on_message = self.on_mqtt_message
        # when connection is successful
        self.mqtt_client.on_connect = self.on_mqtt_connect
        # when connection is disconnected successfully
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        if settings.MQTT_SSL_ENABLED:
            self.ca_file = settings.MQTT_SETTINGS[settings.ENVIRONMENT].get(
                "ca_cert")
            self.mqtt_client.tls_set(self.ca_file)
            self.port = settings.MQTT_SETTINGS[settings.ENVIRONMENT].get(
                "secure_port", 8883)
        self.mqtt_client.connect(self.host, self.port)
        aa_log.debug("Initiating {} MQTT Connection".format(str(mode)))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mqtt_client.disconnect()

    @staticmethod
    def on_mqtt_connect(mqtt_client_handle, data, rc):
        aa_log.info(
            "Connected to MQTT Broker Host: " + str(mqtt_client_handle._host) +
            " Port:" + str(mqtt_client_handle._port))
        mqtt_client_handle.subscribe(sub_topics)
        aa_log.debug("Subscribing to {} MQTT Topics".format(str(mode)) +
                     str(sub_topics))

    @staticmethod
    def on_mqtt_disconnect(mqtt_client_handle, data, rc):
        aa_log.info(
            "Disconnected from MQTT Broker Host: " +
            str(mqtt_client_handle._host) +
            " Port:" + str(mqtt_client_handle._port))

    @staticmethod
    def on_mqtt_message(mqtt_client_handle, obj, message_object):
        try:
            topic = str(message_object.topic)
            message = message_object.payload.decode()
            aa_log.debug("Received on {} MQTT Topic: '{}' Payload: {}".format(
                str(mode), topic, message))
            callbacks.get(topic)(topic, message)
        except Exception as e:
            aa_log.critical(str(e), exc_info=True)

    def receive_loop(self):
        try:
            self.mqtt_client.loop_forever()
        except Exception as e:
            aa_log.critical("Subscribe Loop Error - " + str(e), exc_info=True)

    def on_sdk_publish(self, topic, message):
        if (topic, 1) in self.pub_topics:
                payload = {"topic": topic, "payload": json.dumps(message)}
                async_mqtt_publish.apply_async((payload,))
        else:
            aa_log.critical("Publish Failed."
                            "Trying to publish on a unavailable topic {}"
                            "".format(topic))


class MQTTClient(object):
    def __init__(self,
                 host=settings.MQTT_SETTINGS[settings.ENVIRONMENT]["host"],
                 port=settings.MQTT_SETTINGS[settings.ENVIRONMENT]["port"],
                 ca_file=settings.MQTT_SETTINGS[settings.ENVIRONMENT].get(
                     "ca_cert")):
        self.mqtt_client = None
        self.host = host
        self.port = port
        self.ca_file = ca_file

    def __enter__(self):
        self.mqtt_client = mqtt.Client(client_id="vriot_mqtt_subscribe/" +
                                                 "".join(random.choice(
                                                     "0123456789ADCDEF") for _
                                                         in range(23 - 5)))
        # when message is received
        self.mqtt_client.on_message = self.on_message
        # when message is published
        self.mqtt_client.on_publish = self.on_publish
        # when connection is successful
        self.mqtt_client.on_connect = self.on_connect
        if settings.MQTT_SSL_ENABLED:
            self.mqtt_client.tls_set(self.ca_file)
            self.port = settings.MQTT_SETTINGS[settings.ENVIRONMENT].get(
                "secure_port", 8883)
        self.mqtt_client.connect(self.host, self.port)
        mqtt_log.debug("Initiating MQTT Connection")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mqtt_client.disconnect()

    @staticmethod
    def on_publish(mqtt_client_handle, obj, mid):
        mqtt_log.debug("Message Published to MQTT Topic")
        # mqtt_client_handle.disconnect()

    @staticmethod
    def on_connect(mqtt_client_handle, data, rc):
        mqtt_log.info(
            "Connected to MQTT Broker Host: " + str(mqtt_client_handle._host) +
            " Port:" + str(mqtt_client_handle._port))
        mqtt_topics = settings.MQTT_SETTINGS["common"]["topics"]
        mqtt_client_handle.subscribe(mqtt_topics)
        mqtt_log.debug("Subscribing to MQTT Topics" + str(mqtt_topics))

    @staticmethod
    def on_message(mqtt_client_handle, obj, message_object):
        try:
            mqtt_log.debug("Received on MQTT Topic: '{}' Payload: {}".format(
                str(message_object.topic), message_object.payload.decode()))
            async_mqtt_subscribe.apply_async((str(message_object.topic),
                                              message_object.payload.decode()))
        except Exception as e:
            mqtt_log.critical(str(e), exc_info=True)

    def receive_loop(self):
        try:
            self.mqtt_client.loop_forever()
        except Exception as e:
            mqtt_log.critical("Subscribe Loop Error - " +
                              str(e), exc_info=True)
