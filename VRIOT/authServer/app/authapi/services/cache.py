from ..services import Service

class Cache(metaclass=Service):
    # Idea is to have a redis cache in future here.
    def __init__(self):
        # until redis is implemented, cache is stored in this variable.
        self.cache = {}

    def get(self,key):
        return self.cache.get(key)

    def add(self,key,value):
        # Key must be a string.
        self.cache[key]=value

    def remove(self,key):
        if key in self.cache:
            del self.cache[key]

