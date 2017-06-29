from rest_framework import serializers

from common.db_models.common_serializers import PyMongoSerializer, \
    BlankSerializer
from common.db_models.device_models import DeviceAuth, Device, \
    DeviceSensor, SensorAttribute
from common.validations import device_mac_address_validator, \
    gateway_mac_address_validator, tags_validator, name_basic_validator


class DeviceSerializer(PyMongoSerializer):
    """
    This Serializer is for Thing information
    """
    _id = serializers.CharField(required=False)
    device_euid = serializers.CharField(required=False)
    gateway_euid = serializers.CharField(required=False)
    device_name = serializers.CharField(required=False)
    device_type = serializers.IntegerField(required=False)
    tags = serializers.ListField(required=False)
    network_type = serializers.IntegerField(required=False)
    is_enabled = serializers.BooleanField(required=False)
    device_sensor = serializers.ListField(required=False)
    association_mode = serializers.IntegerField(required=False, default=0)
    # manufacturer = serializers.CharField(required=False)
    # brand = serializers.CharField(required=False)
    # gateway_pri = IntField(required=True)
    # gateway_sec = IntField()
    # gateway_lock = BooleanField()
    # association_mode  = serializers.IntegerField(required=False)
    #  min=0,max=2,req=True,def=1
    # power_mode = serializers.IntegerField(required=False)
    # battery_level = serializers.IntegerField(required=False)

    @staticmethod
    def get_model():
        return Device

    @staticmethod
    def validate_device_name(value):
        if not name_basic_validator(value):
            raise serializers.ValidationError("Device Name Invalid")
        return value

    @staticmethod
    def validate_device_euid(value):
        if not device_mac_address_validator(value):
            raise serializers.ValidationError("Device EUID Invalid")
        return value.upper()

    @staticmethod
    def validate_gateway_euid(value):
        if not gateway_mac_address_validator(value):
            raise serializers.ValidationError("Gateway EUID Invalid")
        return value.upper()

    @staticmethod
    def validate_tags(value):
        if not tags_validator(value):
            raise serializers.ValidationError("Invalid Tag(s) Entered")
        return value


class DeviceSensorCapability(BlankSerializer):
    attribute_id = serializers.CharField(required=False)
    user_command = serializers.CharField(required=False)
    attribute_parameters_value = serializers.ListField(required=False)
    reported_on = serializers.DateTimeField(required=False)
    reported_value = serializers.DictField(required=False)
    configured_value = serializers.DictField(required=False)

    @staticmethod
    def validate_configured_value(values):
        for key, value in values.items():
            # BUG ALERT: Will need more validation based on whether 
            # key is parts of attribute_keys_dict

            # currently checking only for whether the value is int
            # or not. Might not be even int in future.
            if not isinstance(value, int):
                raise serializers.ValidationError("{}: Only int "
                                                  "accepted".format(key))
        return values

    @staticmethod
    def validate_reported_value(values):
        for key, value in values.items():
            if not isinstance(value, int):
                raise serializers.ValidationError("{}: Only int "
                                                  "accepted".format(key))
        return values


class DeviceSensorSerializer(PyMongoSerializer):
    """
    This Serializer is for Thing information
    """
    _id = serializers.CharField(required=False)
    device_id = serializers.CharField(required=False)
    device_euid = serializers.CharField(required=False)
    sensor_type = serializers.IntegerField(required=False)
    function_id = serializers.CharField(required=False, default="0x0001")
    capability = serializers.DictField(required=False)

    @staticmethod
    def get_model():
        return DeviceSensor

    @staticmethod
    def validate_capability(values):
        for key, value in values.items():
            if not DeviceSensorCapability(data=value).is_valid(
                    raise_exception=True):
                raise serializers.ValidationError("Capability data is "
                                                  "invalid")
        return values

    @staticmethod
    def validate_device_euid(value):
        if not device_mac_address_validator(value):
            raise serializers.ValidationError("Device EUID Invalid")
        return value.upper()


class SensorAttributeSerializer(PyMongoSerializer):
    """
    This Serializer is for Thing information
    """
    _id = serializers.CharField(required=False)
    attribute_command = serializers.CharField(required=False)
    attribute_parameters = serializers.ListField(required=False, default=[])
    attribute_parameters_value = serializers.DictField(required=False,
                                                       default={})
    user_command = serializers.CharField(required=False)
    sensor_type = serializers.IntegerField(required=False)
    mqtt_command = serializers.ListField(required=False)

    @staticmethod
    def get_model():
        return SensorAttribute


class DeviceAuthSerializer(PyMongoSerializer):
    """
    This Serializer is for Thing Authentication information
    """
    _id = serializers.CharField(required=False)
    device_euid = serializers.CharField(required=False)
    gateway_euid = serializers.CharField(required=False)
    is_blacklisted = serializers.BooleanField(required=False)
    state = serializers.IntegerField(required=False)
    discovered_mode = serializers.IntegerField(required=False)
    is_user_allowed = serializers.BooleanField(required=False)

    @staticmethod
    def get_model():
        return DeviceAuth

    @staticmethod
    def validate_device_euid(value):
        if not device_mac_address_validator(value):
            raise serializers.ValidationError("Device EUID Invalid")
        return value.upper()

    @staticmethod
    def validate_gateway_euid(value):
        if not gateway_mac_address_validator(value):
            raise serializers.ValidationError("Gateway EUID Invalid")
        return value.upper()
