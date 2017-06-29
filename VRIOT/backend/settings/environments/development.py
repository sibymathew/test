from settings.environments.services import *

ENVIRONMENT = "development"

CELERY_BROKER_URL = "amqp://vriotclient:vriot123@" + AMQP_HOST

CONNECTIONS = {}

AA_VISIONLINE_CONF = {
    "host": VISIONLINE_SERVER,
    "path": "/api/v1",
    "secure": True,
    "user": "sym",
    "password": "sym"
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/tmp/django_cache',
    }
}

AA_CACHE_KEY = "aa_visionline_session"
