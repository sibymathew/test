from flask import Flask
from flask import request, Response
import logging
from logging.handlers import RotatingFileHandler
import os


LOG_PATH = "/var/log/sync.log"
log_hdlr = logging.getLogger(__name__)
log_hdlr.setLevel(logging.DEBUG)

hdlr = RotatingFileHandler(LOG_PATH,maxBytes=5 * 1024 * 1024, backupCount=20)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
hdlr.setFormatter(formatter)
log_hdlr.addHandler(hdlr)

app = Flask(__name__)

TOKEN = os.getenv("BE_TOK", None)

#On-Demand UUID
try:
    with open("/etc/yconfig.json", "r") as hdlr:
        content = json.loads(hdlr.read())

        if "event_details" in content:
            events = content["event_details"]

            if events:
                for event in events:
                    if event["event_name"] == "On-Demand":
                        on_demand_uuid = event["event_uuid"]
            else:
            	on_demand_uuid = None
except Exception as err:
    log_hdlr.info("Read On-Demand Event Failed: {}".format(err))

@app.route("/v1/on-demand/request", methods = ['POST'])
def fe_request():
    try:
    	REQ_TOKEN = request.headers["AUTH_TOKEN"]
    	if REQ_TOKEN == TOKEN:
    		if on_demand_uuid:
    			#Check if already in-progress
    			raise Exception("Previous On-Demand Request is in-progress")
    			#Add in Notification DB
    			msg = "Added On-Demand to Edge Notification DB"
    		else:
    			raise Exception("On-Demand UUID is not part of configuration")
    	else:
    		raise Exception("Invalid Token")

        resp = get_config_data(req["edge_mac"], req["version"])
    except Exception as err:
        log_hdlr.info("{} {} \n {} \n".format(err))
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