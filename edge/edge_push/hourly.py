from edge_loader import get_motor_data, ingest_hourly_stream
import time
import ast
import logging
import json
from logging.handlers import RotatingFileHandler

LOG_PATH = "/var/log/push.log"
log_hdlr = logging.getLogger(__name__)
log_hdlr.setLevel(logging.DEBUG)

hdlr = RotatingFileHandler(LOG_PATH,maxBytes=5 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
hdlr.setFormatter(formatter)
log_hdlr.addHandler(hdlr)

#in milliseconds
__PULL_INTERVAL__ = 1000

try:
    with open("/etc/yconfig.json", "r") as hdlr:
        config = json.loads(hdlr.read())
        config_content = json.loads(content["config_data"])
        crane_weight = config_content["crane_details"]["total_crane_weight"]
except:
    log_hdlr.info("Hourly Push: Configuration JSON or Crane Weight is Missing")
else:
    try:
        to_time = round(time.time() * 1000)
        from_time = to_time - 3600000
        ingest_hourly_stream(from_time, to_time, crane_weight, __PULL_INTERVAL__/1000)
    except Exception as err:
        log_hdlr.info("Hourly Push Exception: {}".format(err))
