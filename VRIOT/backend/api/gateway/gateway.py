import json

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.device.device import DeviceAPI
from common.api import VRIoTAPIView
from common.db_models.device_models import Device
from common.db_models.gateway_models import Gateway
from common.db_models.gateway_serializers import GatewaySerializer
from services.integration.mqtt.publish_functions import \
    GatewayCommands

api_log = settings.VRIOT_LOGGER


class GatewayAPI(VRIoTAPIView):
    def __init__(self):
        super().__init__()

    @staticmethod
    def get(request, resource_id=None):
        try:
            # self.authenticate_request(request)
            gateway_objs = []
            # Checking if requested for specific resource id
            if resource_id:
                api_log.debug("Querying for gateway _id: {}".format(
                    resource_id))
                gateway_obj = Gateway.get_by_id(resource_id)
                if gateway_obj:
                    gateway_objs = gateway_obj
            else:
                api_log.debug("Querying for all gateways")
                gateway_objs = Gateway.all()
            if not gateway_objs:
                api_log.debug("Gateway(s) not found. Sending HTTP 404")
                return Response(status=status.HTTP_404_NOT_FOUND)
            api_log.debug("Gateway(s) found. Sending response with HTTP 200")
            return Response(gateway_objs, status=status.HTTP_200_OK)
        except Exception as e:
            api_log.critical("Request Failed. Sending HTTP 500",
                             exc_info=True)
            return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def post(request):
        try:
            # self.authenticate_request(request)
            post_body = json.loads(request.body.decode())
            gateway_euid = post_body.get("gateway_euid")
            gateway_name = post_body.get("gateway_name")
            gateway_tags = post_body.get("tags", [])
            gateway_obj = Gateway.get(query={
                "gateway_euid": gateway_euid})
            if not gateway_obj:
                api_log.debug("Processing gateway data")
                gateway_data = {
                    "gateway_name": gateway_name,
                    "gateway_euid": gateway_euid,
                    "gateway_state": 0,
                    "tags": gateway_tags,
                    "is_enabled": False
                }
                api_log.debug("Saving gateway data")
                gateway_obj = GatewaySerializer(
                    data=gateway_data).save_to_db()
                api_log.debug("Requesting gateway for settings")
                GatewayCommands().gateway_settings(
                    gateway_euid)
                api_log.info("Gateway added. _id: {}. Sending response with "
                             "HTTP 201".format(gateway_obj["_id"]))
                return Response(gateway_obj, status=status.HTTP_201_CREATED)
            api_log.debug("Gateway exists. _id: {}. Sending response with "
                          "HTTP 409".format(gateway_obj["_id"]))
            return Response(gateway_obj, status=status.HTTP_409_CONFLICT)
        except ValidationError as e:
            api_log.error("Gateway data validation failed: {}. Sending "
                          "response with HTTP 400".format(e.detail))
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            api_log.critical("Request Failed. Sending HTTP 500",
                             exc_info=True)
            return Response(str(e),
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def patch(request, resource_id=None):
        try:
            if not resource_id:
                return Response({
                    "gateway/<id>": [
                        "ID field is required in URL"
                    ]
                }, status=status.HTTP_400_BAD_REQUEST)
            # self.authenticate_request(request)
            post_body = json.loads(request.body.decode())
            gateway_name = post_body.get("gateway_name")
            gateway_tags = post_body.get("tags", [])
            gateway_obj = Gateway.get_by_id(resource_id)
            if gateway_obj:
                api_log.debug("Processing gateway data")
                if gateway_name:
                    gateway_obj.update({"gateway_name": gateway_name})
                if gateway_tags:
                    gateway_obj.update({"tags": gateway_tags})
                gateway_obj = GatewaySerializer(
                    Gateway, data=gateway_obj).save_to_db()
                api_log.info("Gateway edited. _id: {}. Sending response "
                             "with HTTP 200".format(resource_id))
                return Response(gateway_obj, status=status.HTTP_200_OK)
            api_log.error("Gateway not found. _id: {}. Sending HTTP "
                          "404".format(resource_id))
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            api_log.error("Gateway data validation failed: {}. Sending "
                          "response with HTTP 400".format(e.detail))
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            api_log.critical("Request Failed. Sending HTTP 500",
                             exc_info=True)
            return Response(str(e),
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def delete(request, resource_id=None):
        try:
            if not resource_id:
                return Response({
                    "resource_id": [
                        "This field is required in URL"
                    ]
                }, status=status.HTTP_400_BAD_REQUEST)
            # self.authenticate_request(request)
            gateway_obj = Gateway.get_by_id(resource_id)
            if gateway_obj:
                # delete device from gateway
                device_objs = Device.find(query={"gateway_euid": gateway_obj[
                    "gateway_euid"]})
                if device_objs:
                    for device_obj in device_objs:
                        DeviceAPI().delete(None, device_obj["_id"])
                gateway_delete = Gateway.delete_by_id(resource_id)
                if gateway_delete > 0:
                    api_log.info("Gateway deleted. _id: {}. Sending HTTP "
                                 "200".format(resource_id))
                    return Response(status=status.HTTP_200_OK)
            else:
                api_log.debug("Gateway not found. _id: {}. Sending HTTP "
                              "404".format(resource_id))
                return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            api_log.critical("Request Failed. Sending HTTP 500",
                             exc_info=True)
            return Response(str(e),
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
