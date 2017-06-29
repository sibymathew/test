from django.conf import settings
from django.core.management.base import BaseCommand

from common.db_models.device_serializers import SensorAttributeSerializer

mongo_log = settings.MONGO_LOGGER


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            self.sensor_attribute_defaults()
        except Exception as e:
            print(e)

    def sensor_attribute_defaults(self):
        try:
            mongo_log.debug("Inserting default documents to SensorAttributeDoc")
            db_data = {
                "attribute_command": "COLOR",
                "attribute_parameters": ["red", "blue", "green"],
                "attribute_parameters_value": {
                    "red": {"type": "int", "min": 0, "max": 255},
                    "blue": {"type": "int",
                             "min": 0, "max": 255},
                    "green": {"type": "int", "min": 0, "max": 255}
                },
                "user_command": "COLOR",
                "sensor_type": 0,
                "mqtt_command": ["LIGHT_MOVECOLOR"]
            }
            query = {
                "attribute_command": "COLOR",
                "sensor_type": 0,
            }
            self.insert_update(SensorAttributeSerializer, db_data, query)
            db_data = {
                "attribute_command": "BRIGHTNESS",
                "attribute_parameters": ['level'],
                "attribute_parameters_value": {
                    "level": {"type": "int", "min": 0, "max": 255}
                },
                "user_command": "BRIGHTNESS",
                "sensor_type": 0,
                "mqtt_command": ["LIGHT_BRIGHTNESS"]
            }
            query = {
                "attribute_command": "BRIGHTNESS",
                "sensor_type": 0,
            }
            self.insert_update(SensorAttributeSerializer, db_data, query)
            db_data = {
                "attribute_command": "ON_OFF",
                "attribute_parameters": ['on'],
                "attribute_parameters_value": {
                    "on": {"type": "int", "values": [0, 1]}
                },
                "user_command": 'STATE',
                "sensor_type": 0,
                "mqtt_command": ['OFF', 'ON']
            }
            query = {
                "attribute_command": "ON_OFF",
                "sensor_type": 0,
            }
            self.insert_update(SensorAttributeSerializer, db_data, query)
            db_data = {
                "attribute_command": "LOCK_STATE",
                "attribute_parameters": ['lock'],
                "attribute_parameters_value": {
                    "lock": {"type": "int", "values": [1, 2]}
                },
                "user_command": 'LOCK_STATE',
                "sensor_type": 1,
                "mqtt_command": ['DOOR_LOCK', 'DOOR_UNLOCK']
            }
            query = {
                "attribute_command": "LOCK_STATE",
                "sensor_type": 1,
            }
            self.insert_update(SensorAttributeSerializer, db_data, query)
        except Exception as e:
            raise e

    @staticmethod
    def insert_update(serializer, db_data, query):
        try:
            ser_obj = serializer(data=db_data)
            if ser_obj.is_valid(raise_exception=True):
                ser_obj.get_model().update(
                    query=query,
                    update_fields=db_data,
                    upsert=True
                )
        except Exception as e:
            raise e
