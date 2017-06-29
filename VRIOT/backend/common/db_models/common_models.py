import datetime

import pymongo
from bson.objectid import ObjectId
from django.conf import settings
from pymongo.errors import CollectionInvalid, OperationFailure
from pymongo.mongo_client import MongoClient


class DBModel(object):
    _collection = None
    meta = {}

    def __new__(cls):
        cls._db_object = None
        cls._db = None
        cls._meta = cls.meta
        cls._collection = cls._get_collection()

    @staticmethod
    def _init_db_conn():
        env = settings.ENVIRONMENT
        db_conf = settings.NOSQL_DATABASES[env]
        db_client = MongoClient(db_conf["host"],
                                db_conf["port"],
                                connect=False,
                                maxPoolSize=db_conf["connection_pool"])
        db_object = db_client[db_conf["db"]]
        return db_object

    @classmethod
    def _get_db_object(cls):
        if not settings.CONNECTIONS.get("db"):
            settings.CONNECTIONS["db"] = cls._init_db_conn()
        return settings.CONNECTIONS["db"]

    @classmethod
    def _build_index_spec(cls):
        index_models = []
        for index in cls.meta["indexes"]:
            index_name = index[1:]
            index_type = pymongo.ASCENDING
            if index.startswith("-"):
                index_type = pymongo.DESCENDING
            elif index.startswith("$"):
                index_type = pymongo.TEXT
            elif index.startswith("#"):
                index_type = pymongo.HASHED
            elif index.startswith("("):
                index_type = pymongo.GEOSPHERE
            elif index.startswith(")"):
                index_type = pymongo.GEOHAYSTACK
            elif index.startswith("*"):
                index_type = pymongo.GEO2D
            index_models.append((index_name, index_type))
        return index_models

    @classmethod
    def _get_collection(cls):
        try:
            cls._db_object = cls._get_db_object()
            collection_name = cls.meta.get("collection")
            if collection_name in cls._db_object.collection_names():
                collection = cls._db_object[collection_name]
                return collection
            """
            If collection not present in the db then create the
            collection and return the collection object.
            """
            try:
                collection = cls._db_object.create_collection(
                    collection_name)
                if cls.meta.get('auto_create_index', True):
                    if cls.meta.get('indexes'):
                        indexes = cls._build_index_spec()
                        collection.create_index(indexes,
                                                background=cls.meta.get(
                                                    "index_background",
                                                    True))
            except (CollectionInvalid, OperationFailure):
                """
                This condition appears when two threads try to create the
                collection in parallel. in such cases return the collection
                object.
                """
                collection = cls._db_object[collection_name]
            return collection
        except Exception:
            return None

    @classmethod
    def get(cls, query=None):
        cls.__new__(cls)
        if query is None:
            query = dict()
        query.update({"is_deleted": False})
        return cls._collection.find_one(query)

    @classmethod
    def get_by_id(cls, _id):
        cls.__new__(cls)
        return cls.get({"_id": ObjectId(_id)})

    @classmethod
    def find(cls, query=None):
        cls.__new__(cls)
        if query is None:
            query = dict()
        query.update({"is_deleted": False})
        return cls._collection.find(query)

    @classmethod
    def all(cls):
        cls.__new__(cls)
        return cls.find()

    @classmethod
    def create(cls, document):
        cls.__new__(cls)
        document.update({
            "created_on": datetime.datetime.utcnow(),
            "is_deleted": False
        })
        result = cls._collection.insert_one(document)
        document.update({"_id": result.inserted_id})
        return result.inserted_id

    @classmethod
    def create_bulk(cls, documents):
        cls.__new__(cls)
        for document in documents:
            document.update({"created_on": datetime.datetime.utcnow()})
        result = cls._collection.insert_many(documents)
        for i, obj_id in enumerate(result.inserted_ids):
            documents[i].update({"_id": obj_id})
        return result.inserted_ids

    @classmethod
    def update(cls, query=None, update_fields=None, **kwargs):
        cls.__new__(cls)
        if query is None:
            query = dict()
        if update_fields is None:
            update_fields = dict()
        query.update({"is_deleted": False})
        update_fields.update({"updated_on": datetime.datetime.utcnow()})
        result = cls._collection.update_one(
            query, {"$set": update_fields, "$setOnInsert": {
                "created_on": datetime.datetime.utcnow()}}, **kwargs)
        return result.modified_count

    @classmethod
    def update_bulk(cls, query, update_fields, **kwargs):
        cls.__new__(cls)
        if query is None:
            query = dict()
        if update_fields is None:
            update_fields = dict()
        query.update({"is_deleted": False})
        update_fields.update({"updated_on": datetime.datetime.utcnow()})
        result = cls._collection.update_many(
            query, {"$set": update_fields, "$setOnInsert": {
                "created_on": datetime.datetime.utcnow()}}, **kwargs)
        return result.modified_count

    @classmethod
    def delete(cls, query=None, updated_fields=None, hard_delete=False):
        cls.__new__(cls)
        if query is None:
            return False
        db_update_fields = {"is_deleted": True}
        if updated_fields:
            db_update_fields.update(updated_fields)
        if hard_delete:
            result = cls._collection.delete_one(query)
            return result.deleted_count
        result = cls.update(query, db_update_fields)
        return result

    @classmethod
    def delete_by_id(cls, _id):
        cls.__new__(cls)
        result = cls.delete({"_id": ObjectId(_id)})
        return result

    @classmethod
    def delete_bulk(cls, query, updated_fields=None, hard_delete=False):
        cls.__new__(cls)
        if query is None:
            return False
        db_update_fields = {"is_deleted": True}
        if updated_fields:
            db_update_fields.update(updated_fields)
        if hard_delete:
            result = cls._collection.delete_many(query)
            return result.deleted_count
        result = cls.update_bulk(query, db_update_fields)
        return result

    @classmethod
    def count(cls, cursor):
        return cursor.count()

    @classmethod
    def save(cls, document):
        if "_id" in document:
            cls.update({"_id": document["_id"]}, document)
        else:
            cls.create(document)
        return document

    @classmethod
    def _convert_id(cls, documents, to_object_id=False):
        if not isinstance(documents, list):
            if to_object_id:
                documents["_id"] = ObjectId(documents["_id"])
            else:
                documents["_id"] = str(documents["_id"])
        else:
            for document in documents:
                if to_object_id:
                    document["_id"] = ObjectId(document["_id"])
                else:
                    document["_id"] = str(document["_id"])

    @classmethod
    def _return_serialized_data(cls, *args, **kwargs):
        raise NotImplemented


class SerializedDBModel(DBModel):
    @classmethod
    def get(cls, query=None):
        db_obj = super().get(query=query)
        if db_obj:
            cls._convert_id(db_obj)
            return cls._return_serialized_data(db_obj)
        return None

    @classmethod
    def get_by_id(cls, _id):
        db_obj = super().get_by_id(_id)
        if db_obj:
            cls._convert_id(db_obj)
            return cls._return_serialized_data(db_obj)
        return None

    @classmethod
    def all(cls):
        db_objs = list(super().all())
        if db_objs:
            cls._convert_id(db_objs)
            return cls._return_serialized_data(db_objs, many=True)
        return None

    @classmethod
    def find(cls, query=None):
        db_obj = super().find(query=query)
        if db_obj:
            # OPTIMIZATION needed. putting a pymongo cursor into a list.
            db_obj_list = list(db_obj)
            cls._convert_id(db_obj_list)
            return cls._return_serialized_data(db_obj_list, many=True)
        return None

    @classmethod
    def delete(cls, query=None, updated_fields=None, hard_delete=False):
        if query is None:
            return False
        updated_fields = {"is_enabled": False}
        return super().delete(query, updated_fields=updated_fields,
                              hard_delete=hard_delete)
