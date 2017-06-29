from common.db_models.common_models import SerializedDBModel


class Device(SerializedDBModel):
    meta = {
        "collection": "device",
        "indexes": [
            "#device_euid"
        ]
    }

    @classmethod
    def get_capability_info(cls, device_obj):
        if "device_sensor" in device_obj:
            for sensor in device_obj["device_sensor"]:
                sensor_obj = DeviceSensor.get_by_id(
                    sensor["sensor_id"])
                if sensor_obj:
                    sensor["capability"] = sensor_obj["capability"]

    @classmethod
    def _return_serialized_data(cls, document, many=False):
        from common.db_models.device_serializers import DeviceSerializer
        db_obj = DeviceSerializer(data=document, many=many)
        db_obj.is_valid(raise_exception=True)
        return db_obj.data


class DeviceSensor(SerializedDBModel):
    meta = {
        "collection": "device_sensor",
        "indexes": [
            "#device_euid"
        ]
    }

    @classmethod
    def _return_serialized_data(cls, document, many=False):
        from common.db_models.device_serializers import \
            DeviceSensorSerializer
        db_obj = DeviceSensorSerializer(data=document, many=many)
        db_obj.is_valid(raise_exception=True)
        return db_obj.data


class SensorAttribute(SerializedDBModel):
    meta = {
        "collection": "sensor_attribute",
    }

    @classmethod
    def _return_serialized_data(cls, document, many=False):
        from common.db_models.device_serializers import \
            SensorAttributeSerializer
        db_obj = SensorAttributeSerializer(data=document, many=many)
        db_obj.is_valid(raise_exception=True)
        return db_obj.data


class DeviceAuth(SerializedDBModel):
    meta = {
        "collection": "device_auth",
        "indexes": [
            "#device_euid"
        ]
    }

    @classmethod
    def _return_serialized_data(cls, document, many=False):
        from common.db_models.device_serializers import \
            DeviceAuthSerializer
        db_obj = DeviceAuthSerializer(data=document, many=many)
        db_obj.is_valid(raise_exception=True)
        return db_obj.data
