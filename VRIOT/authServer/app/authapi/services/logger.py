from ..services import Service


class Logger(metaclass=Service):

    def __init__(self):
        import logging 
        self.loggerProfiles={}
        defaultLog = logging.getLogger('default')
        defaultHandler = logging.FileHandler('../logs/defaultLogs.txt')
        defaultHandler.setLevel(logging.INFO)
        defaultHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s'))
        defaultLog.addHandler(defaultHandler)
        self.loggerProfiles['default'] = defaultLog

    def log(message,profile='default'):
        self.loggerProfiles[profile].log(message)

    def createLoggerProfile():
        # creating a non default logger profilewith different level
        # puts the logger in the dict.
        pass


