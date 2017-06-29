import codecs
import datetime
import json

from django.conf import settings

from common.db_models.device_models import DeviceAuth, Device, \
    DeviceSensor, SensorAttribute
from common.db_models.device_serializers import DeviceAuthSerializer, \
    DeviceSensorSerializer, DeviceSerializer
from common.db_models.gateway_models import Gateway
from common.db_models.gateway_serializers import GatewaySerializer

mqtt_log = settings.MQTT_LOGGER


class MQTTSubscribeFunction(object):
    def __init__(self, mqtt_handle=None, topic=None, message=None):
        self.mqtt_handle = mqtt_handle
        self.topic = topic
        self.message = message
        self.sensor_type_map = settings.SENSOR_TYPE_MAP
        self.attribute_value_key = settings.ATTRIBUTE_VALUE_KEYS
        self.topic_function_resolve()

    def topic_function_resolve(self):
        try:
            mqtt_topic_function_map = {
                "gateway/device/function/attribute":
                    self.device_function_attribute,
                "gateway/device/settings": self.device_settings,
                "gateway/device/authentication": self.device_authentication,
                "gateway/scan_list": self.gateway_scan_list,
                "gateway/settings": self.gateway_settings,
            }
            if self.topic and self.message:
                mqtt_log.debug("Received Topic: {}, Payload: {}".format(
                    self.topic, self.message))
                self.topic = str(self.topic)
                self.message = json.loads(self.message)
                if mqtt_topic_function_map.get(self.topic):
                    mqtt_topic_function_map.get(self.topic)()
        except Exception as e:
            mqtt_log.critical("Subscribe Function Error - " + str(e),
                              exc_info=True)

    @staticmethod
    def check_gateway(gateway_euid, require_enabled=False):
        if require_enabled:
            gateway_obj = Gateway.get(query={
                "gateway_euid": gateway_euid,
                "is_enabled": True
            })
        else:
            gateway_obj = Gateway.get(query={
                "gateway_euid": gateway_euid
            })
        return gateway_obj

    def attribute_value(self, sensor_attr_obj, value):
        if not isinstance(value, list):
            value = [value]
        return dict(zip(self.attribute_value_key[sensor_attr_obj[
            "user_command"]], value))

    def gateway_scan_list(self):
        """
        sample payload
        {
          "gateway_euid": "EC:8C:A2:33:BA:E0",
          "gateway": [
            {
              "network_id": "FFFF",
              "device_euid": "00:00:C0:FB:1E:AA:96:76",
              "auth": 1,
              "last_seen": 0
            },
            {
              "network_id": "FFFF",
              "device_euid": "00:00:CF:EA:1A:2B:6B:08",
              "auth": 1,
              "last_seen": 0
            },
            {
              "network_id": "FFFF",
              "device_euid": "00:00:DC:FB:A1:46:AA:E4",
              "auth": 1,
              "last_seen": 0
            },
            {
              "network_id": "FFFF",
              "device_euid": "00:00:78:A5:04:56:F8:6D",
              "auth": 1,
              "last_seen": 0
            }
          ]
        }
        :return:
        """
        try:
            if self.message and isinstance(self.message, dict):
                gateway_euid = self.message.get("gateway_euid")
                gateway_devices = self.message.get("devices")
                gateway_obj = self.check_gateway(gateway_euid)
                if gateway_obj:
                    # Enable gateway, if disabled, only while provisioning
                    gateway_obj.update({"is_enabled": True,
                                        "gateway_device_list": []})
                    if gateway_devices:
                        for iot_device in gateway_devices:
                            device_euid = iot_device.get("device_euid")
                            device_auth_state = int(iot_device.get("auth"))
                            gateway_obj["gateway_device_list"].append({
                                "network_id": iot_device.get("network_id"),
                                "device_euid": device_euid,
                                "auth_state": device_auth_state,
                                "last_seen": iot_device.get("last_seen"),
                            })
                            # Update the device authentication with auth status
                            device_auth_obj = DeviceAuth.get(query={
                                "device_euid": device_euid})
                            device_obj = Device.get(query={
                                "device_euid": device_euid})
                            if device_obj:
                                is_enabled = True if iot_device.get("auth") == 0 \
                                    else False
                                device_obj.update({"is_enabled": is_enabled})
                                DeviceSerializer(Device,
                                                 data=device_obj).save_to_db()
                            if device_auth_obj:
                                device_auth_obj.update({
                                    "auth_state": device_auth_state})
                                DeviceAuthSerializer(
                                    DeviceAuth,
                                    data=device_auth_obj).save_to_db()
                    GatewaySerializer(Gateway, data=gateway_obj).save_to_db()
        except Exception as e:
            mqtt_log.critical(str(e), exc_info=True)

    def gateway_settings(self):
        """
        sample payload
        {
          "gateway_euid": "EC:8C:A2:33:BA:E0",
          "networks": [
            {
              "network_mac": "00:00:00:00:00:00:00:00",
              "network_type": "zigbee",
              "network_id": "",
              "radio_tx_power": 0,
              "radio_channel": 0
            },
            {
              "network_mac": "00:02:5B:A0:86:77",
              "network_type": "ble",
              "network_id": "FFFF",
              "radio_tx_power": "TODO",
              "radio_channel": "TODO"
            }
          ],
          "ap-details": [
            {
              "ip": "192.168.149.48",
              "mac": "ec:8c:a2:33:ba:e0",
              "netmask": "255.255.255.0",
              "gateway": "192.168.149.254",
              "dns": " 172.19.0.6"
            }
          ]
        }
        :return:
        """
        try:
            if self.message and isinstance(self.message, dict):
                gateway_euid = self.message.get("gateway_euid")
                gateway_obj = self.check_gateway(gateway_euid)
                if not gateway_obj:
                    gateway_name = "Auto Created " + str(
                        datetime.datetime.now())
                    gateway_obj = GatewaySerializer(data={
                        "gateway_euid": gateway_euid,
                        "gateway_name": gateway_name
                    }).save_to_db()
                iot_networks = self.message.get("networks")
                ip_networks = self.message.get("ap-details")
                diagnostics = self.message.get("diagnostics", [])
                gateway_obj.update({
                    "is_enabled": True,
                    "gateway_iot_networks": [],
                    "gateway_ip_networks": [],
                    "gateway_diagnostics": diagnostics,
                    "gateway_state": 1,
                })
                if iot_networks:
                    for iot_network in iot_networks:
                        network_id = iot_network.get("network_id", "0x0000")
                        network_id = "0x0000" if not network_id else \
                            network_id
                        network_mac = iot_network.get(
                            "network_mac", "00:00:00:00:00:00:00:00")
                        network_mac = "00:00:00:00:00:00:00:00" if not \
                            network_mac else network_mac
                        iot_data = {
                            "network_type": iot_network.get("network_type"),
                            "network_id": network_id,
                            "network_mac": network_mac,
                            "set_radio_tx_power": iot_network.get(
                                "set_radio_tx_power", 0),
                            "get_radio_tx_power": iot_network.get(
                                "radio_tx_power", 0),
                            "set_radio_channel": iot_network.get(
                                "set_radio_channel", 0),
                            "get_radio_channel": iot_network.get(
                                "radio_channel", 0),
                        }
                        gateway_obj["gateway_iot_networks"].append(iot_data)
                if ip_networks:
                    for ip_network in ip_networks:
                        ip_data = {
                            "ip": ip_network.get("ip"),
                            "netmask": ip_network.get("netmask"),
                            "mac": ip_network.get("mac").upper(),
                            "gateway": ip_network.get("gateway"),
                            "dns": [ip_network.get("dns")],
                        }
                        gateway_obj["gateway_ip_networks"].append(ip_data)
                GatewaySerializer(Gateway, data=gateway_obj).save_to_db()
        except Exception as e:
            mqtt_log.critical(str(e), exc_info=True)

    def device_function_attribute(self):
        """
        This function receives the status updates from the thing. Whenever
        there is a change in the state of the device, the device responds
        with the state of the device. For ex. If from the front end if the
        user switches on the light, the mqtt message is sent on the channel,
        on successful status change, the device responds on this channel.

        - **Response from Gateway:**::
            {
              "device_id": "<device_id of the thing>",
              "network_id": "<IoT network ID. Only for zigbee>",
              "gateway_id": "<gateway_id from where the request is received>",
              "device_type": "<Type of IoT thing>",
              "attributes": [
                {
                  "value": <Value of the attribute>,
                  "attribute": "<Type of thing attribute>"
                }
              ]
            }
        :return: None
        """
        try:
            if self.message and isinstance(self.message, dict):
                device_euid = self.message.get("device_euid")
                gateway_euid = self.message.get("gateway_euid")
                attributes = self.message.get("attributes")
                gateway_obj = self.check_gateway(gateway_euid,
                                                 require_enabled=True)
                if gateway_obj:
                    device_sensor_obj = DeviceSensor.get(query={
                        "device_euid": device_euid
                    })
                    if not device_sensor_obj:
                        mqtt_log.warning(
                            "Device Sensor not available for device {}"
                            "".format(device_euid)
                        )
                        return False
                    for attribute in attributes:
                        attribute_command = attribute["attribute"]
                        sensor_attr_obj = SensorAttribute.get(query={
                            "attribute_command": attribute_command
                        })
                        sensor_attr_id = str(sensor_attr_obj["_id"])
                        device_sensor_obj["capability"][sensor_attr_id].update({
                            "reported_value": self.attribute_value(
                                sensor_attr_obj,
                                attribute["value"]),
                            "reported_on": datetime.datetime.now()
                        })
                    DeviceSensorSerializer(DeviceSensor,
                                           data=device_sensor_obj).save_to_db()
        except Exception as e:
            mqtt_log.critical(str(e), exc_info=True)

    def device_settings(self):
        """
        sample payload
        {
          "gateway_id": "00:00:00:00:00:00:00:00",
          "device_id": "00:00:78:A5:04:56:F8:6D",
          "endpoints": [
            {
              "end_point_id": "0",
              "attributes": [
                {
                  "attribute": "ON_OFF",
                  "value": 0
                },
                {
                  "attribute": "COLOR",
                  "value": [
                    0,
                    0,
                    0
                  ]
                },
                {
                  "attribute": "BRIGHTNESS",
                  "value": 0
                }
              ]
            }
          ]
        }
        
        {
          "gateway_euid": "D8:38:FC:25:BB:60",
          "device_euid": "00:0D:6F:00:03:1D:85:5F",
          "device_type": "DOOR_LOCK",
          "endpoints": [
            {
              "end_point_id": "0",
              "attributes": [
                {
                  "attribute": "LOCK_STATE",
                  "value": 0
                }
              ]
            }
          ]
        }
        :return:
        """
        try:
            if self.message and isinstance(self.message, dict):
                device_euid = self.message.get("device_euid")
                gateway_euid = self.message.get("gateway_euid")
                gateway_obj = self.check_gateway(gateway_euid,
                                                 require_enabled=True)
                if gateway_obj:
                    # Just to get device id
                    device_obj = Device.get(query={
                        "device_euid": device_euid
                    })
                    if not device_obj:
                        mqtt_log.warning(
                            "Device not available for device {}"
                            "".format(device_euid)
                        )
                        return False
                    # iterating over the endpoints
                    sensor_type = self.message.get("device_type", None)
                    for endpoint in self.message["endpoints"]:
                        # setting the function id from message
                        # function_id = endpoint.get("end_point_id", 1)
                        # function_id = 1 if not function_id else int(function_id)
                        sensor_capability = {}
                        # Iterate over attributes
                        device_sensor_obj = DeviceSensor.get(query={
                            "device_euid": device_euid
                        })
                        if device_sensor_obj:
                            sensor_capability.update(
                                device_sensor_obj["capability"])
                        for attribute in endpoint["attributes"]:
                            attribute_command = attribute["attribute"]
                            sensor_attr_obj = SensorAttribute.get(query={
                                "attribute_command": attribute_command
                            })
                            if sensor_attr_obj:
                                sensor_attr_id = str(sensor_attr_obj["_id"])
                                if sensor_attr_id in sensor_capability:
                                    continue
                                else:
                                    value = self.attribute_value(
                                        sensor_attr_obj, attribute["value"])
                                    sensor_capability.update({
                                        sensor_attr_id: {
                                            "attribute_id": sensor_attr_id,
                                            "user_command": sensor_attr_obj[
                                                "user_command"],
                                            "attribute_parameters_value": [],
                                            "created_on":
                                                datetime.datetime.now(),
                                            "updated_on":
                                                datetime.datetime.now(),
                                            "reported_on":
                                                datetime.datetime.now(),
                                            "reported_value": value,
                                            "configured_value": value
                                        }
                                    })
                            else:
                                mqtt_log.warning(
                                    "Sensor Attribute not available for "
                                    "attribute command {}"
                                    "".format(attribute_command)
                                )
                                continue
                        # create sensor info data to be updated
                        if device_sensor_obj:
                            device_sensor_obj.update({
                                "capability": sensor_capability
                            })
                            DeviceSensorSerializer(
                                DeviceSensor, data=device_sensor_obj
                            ).save_to_db()
                        else:
                            device_sensor_obj = {
                                "device_id": device_obj["_id"],
                                "device_euid": device_obj["device_euid"],
                                "sensor_type": self.sensor_type_map[
                                    sensor_type],
                                "capability": sensor_capability
                            }
                            device_sensor = DeviceSensorSerializer(
                                data=device_sensor_obj).save_to_db()
                            if "device_sensor" not in device_obj:
                                device_obj["device_sensor"] = []
                            device_obj["device_sensor"].append({
                                "sensor_id": str(device_sensor["_id"]),
                                "sensor_type": self.sensor_type_map[
                                    sensor_type]
                            })
                    device_obj.update({"is_enabled": True})
                    DeviceSerializer(Device, data=device_obj).save_to_db()
        except Exception as e:
            mqtt_log.critical(str(e), exc_info=True)

    def device_authentication(self):
        """
        In this function we will receive a authentication request from the
        IoT Gateway for adding the device to the device of the gateway device
        global table. In response to the authentication request we have to
        return the authenticated request back to the gateway.

        - **Request from Gateway:**::
            {
              "gateway_id": "<gateway_id from where the request is received>",
              "network_id": "<network_id of the IoT network>",
              "device_id": "<device_id of the thing to be authenticated>",
              "Serial_Num": "<Not Implemented Random value sent>"
            }
        - **Response to Gateway:**::
            {
              "gateway_id": "<gateway_id received in request>",
              "commands": [
                {
                  "command": "<PERMITTED/NOT PERMITTED>",
                  "device_id": "<device_id received in request>"
                }
              ]
            }
        """
        try:
            from services.integration.mqtt.publish_functions import \
                GatewayCommands, DeviceOperationsCommands
            if self.message and isinstance(self.message, dict):
                device_euid = self.message.get("device_euid")
                gateway_euid = self.message.get("gateway_euid")
                gateway_obj = self.check_gateway(gateway_euid,
                                                 require_enabled=True)
                if gateway_obj:
                    device_auth_obj = DeviceAuth.get(query={
                        "device_euid": device_euid,
                        "gateway_euid": gateway_euid
                    })

                    if not device_auth_obj:
                        # scan based add workflow.
                        # if device not present in DeviceAuth Table, add it
                        # with is_user_allowed = False, discovered_mode = 0
                        new_device_auth = {
                            "device_euid": device_euid,
                            "gateway_euid": gateway_euid,
                            "is_blacklisted": False,
                            "state": 1,
                            "discovered_mode": 0,
                            "is_user_allowed": False
                        }
                        DeviceAuthSerializer(data=new_device_auth).save_to_db()
                        mqtt_log.debug("No Entry in Auth Table. Adding Device :"
                                       " {}".format(device_euid))
                        return True

                    # check if user is allowed, scan based add check.
                    device_auth_is_user_allowed = device_auth_obj.get(
                        'is_user_allowed')

                    if device_auth_obj and device_auth_is_user_allowed:
                        # updating the following things in DB before sending
                        # response
                        # Adding the payload to DB, gateway from where the
                        # authentication arrived, is the gateway authenticated,
                        # the auth time
                        device_auth_obj.update({
                            "gateway_euid": gateway_euid
                        })
                        permitted = 1
                        if device_auth_obj["is_blacklisted"]:
                            device_auth_obj.update({"state": 2})
                            permitted = 0
                        DeviceAuthSerializer(DeviceAuth,
                                             data=device_auth_obj).save_to_db()
                        device_obj = Device.get(query={
                            "device_euid": device_euid
                        })
                        if device_obj:
                            if device_auth_obj["is_blacklisted"]:
                                mqtt_log.info(
                                    "Rejected authentication for device {}"
                                    "".format(device_euid))
                                if device_obj["is_enabled"]:
                                    device_obj["is_enabled"] = False
                            else:
                                # updating the device info document by setting
                                # the is_enabled variable as true and requesting
                                # for device attributes if it is getting enabled
                                # from false
                                mqtt_log.info(
                                    "Accepted authentication for device "
                                    "{}".format(device_euid))
                                device_obj["is_enabled"] = True
                            DeviceSerializer(
                                Device, data=device_obj).save_to_db()
                            auth_payload = GatewayCommands().auth_response(
                                gateway_euid, device_euid, permitted,
                                send_mqtt=False)
                            DeviceOperationsCommands().device_attributes(
                                device_euid, queued_payload=auth_payload)
                        else:
                            GatewayCommands().auth_response(
                                gateway_euid, device_euid, permitted)
                    else:
                        GatewayCommands().auth_response(
                            gateway_euid, device_euid, 0)
                        mqtt_log.debug("Authentication received for unknown"
                                       " device: {}".format(device_euid))
                else:
                    GatewayCommands().auth_response(
                        gateway_euid, device_euid, 0)
                    mqtt_log.debug("Authentication received from unknown "
                                   "gateway {} device {}".format(gateway_euid,
                                                                 device_euid))
        except Exception as e:
            mqtt_log.critical(str(e), exc_info=True)