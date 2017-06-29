from kombu import Queue, Exchange

from settings.environments.default import *

NOSQL_DATABASES = {
    "development": {
        "db": "vriot_dev_db",
        "host": DB_HOST,
        "port": 27017,
        "connection_pool": 32
    },
    "staging": {},
    "production": {},
    "common": {
        "engine": "mongo"
    }
}

MQTT_SETTINGS = {
    "development": {
        "host": MQTT_HOST,
        "port": 1883,
        "secure_port": 8883,
        'ca_cert': '/cafiles/ca.crt'
    },
    "staging": {},
    "production": {},
    "common": {
        "topics": [
            ("gateway/#", 1),
            # ("controller/#", 1),
        ]
    },
    "assaabloy": {
        "subtopics": [
            ("AA_gateway/device/function/attribute", 1),
        ],
        "pubtopics": [
            ("AA_controller/gateway/device/commands", 1),
        ],
    }
}

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_DEFAULT_QUEUE = 'default'
CELERY_DEFAULT_EXCHANGE_TYPE = 'direct'
CELERY_DEFAULT_ROUTING_KEY = 'default'
CELERY_QUEUES = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('mqtt_normal', Exchange('mqtt_normal'),
          routing_key='mqtt_normal'),
    Queue('mqtt_priority', Exchange('mqtt_priority'),
          routing_key='mqtt_priority'),
)
