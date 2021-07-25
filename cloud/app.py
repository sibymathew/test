from flask import Flask
from flask import request
from io import BytesIO
from cloud_loader import ingest_stream
import json
import gzip
import base64
import logging
from logging.handlers import RotatingFileHandler

LOG_PATH = "/var/log/cloud.log"
log_hdlr = logging.getLogger(__name__)
log_hdlr.setLevel(logging.DEBUG)

hdlr = RotatingFileHandler(LOG_PATH,maxBytes=5 * 1024 * 1024, backupCount=20)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
hdlr.setFormatter(formatter)
log_hdlr.addHandler(hdlr)

app = Flask(__name__)

@app.route("/v1/data/push", methods = ['POST', 'GET'])
def index():
    try:
        resp = request.json
        decodedData = base64.b64decode(resp["data"])

        received_value = BytesIO(decodedData)
        to_receive = gzip.GzipFile(fileobj=received_value, mode='rb').read()
        data = to_receive.decode("utf-8")
        log_hdlr.info(data)
        ingest_stream(data)
        #payload_rx = json.loads(to_receive.decode("utf-8"))
        #print(payload_rx)
        #print(len(payload_rx))
    except Exception as err:
        return {"status": 0, "msg": err}
    else:
        return {"status": 1, "msg": "Success"}

if __name__ == '__main__':
   app.run(host="0.0.0.0", port=443, debug = True)
