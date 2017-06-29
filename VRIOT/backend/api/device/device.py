import json

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR

from common.api import VRIoTAPIView
from common.db_models.device_models import Device, DeviceSensor, DeviceAuth
from common.db_models.device_serializers import DeviceSerializer, \
    DeviceSensorSerializer, DeviceAuthSerializer
from services.integration.mqtt.publish_functions import GatewayCommands
from .device_operation import DeviceOperation

api_log = settings.VRIOT_LOGGER


class DeviceAPI(VRIoTAPIView):
    def __init__(self):
        super().__init__()

    @staticmethod
    def get(request, resource_id=None):
        try:
            # self.authenticate_request(request)
            device_objs = []
            # Checking if requested for specific resource id
            if resource_id:
                api_log.debug("Querying for device _id: {}".format(
                    resource_id))
                device_obj = Device.get_by_id(resource_id)
                if device_obj:
                    Device.get_capability_info(device_obj)
                    device_objs = device_obj
            else:
                api_log.debug("Querying for all devices")
                device_objs = Device.all()
                if device_objs:
                    for device_obj in device_objs:
                        Device.get_capability_info(device_obj)
            if not device_objs:
                api_log.error("Device(s) not found. Sending HTTP 404")
                return Response(status=status.HTTP_404_NOT_FOUND)
            api_log.debug("Device(s) found. Sending response with HTTP 200")
            return Response(device_objs, status=status.HTTP_200_OK)
        except Exception as e:
            api_log.critical("Request Failed. Sending HTTP 500", exc_info=True)
            return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def post(request):
        try:
            post_body = json.loads(request.body.decode())
            device_euid = post_body.get("device_euid")
            device_name = post_body.get("device_name")
            device_tags = post_body.get("tags", [])
            device_gateway = post_body.get("gateway_euid")
            device_obj = Device.get(query={
                "device_euid": device_euid})
            if device_obj:
                api_log.info("Device exists. _id: {}. Sending response with "
                             "HTTP 409".format(device_obj["_id"]))
                return Response(device_obj, status=status.HTTP_409_CONFLICT)

            api_log.debug("Processing device data")
            device_data = {
                "device_name": device_name,
                "device_euid": device_euid,
                "gateway_euid": device_gateway,
                "tags": device_tags,
                "is_enabled": False
            }
            api_log.debug("Saving device data")
            device_obj = DeviceSerializer(data=device_data).save_to_db()
            if not device_obj:
                return Response("unable to add device to DB."
                                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # check if there is a existing Device Auth table entry.
            # if so, this device is coming in as a scan based add.
            db_device_auth_obj = DeviceAuth.get(
                query={'device_euid': device_obj["device_euid"]})
            if db_device_auth_obj:
                # then just update.
                api_log.info("Allowing a scan based device add, device_euid" +
                             str(device_obj["device_euid"]))
                db_device_auth_obj.update({
                    "is_user_allowed": True
                })
                DeviceAuthSerializer(
                    DeviceAuth, data=db_device_auth_obj
                ).save_to_db()
            else:
                # create a new device_auth_object
                api_log.debug("Processing device auth data")
                device_auth = {
                    "device_euid": device_obj["device_euid"],
                    "gateway_euid": device_gateway,
                    "is_blacklisted": False,
                    "state": 0,
                    "discovered_mode": 1,
                    "is_user_allowed": True
                }
                api_log.debug("Saving device auth data")
                DeviceAuthSerializer(data=device_auth).save_to_db()
                api_log.debug("Requesting gateway for device join")
            api_log.info("Device added. _id: {}. Sending response with "
                         "HTTP 201".format(device_obj["_id"]))
            return Response(device_obj, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            api_log.error("Device data validation failed: {}. Sending "
                          "response with HTTP 400".format(e.detail))
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            api_log.critical("Request Failed. Sending HTTP 500", exc_info=True)
            return Response(e, status=HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def patch(request, resource_id=None):
        try:
            if not resource_id:
                return Response({
                    "device/<id>": [
                        "ID field is required in URL"
                    ]
                }, status=status.HTTP_400_BAD_REQUEST)
            post_body = json.loads(request.body.decode())
            device_name = post_body.get("device_name")
            device_tags = post_body.get("tags", [])
            device_obj = Device.get_by_id(resource_id)
            if not device_obj:
                api_log.error("Device not found. _id: {}. Sending HTTP "
                              "404".format(resource_id))
                return Response(status=status.HTTP_404_NOT_FOUND)
            device_gateway = post_body.get("gateway_euid", device_obj["gateway_euid"])
            api_log.debug("Processing device data")
            device_euid = device_obj["device_euid"]
            device_new_data = {}
            if device_name:
                device_new_data.update({"device_name": device_name})
            if device_tags:
                device_new_data.update({"tags": device_tags})
            if device_gateway:
                device_new_data.update({"gateway_euid": device_gateway})
            if device_obj["gateway_euid"] != device_gateway:
                # send not permitted to old gateway for the device
                GatewayCommands().auth_response(device_obj["gateway_euid"],
                                                device_euid, permitted=0)
                # update in device auth doc
                device_auth_obj = DeviceAuth.get(query={
                    "device_euid": device_obj["device_euid"],
                    "gateway_euid": device_obj["gateway_euid"]
                })
                device_auth_obj.update({
                    "gateway_euid": device_gateway,
                    "is_blacklisted": False,
                    "state": 0,
                    "discovered_mode": 1,
                    "is_user_allowed": True
                })
                DeviceAuthSerializer(DeviceAuth,
                                     data=device_auth_obj).save_to_db()
                # remove device sensor doc
                DeviceSensor.delete(query={
                    'device_euid': device_obj["device_euid"]
                }, hard_delete=True)
                # device_obj["old_gateway_euid"] = device_obj["gateway_euid"]
                device_obj.update({"gateway_euid": device_gateway})
                DeviceSerializer(Device, data=device_obj).save_to_db()
                # send device join to new gateway for the device
                GatewayCommands().device_join(device_gateway)
                return Response(device_obj, status=status.HTTP_200_OK)
            device_sensors = None
            mqtt_commands = []
            if "device_sensors" in post_body:
                device_sensors = post_body.pop("device_sensors")
            if device_sensors:
                api_log.debug("Processing device sensor data")
                # fetch for the sensor
                for sensor in device_sensors:
                    try:
                        # check for sensor_id and capability.
                        if "sensor_id" not in sensor or "capability" not in \
                                sensor:
                            api_log.debug("Device sensor data not proper.")
                            continue
                        device_sensor_obj = DeviceSensor.get_by_id(
                            sensor["sensor_id"])
                        if not device_sensor_obj:
                            api_log.error(
                                "Device sensor not found. _id: {}. Sending "
                                "HTTP 404".format(sensor["sensor_id"]))
                            return Response({
                                "sensor_id": "Sensor id not found"},
                                status=status.HTTP_400_BAD_REQUEST)
                        for attribute_id, value in sensor["capability"].items():
                            if attribute_id in device_sensor_obj["capability"]:
                                # fetch user_command and configured_value
                                # from the request.
                                user_command = \
                                    device_sensor_obj[
                                        "capability"][
                                        attribute_id]["user_command"]
                                configured_value = value["configured_value"]
                                # make sure they are dictionary
                                if isinstance(configured_value, dict):
                                    # make sure configured_value is coherent
                                    # with expected keys.
                                    attribute_value_key = \
                                        settings.ATTRIBUTE_VALUE_KEYS.get(
                                            user_command)
                                    new_value = {}
                                    for value_key in attribute_value_key:
                                        # BUG ALERT: this can save some 
                                        # configured_value without all three
                                        # red, green, blue.
                                        if value_key in configured_value:
                                            # build capability updating object
                                            new_value.update({
                                                value_key: configured_value[
                                                    value_key]
                                            })
                                    # replace the configured_value in DB with
                                    # newly built configured value dict.
                                    device_sensor_obj["capability"][
                                        attribute_id][
                                        "configured_value"] = new_value
                                    # collating mqtt commands in a list.
                                    mqtt_commands.append((user_command,
                                                          device_euid,
                                                          new_value))
                            else:
                                api_log.error(
                                    "Device sensor  capability not found with "
                                    "_id: {}. Sending HTTP 404".format(
                                        attribute_id))
                                return Response({
                                    "capability": "Capability not supported"},
                                    status=status.HTTP_400_BAD_REQUEST)
                        api_log.debug("Saving device sensor data")
                        # saving Device Sensor with new configured_value
                        DeviceSensorSerializer(
                            DeviceSensor, data=device_sensor_obj).save_to_db()
                        api_log.debug(
                            "Device sensor edited. _id: {}.".format(
                                device_sensor_obj["_id"]))
                    except ValidationError as e:
                        api_log.error(
                            "Device sensor data validation failed: {}. Sending "
                            "response with HTTP 400".format(e.detail))
                        return Response(e.detail,
                                        status=status.HTTP_400_BAD_REQUEST)
            device_obj.update(device_new_data)
            api_log.debug("Saving device data")
            # device table updated.
            DeviceSerializer(Device, data=device_obj).save_to_db()
            # Sending all mqtt commands.
            for mqtt_command in mqtt_commands:
                api_log.debug(
                    "Requesting gateway for device configuration "
                    "change {}".format(mqtt_command))
                mqtt_publisher_func(*mqtt_command)
            api_log.debug("Device edited. _id: {}. Sending response with HTTP "
                          "200".format(device_obj["_id"]))
            return Response(device_obj, status=status.HTTP_200_OK)
        except ValidationError as e:
            # error handing for validating Device
            api_log.error("Device data validation failed: {}. Sending "
                          "response with HTTP 400".format(e.detail))
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # error handling for for all other errors
            api_log.critical("Request Failed. Sending HTTP 500", exc_info=True)
            return Response(e, status=HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def delete(request, resource_id=None):
        try:
            if not resource_id:
                return Response({
                    "device/<id>": [
                        "ID field is required in URL"
                    ]
                }, status=status.HTTP_400_BAD_REQUEST)
            # query for device. Needed to get a list of attached sensors.
            device_obj = Device.get_by_id(resource_id)
            # delete the device.
            device_deleted = Device.delete_by_id(resource_id)
            # stuff to do post deletion.
            if device_deleted > 0:
                # delete the device auth table for the respective device
                DeviceAuth.delete({'device_euid': device_obj["device_euid"]})
                api_log.debug("Device auth data deleted. Euid: {}".format(
                    device_obj["device_euid"]))
                # Delete the related sensors after deletion.
                DeviceSensor.delete({'device_euid': device_obj["device_euid"]})
                api_log.debug("Device sensor data deleted. Euid: {}".format(
                    device_obj["device_euid"]))
                # Make a Device Leave Request.
                GatewayCommands().device_leave(device_obj["device_euid"])
                api_log.debug("Requesting gateway to leaave device. Euid: {} "
                              "".format(device_obj["device_euid"]))
                api_log.info("Device deleted. _id: {}, Euid: {}. Sending HTTP "
                             "200".format(resource_id,
                                          device_obj["device_euid"]))
                return Response(status=status.HTTP_200_OK)
            api_log.debug("Device not found. _id: {}. Sending HTTP "
                          "404".format(resource_id))
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            api_log.critical("Request Failed. Sending HTTP 500", exc_info=True)
            return Response(e, status=HTTP_500_INTERNAL_SERVER_ERROR)


def validate_device_scan_request_post_data(request_data):
    """
        validates and parses request data for device join api.

        :param request_data : request data
        
        returns: 
        dictionary w/keys
            "gateway_list": list of strings, represnting gateway_euid s
            "interval": integer , representing seconds of duration.

    """
    from common.validations import gateway_mac_address_validator
    from common.db_models.gateway_models import Gateway

    # validate request.data to be a dictonary.
    if not isinstance(request_data, dict):
        raise Exception({
            "detail": "body shall be dictionary."
        })

    # fetch the required parameters
    interval = request_data.get('interval', 60)  # if no int, defailt to 60
    gateway = request_data.get('gateway_euid')
    # validate params.
    if not isinstance(interval, int):
        api_log.info("invalid interval: " + str(interval))
        api_log.info("responding 400 BAD REQUEST")
        raise Exception({"detail": "invalid interval"})

    if gateway and not gateway_mac_address_validator(gateway):
        api_log.info("invalid gateway: " + str(gateway))
        raise Exception({"detail": "invalid gateway"})

    if gateway:
        # check if the gateway exists in the gateway table or not.
        gateway_obj = Gateway.get(query={'gateway_euid': gateway.upper()})
        if not gateway_obj:
            api_log.info("gateway for device_join doesn't exist")
            raise Exception({"detail": "Provided gateway doesn't exist"})
        # Put that gateway euid in a list for return value
        gateway_list = [gateway]
    else:
        # get all gateways and put them in a list.
        gateway_list = map(lambda x: x["gateway_euid"], Gateway.all())

    # validated parameters returned
    return {
        'interval': interval,
        'gateway_euid_list': gateway_list
    }


def validate_device_scan_request_get_querystring(request_get):
    from common.validations import gateway_mac_address_validator

    gateway = request_get.get('gateway_euid', None)
    if gateway and not gateway_mac_address_validator(gateway):
        api_log.info("invalid gateway: " + str(gateway))
        raise Exception({"detail": "invalid gateway"})
    return gateway.upper()


class DeviceScanAPI(VRIoTAPIView):
    @staticmethod
    def get(request):
        try:
            gateway = validate_device_scan_request_get_querystring(request.GET)
        except Exception as e:
            return Response(e.args[0], status=status.HTTP_400_BAD_REQUEST)
        try:
            if gateway:
                # get devices pertaining to the gateway.
                devices = DeviceAuth.find(
                    query={
                        'discovered_mode': 0,
                        'gateway_euid': gateway
                    })
            else:
                # query DeviceAuth and return everything.
                devices = DeviceAuth.find(query={'discovered_mode': 0})

        except Exception as e:
            return Response(e.args,
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(devices, status=status.HTTP_200_OK)

    @staticmethod
    def post(request):
        ## IOTC -183
        ## This function needs to be moved to a View of its own.
        ## And, 
        try:
            valid_request = validate_device_scan_request_post_data(request.data)
        except Exception as e:
            return Response(e.args[0], status=status.HTTP_400_BAD_REQUEST)

        try:
            gateway_list = valid_request.get('gateway_euid_list', [])
            interval = valid_request['interval']
            for gateway in gateway_list:
                api_log.debug("called device_join: " + gateway + " " + str(
                    interval) + "Sec")
                GatewayCommands().device_join(gateway, duration=interval)
        except Exception as e:
            api_log.error("GatewayCommand raised an error.!")
            api_log.debug(e.args)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(status.HTTP_200_OK)


def mqtt_publisher_func(user_command, device_euid, configured_value):
    """
        This function shall be removed eventually and 
        DeviceOperation command shall be called directly.
    """
    if not DeviceOperation().device_mqtt_operation(
            user_command, device_euid, configured_value):
        return False
    return True
