from mongoengine import *
from baseapp.settings import MONGODB_SETTINGS
from baseapp.settings import DB_ENV
from ..services import Service


class DB(metaclass=Service):
    def __init__(self,):
        self.connection = connect('try',
            host=MONGODB_SETTINGS[DB_ENV]['host'],
            port=MONGODB_SETTINGS[DB_ENV]['port']
            )

