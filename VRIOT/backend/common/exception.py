import logging

logger = logging.getLogger(name="django")


class VRIoTException(Exception):
    def __init__(self, msg):
        super(VRIoTException, self).__init__()
        self.msg = msg
        logger.error(msg)
