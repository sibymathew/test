from edge_loader import ingest_hourly_stream
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
        config_content = json.loads(config["config_data"])
        crane_weight = config_content["crane_details"]["total_crane_weight"]

        #Get the motor_uuid where load cell is configured
        for mapping in config_content["crane_details"]["vfd_mapping"]
            if 'loadcell' in mapping:
                motor_uuid = mapping["vfd_motor_mapping"][0]
except:
    log_hdlr.info("Hourly Push: Configuration JSON or Crane Weight is Missing")
else:
    try:
        to_time = round(time.time() * 1000)
        from_time = to_time - 3600000
        interval = int(__PULL_INTERVAL__/1000)
        log_hdlr.info("Hourly is called {} {} {} {} {}".format(from_time, to_time, crane_weight, interval, motor_uuid))
        resp = ingest_hourly_stream(from_time, to_time, crane_weight, interval, motor_uuid)
        log_hdlr.info("Hourly Data: {}".format(resp))
    except Exception as err:
        log_hdlr.info("Hourly Push Exception: {}".format(err))
