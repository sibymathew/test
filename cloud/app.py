from flask import Flask
from flask import request
from io import BytesIO
from cloud_loader import ingest_stream
import json
import gzip
import base64

app = Flask(__name__)

@app.route("/v1/data/push", methods = ['POST', 'GET'])
def index():
    resp = request.json
    print(resp)
    decodedData = base64.b64decode(resp["data"])
    print(decodedData)

    received_value = BytesIO(decodedData)
    to_receive = gzip.GzipFile(fileobj=received_value, mode='rb').read()
    ingest_stream(to_receive.decode("utf-8"))
    #payload_rx = json.loads(to_receive.decode("utf-8"))
    #print(payload_rx)
    #print(len(payload_rx))

    return {"msg": "Success!"}

if __name__ == '__main__':
   app.run(host="0.0.0.0", port=443, debug = True)
