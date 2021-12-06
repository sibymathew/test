from flask import Flask
from flask import request, Response
import logging
from logging.handlers import RotatingFileHandler
from edge_loader import ingest_notifications, get_notify_data
import os
import time
import json
import ast


LOG_PATH = "/var/log/sync.log"
log_hdlr = logging.getLogger(__name__)
log_hdlr.setLevel(logging.DEBUG)

hdlr = RotatingFileHandler(LOG_PATH,maxBytes=5 * 1024 * 1024, backupCount=20)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
hdlr.setFormatter(formatter)
log_hdlr.addHandler(hdlr)

app = Flask(__name__)

TOKEN = os.getenv("BE_TOK", None)

@app.route("/v1/on-demand/request", methods = ['POST'])
def fe_request():
    #On-Demand UUID
    try:
        notify_json = {}
        with open("/etc/yconfig.json", "r") as hdlr:
            content = json.loads(hdlr.read())

            notify_json["edge_uuid"] = content["edge_uuid"]
            # As this event is global event, motor_uuid is replaced with edge_uuid
            notify_json["motor_uuid"] = content["edge_uuid"]
            notify_json["event_name"] = "On-Demand"
            notify_json["event_action"] = 2
            notify_json["event_uuid"] = None
            if "event_details" in content:
                events = content["event_details"]

                if events:
                    for event in events:
                        if event["event_name"] == "On-Demand":
                            notify_json["event_uuid"] = event["event_uuid"]

                            """if "motor_uuid" in event:
                                notify_json["motor_uuid"] = event["motor_uuid"]
                            else:
                                notify_json["motor_uuid"] = None

                            notify_json["event_action"] = 0
                            for action in event["event_action"]:
                                # Send Email
                                if action == 1:
                                    notify_json["event_action"] += 1
                                # Send Data to Cloud
                                if action == 2:
                                    notify_json["event_action"] += 2"""
    except Exception as err:
        log_hdlr.info("Read On-Demand Event Failed: {}".format(err))

    try:
        REQ_TOKEN = request.headers["AUTH_TOKEN"]
        if REQ_TOKEN == TOKEN:
            if notify_json["event_uuid"]:
                #Check if already in-progress
                active_notifications = get_notify_data([notify_json["motor_uuid"]], 30)

                for notifications in ast.literal_eval(active_notifications):
                    notification = json.loads(notifications)
                    if notify_json["event_uuid"] == notification["event_uuid"]:
                        raise Exception("Previous On-Demand Request is in-progress")

                #Add in Notification DB
                msg = "Added On-Demand to Edge Notification DB"
                notify_json["created_on"] = round(time.time() * 1000)
                notify_json["action_status"] = False
                ingest_notifications(notify_json)
            else:
                raise Exception("On-Demand UUID is not part of configuration")
        else:
            raise Exception("Invalid Token")

    except Exception as err:
        err = str(err)
        log_hdlr.info("{}".format(err))
        if err == "Invalid Token":
            return Response(response=json.dumps({"status": 0, "msg": err}), status=401)
        elif err == "On-Demand UUID is not part of configuration":
            return Response(response=json.dumps({"status": 0, "msg": err}), status=404)
        elif err == "Previous On-Demand Request is in-progress":
            return Response(response=json.dumps({"status": 0, "msg": err}), status=409)
        else:
            return Response(response=json.dumps({"status": 0, "msg": err}), status=400)
    else:
        log_hdlr.info(msg)
        return Response(response=json.dumps({"status": 0, "msg": msg}), status=200)

if __name__ == '__main__':
   app.run(host="0.0.0.0", port=9993, debug = True)