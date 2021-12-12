from edge_loader import check_rules, ingest_notifications
import time
import ast

LOG_PATH = "/var/log/sync.log"
log_hdlr = logging.getLogger(__name__)
log_hdlr.setLevel(logging.DEBUG)

hdlr = RotatingFileHandler(LOG_PATH,maxBytes=5 * 1024 * 1024, backupCount=20)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
hdlr.setFormatter(formatter)
log_hdlr.addHandler(hdlr)

# Rule Check Interval
SLEEP = 5

def rules_check(edge_uuid, rules, rules_md):
    while True:
    	log_hdlr.info("Rules to be checked are: {}".format(rules))
    	triggered_rules = None
    	check_time = round(time.time() * 1000)
        triggered_rules = check_rules(rules)
        log_hdlr.info("Triggered Rules are: {}".format(triggered_rules))

        for event_uuid in triggered_rules:
        	notify_json = {}
        	for rule in rules:
        		notify_json["edge_uuid"] = edge_uuid
        		if rule["event_uuid"] == event_uuid:
        			notify_json["event_uuid"] = rule["event_uuid"]
        			notify_json["motor_uuid"] = rule["motor_uuid"]
        			notify_json["action_status"] = False
        			notify_json["created_on"] = check_time
        			break
        	for rule_md in rules_md:
        		if rule_md["event_uuid"] == event_uuid:
        			notify_json["event_name"] = rule_md["event_name"]
        			notify_json["event_action"] = rules_md["event_action"]
        			break

            log_hdlr.info("Adding to Notification DB: {}".format(notify_json))
        	resp = ingest_notifications(notify_json)
        	log_hdlr.info("DB add responsed for event {} : {}".format(notify_json["event_uuid"], resp))

if __name__ == "__main__":

    rule = {}
    rules = []
    rule_md = {}
    rules_md = []

	try:
	    with open("/etc/yconfig.json", "r") as hdlr:
	        con = json.loads(hdlr.read())
	        EDGE_UUID = con["edge_uuid"]
	        content = json.loads(con["config_data"])

	        motor_conf = content["crane_details"]["motor_config"]
	        if "event_details" in content:
	            events = content["event_details"]

	            if events:
	                for event in events:
	                    rule["event_uuid"] == event["event_uuid"]
	                    rule_md["event_uuid"] == event["event_uuid"]
	                    rule["key"] = event["event_formula"]["key"]
	                    rule["rcondition"] = event["event_formula"]["condition"]
	                    rule["value"] = event["event_formula"]["value"]
	                    rule["event_seconds"] = event["event_seconds"]

	                    rule_md["event_name"] = event["event_name"]
	                    rule_md["event_action"] = 0
                            for action in event["event_action"]:
                                # Send Email
                                if action == 1:
                                    rule_md["event_action"] += 1
                                # Send Data to Cloud
                                if action == 2:
                                    rule_md["event_action"] += 2

                        for motor in motor_conf:
                            if motor["uuid"] == event["event_formula"]["motor_uuid"]:
                                rule["motor_uuid"] = motor["name"]

                        rules.append(rule)
                        rules_md.append(rule_md)
                        rule = {}
                        rule_md = {}

        if rules:
        	rules_check(EDGE_UUID, rules, rules_md)
        else:
        	log_hdlr.info("User Rules are not configured.")

	except Exception as err:
		pass
