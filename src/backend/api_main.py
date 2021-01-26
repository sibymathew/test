import flask
from flask import Flask, render_template, request, Response

from base64 import b64decode
import json
import datetime

from plc import dreams_plc_find_info

app = flask.Flask(__name__)
app.config["DEBUG"] = True

BASE_URL = "dreams"
VERSION = "v1"

@app.route('/<BASE_URL>/<VERSION>/plc', methods=['GET'])
def dreams_plc_get(BASE_URL, VERSION):

  if not "ip_addr" in request.args:
    response = {"status": 0, "response": {"reason": "Unknown Query Parameter. Refer API Documentation."}}
    return Response(json.dumps({"message": response}), 400)

  ip_addr=request.args.get('ip_addr')
  if "mode" in request.args and request.args.get('mode') == "test":
    response = {"status": 0, "response": {'vendor': 'Rockwell Automation/Allen-Bradley', 'product_type': 'Programmable Logic Controller'}}
    return Response(json.dumps({"message": response}), 200)
  else:
    info = dreams_plc_find_info(ip_addr)
    response = {"status": 0, "response": json.dumps(info)}
    return Response(json.dumps({"message": response}), 200)

app.run(host="0.0.0.0")
