import json

from django.conf import settings

from services.tasks import async_mqtt_publish

mqtt_log = settings.MQTT_LOGGER


class MQTTPublishFunctions(object):
    def __init__(self):
        self.controller_gateway_device_commands = \
            "controller/gateway/device/commands"
        self.controller_gateway_commands = "controller/gateway/commands"
        self.controller_gateway_device_state = "controller/gateway/device/state"
        self.controller_gateway_state = "controller/gateway/state"

    @staticmethod
    def payload_generation(payload, send_mqtt=True, queued_payload=None):
        try:
            queued_payload = [] if not queued_payload else queued_payload
            queued_payload.append(payload)
            if send_mqtt:
                mqtt_log.debug("Sending payload {}".format(queued_payload))
                async_mqtt_publish.apply_async((queued_payload,))
                return True
            else:
                return queued_payload
        except Exception:
            mqtt_log.critical("MQTT Publish failed for payload {}".format(
                queued_payload), exc_info=True)


class DeviceOperationsCommands(MQTTPublishFunctions):
    def __init__(self):
        super().__init__()

    def on_off(self, device_euid, command, send_mqtt=True, queued_payload=None):
        try:
            mqtt_log.debug(
                "Sending {} command for device {}".format(command, device_euid))
            message = {
                "device_euid": device_euid.upper(),
                "commands": [{
                    "command": command.upper()
                }]
            }
            payload = {
                "topic": self.controller_gateway_device_commands,
                "payload": json.dumps(message)
            }
            return self.payload_generation(payload, send_mqtt=send_mqtt,
                                           queued_payload=queued_payload)
        except Exception:
            mqtt_log.critical(
                "{} command failed for device {}".format(
                    command, device_euid), exc_info=True)

    def color(self, device_euid, color, mqtt_command, delay=0, send_mqtt=True,
              queued_payload=None):
        try:
            mqtt_log.debug(
                "Sending COLOR command for device {}".format(device_euid))
            rgb_color = []
            for value in color:
                rgb_color.append(int(value) % 256)
            message = {
                "device_euid": device_euid.upper(),
                "commands": [{
                    "command": mqtt_command,
                    "color": rgb_color,
                    "duration": int(delay)
                }]
            }
            payload = {
                "topic": self.controller_gateway_device_commands,
                "payload": json.dumps(message)
            }
            return self.payload_generation(payload, send_mqtt=send_mqtt,
                                           queued_payload=queued_payload)
        except Exception:
            mqtt_log.critical(
                "COLOR command failed for device {}".format(
                    device_euid), exc_info=True)

    def brightness(self, device_euid, value, mqtt_command, delay=0,
                   send_mqtt=True, queued_payload=None):
        try:
            mqtt_log.debug(
                "Sending BRIGHTNESS command for device {}".format(device_euid))
            message = {
                "device_euid": device_euid.upper(),
                "commands": [{
                    "command": mqtt_command,
                    "level": int(value) % 256,
                    "duration": int(delay)
                }]
            }
            payload = {
                "topic": self.controller_gateway_device_commands,
                "payload": json.dumps(message)
            }
            return self.payload_generation(payload, send_mqtt=send_mqtt,
                                           queued_payload=queued_payload)
        except Exception:
            mqtt_log.critical(
                "BRIGHTNESS command failed for device {}".format(
                    device_euid), exc_info=True)

    def device_attributes(self, device_euid, send_mqtt=True,
                          queued_payload=None):
        try:
            mqtt_log.debug("Request device state {}".format(device_euid))
            message = {
                "device_euid": device_euid
            }
            payload = {
                "topic": self.controller_gateway_device_state,
                "payload": json.dumps(message)
            }
            return self.payload_generation(payload, send_mqtt=send_mqtt,
                                           queued_payload=queued_payload)
        except Exception:
            mqtt_log.critical("Request device state {} failed "
                              "".format(device_euid), exc_info=True)

    def door_lock(self, device_euid, command, lock_pin="1234", send_mqtt=True, queued_payload=None):
        try:
            mqtt_log.debug(
                "Sending {} command for device {}".format(command, device_euid))
            message = {
                "device_euid": device_euid.upper(),
                "commands": [{
                    "command": command.upper(),
                    "pin": lock_pin
                }]
            }
            payload = {
                "topic": self.controller_gateway_device_commands,
                "payload": json.dumps(message)
            }
            return self.payload_generation(payload, send_mqtt=send_mqtt,
                                           queued_payload=queued_payload)
        except Exception:
            mqtt_log.critical(
                "{} command failed for device {}".format(
                    command, device_euid), exc_info=True)


class GatewayCommands(MQTTPublishFunctions):
    def __init__(self):
        super().__init__()

    def auth_response(self, gateway_euid, device_euid, permitted=0,
                      send_mqtt=True, queued_payload=None):
        try:
            mqtt_log.debug(
                "Responding to permission request device {}".format(
                    device_euid))
            command = "PERMITTED" if permitted == 1 else "NOT_PERMITTED"
            message = {
                "gateway_euid": gateway_euid,
                "commands": [{
                    "command": command,
                    "device_euid": device_euid
                }]
            }
            payload = {
                "topic": self.controller_gateway_commands,
                "payload": json.dumps(message)
            }
            return self.payload_generation(payload, send_mqtt=send_mqtt,
                                           queued_payload=queued_payload)
        except Exception:
            mqtt_log.critical("Auth response failed gateway {} device {} "
                              "".format(gateway_euid, device_euid),
                              exc_info=True)

    def gateway_settings(self, gateway_euid, send_mqtt=True,
                         queued_payload=None):
        try:
            message = {"gateway_euid": gateway_euid}
            payload = {
                "topic": self.controller_gateway_state,
                "payload": json.dumps(message)
            }
            return self.payload_generation(payload, send_mqtt=send_mqtt,
                                           queued_payload=queued_payload)
        except Exception:
            mqtt_log.critical("Gateway settings failed gateway {}"
                              "".format(gateway_euid), exc_info=True)

    def device_join(self, gateway_euid, duration=120, send_mqtt=True,
                    queued_payload=None):
        try:
            mqtt_log.debug(
                "Received join request for gateway {}".format(gateway_euid))
            message = {
                "gateway_euid": gateway_euid,
                "commands": [{
                    "command": "DEVICE_JOIN",
                    "duration": duration
                }]
            }
            payload = {
                "topic": self.controller_gateway_commands,
                "payload": json.dumps(message)
            }
            return self.payload_generation(payload, send_mqtt=send_mqtt,
                                           queued_payload=queued_payload)
        except Exception:
            mqtt_log.critical(
                "Device Join command gateway {} failed".format(gateway_euid),
                exc_info=True)

    def device_leave(self, device_euid, duration=120, send_mqtt=True,
                     queued_payload=None):
        try:
            mqtt_log.debug(
                "Received leave request for device {}".format(device_euid))
            message = {
                "device_euid": device_euid,
                "commands": [{
                    "command": "DEVICE_LEAVE",
                    "duration": duration
                }]
            }
            payload = {
                "topic": self.controller_gateway_device_commands,
                "payload": json.dumps(message)
            }
            return self.payload_generation(payload, send_mqtt=send_mqtt,
                                           queued_payload=queued_payload)
        except Exception:
            mqtt_log.critical(
                "Device leave command device {} failed".format(device_euid),
                exc_info=True)
