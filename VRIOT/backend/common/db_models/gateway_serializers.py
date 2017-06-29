from rest_framework import serializers

from common.db_models.common_serializers import BlankSerializer, \
    PyMongoSerializer
from common.db_models.gateway_models import Gateway
from common.validations import name_basic_validator, \
    gateway_mac_address_validator, device_mac_address_validator, tags_validator


class GatewayIPNetwork(BlankSerializer):
    ip = serializers.IPAddressField(required=True)
    gateway = serializers.IPAddressField(required=False, allow_blank=True)
    netmask = serializers.IPAddressField(required=False, allow_blank=True)
    mac = serializers.CharField(required=True)
    dns = serializers.ListField(required=False)

    @staticmethod
    def validate_mac(value):
        if not gateway_mac_address_validator(value):
            raise serializers.ValidationError("Interface MAC Address Invalid")
        return value.upper()


class GatewayDiagnostics(BlankSerializer):
    network_type = serializers.CharField(required=True)
    interface_name = serializers.CharField(required=False)
    memory_usage = serializers.CharField(required=False)
    cpu_usage = serializers.CharField(required=False)
    network_stack = serializers.CharField(required=False)
    network_stack_ver = serializers.CharField(required=False)
    ap_up_time = serializers.CharField(required=False)
    gateway_up_time = serializers.CharField(required=False)
    mqtt_qos = serializers.CharField(required=False)


class GatewayDiagnostics(BlankSerializer):
    network_type = serializers.CharField(required=True)
    interface_name = serializers.CharField(required=False)
    memory_usage = serializers.CharField(required=False)
    cpu_usage = serializers.CharField(required=False)
    network_stack = serializers.CharField(required=False)
    network_stack_ver = serializers.CharField(required=False)
    ap_up_time = serializers.CharField(required=False)
    gateway_up_time = serializers.CharField(required=False)
    mqtt_qos = serializers.CharField(required=False)


class GatewayIoTNetwork(BlankSerializer):
    network_type = serializers.CharField(required=True)
    set_radio_tx_power = serializers.CharField(required=True)
    get_radio_tx_power = serializers.CharField(required=True)
    set_radio_channel = serializers.CharField(required=True)
    get_radio_channel = serializers.CharField(required=True)
    network_mac = serializers.CharField(required=True)
    network_id = serializers.CharField(required=True)

    @staticmethod
    def validate_network_mac(value):
        if not device_mac_address_validator(value):
            raise serializers.ValidationError("Device MAC Address Invalid")
        return value.upper()


class GatewaySerializer(PyMongoSerializer):
    """
    use .save() to save data to DB
    use .data() to get the serialized data
    """
    _id = serializers.CharField(required=False)
    gateway_euid = serializers.CharField(required=False)
    gateway_name = serializers.CharField(required=False)
    tags = serializers.ListField(required=False)
    gateway_ip_networks = serializers.ListField(required=False)
    gateway_iot_network_mode = serializers.IntegerField(required=False)
    gateway_iot_networks = serializers.ListField(required=False)
    gateway_state = serializers.IntegerField(required=False)
    gateway_device_list = serializers.ListField(required=False)
    is_enabled = serializers.BooleanField(required=False)
    created_on = serializers.DateTimeField(required=False)
    updated_on = serializers.DateTimeField(required=False)
    gateway_diagnostics = serializers.ListField(required=False)

    @staticmethod
    def get_model():
        return Gateway

    @staticmethod
    def validate_gateway_euid(value):
        if not gateway_mac_address_validator(value):
            raise serializers.ValidationError("Gateway EUID Invalid")
        return value.upper()

    @staticmethod
    def validate_gateway_name(value):
        if not name_basic_validator(value):
            raise serializers.ValidationError("Gateway Name is Invalid")
        return value

    @staticmethod
    def validate_tags(value):
        if not tags_validator(value):
            raise serializers.ValidationError("Invalid Tag(s) Entered")
        return value

    @staticmethod
    def validate_gateway_ip_networks(value):
        if not GatewayIPNetwork(data=value, many=True).is_valid(
                raise_exception=True):
            raise serializers.ValidationError("Gateway IP network data is "
                                              "invalid")
        return value

    @staticmethod
    def validate_gateway_iot_networks(value):
        if not GatewayIoTNetwork(data=value, many=True).is_valid(
                raise_exception=True):
            raise serializers.ValidationError("Gateway IoT network data "
                                              "is invalid")
        return value

    @staticmethod
    def validate_gateway_diagnostics(value):
        if not GatewayDiagnostics(data=value, many=True).is_valid(
                raise_exception=True):
            raise serializers.ValidationError("Gateway diagnostics data "
                                              "is invalid")
        return value
