from .services.db import DB
from .services.cache import Cache

DB()
Cache() # initiates Cache and creates a singleton.