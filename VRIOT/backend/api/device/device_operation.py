from django.conf import settings

from common.db_models.device_models import SensorAttribute
from services.integration.mqtt.publish_functions import DeviceOperationsCommands

vriot_log = settings.VRIOT_LOGGER


class DeviceOperation(object):
    @staticmethod
    def device_mqtt_operation(user_command, device_euid,
                              configured_value):
        try:
            vriot_log.debug("Identify MQTT command from user command")
            user_command = user_command.upper()

            if 'level' in configured_value:
                configured_value['value'] = configured_value['level']
            if 'on' in configured_value:
                configured_value['value'] = configured_value['on']
            if 'lock' in configured_value:
                configured_value['value'] = configured_value['lock']
            if user_command == "COLOR":
                red = configured_value.get("red", 255)
                green = configured_value.get("green", 255)
                blue = configured_value.get("blue", 255)
                value = [int(red), int(green), int(blue)]
            else:
                value = int(configured_value["value"])
            delay = 0
            # Checking for equivalent MQTT command
            sensor_object = SensorAttribute.get(
                {'user_command': user_command})
            # Publish messages on MQTT here (dev_id, value, mqtt_command, delay)
            mqtt_operations = DeviceOperationsCommands()
            if user_command == "STATE":
                command = sensor_object['mqtt_command'][int(value)]
                mqtt_operations.on_off(device_euid, command)
            if user_command == "COLOR":
                command = sensor_object['mqtt_command'][0]
                mqtt_operations.color(device_euid, value, command, delay=int(delay))
            if user_command == "BRIGHTNESS":
                mqtt_operations.brightness(device_euid, int(value),
                                           sensor_object['mqtt_command'][0],
                                           delay=int(delay))
            if user_command == "LOCK_STATE":
                index_map = {1: 0, 2: 1}
                command = sensor_object['mqtt_command'][index_map[int(value)]]
                lock_pin = configured_value.get('lock_pin', "1234")
                mqtt_operations.door_lock(device_euid, command, lock_pin)
            return True
        except Exception:
            vriot_log.critical("Device MQTT operation failed {} device {} "
                               "".format(user_command, device_euid),
                               exc_info=True)
