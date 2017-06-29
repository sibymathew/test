
class Service(type):
	# Service is a singleton class where all instances of services 
	# are stored in this class variable.
	# All calls are delegated to this. And, only one instance of a 
	# class is available throughout the code.
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Service, cls).__call__(*args, **kwargs)
        return cls._instances[cls]