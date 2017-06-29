from bson.objectid import ObjectId
from rest_framework import serializers


class PyMongoSerializer(serializers.Serializer):
    def create(self, validated_data):
        instance = self.get_model()
        db_obj = instance.save(validated_data)
        db_obj.update({"_id": str(db_obj.pop("_id"))})
        db_obj.pop("is_deleted")
        return db_obj

    def update(self, instance, validated_data):
        if "_id" in validated_data:
            validated_data.update({
                "_id": ObjectId(validated_data.pop("_id")),
            })
            db_obj = instance.save(validated_data)
            db_obj.update({"_id": str(db_obj.pop("_id"))})
            return db_obj
        return None

    def save_to_db(self):
        if self.is_valid(raise_exception=True):
            return self.save()


class BlankSerializer(serializers.Serializer):
    def create(self, validated_data):
        raise NotImplemented

    def update(self, instance, validated_data):
        raise NotImplemented
