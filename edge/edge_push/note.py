"""note-python Serial example.
This file contains a complete working sample for using the note-python
library with a Serial Notecard connection.
"""
import sys
import os
import time
import argparse

from io import BytesIO
import gzip
import json
import base64

from serial import Serial
from edge_loader import get_motor_data

sys.path.insert(0, os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..')))

import notecard
import logging
from logging.handlers import RotatingFileHandler

LOG_PATH = "/var/log/push.log"
log_hdlr = logging.getLogger(__name__)
log_hdlr.setLevel(logging.DEBUG)

hdlr = RotatingFileHandler(LOG_PATH,maxBytes=5 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
hdlr.setFormatter(formatter)
log_hdlr.addHandler(hdlr)

__PUSH_INTERVAL__ = 60 * 60 #seconds

def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-puuid', action='store', help='Notecard Product UUID', type=str)
    parser.add_argument('-port', action='store', help='Notecard Comm Port', type=str)
    parser.add_argument('-rate', action='store', help='Notecard Baud Rate', type=int, default=115200)
    parser.add_argument('-mu', action='store', help='Motor UUID', nargs="+", type=str)

    return parser.parse_args()

def configure_notecard(productUID, card):
    req = {"req": "hub.set"}
    req["product"] = productUID
    req["mode"] = "continuous"

    try:
        resp = card.Transaction(req)
        log_hdlr.info("Configure NoteCard Response {}".format(resp))
    except Exception as exception:
        log_hdlr.info("Transaction error: {}".format(exception))
        time.sleep(5)

def connect(productUID, nodeport, noderate, motor_uuid):

    print("Opening port...")
    try:
        port = Serial(nodeport, noderate)
        log_hdlr.info("Opened Serial Port {}".format(port))
    except Exception as exception:
        log_hdlr.info("Error opening port: {}".format(exception))

    print("Opening Notecard...")
    try:
        card = notecard.OpenSerial(port)
        log_hdlr.info("Opened Card {}".format(card))
    except Exception as exception:
        log_hdlr.info("Error opening notecard: {}".format(exception))

    try:
        configure_notecard(productUID, card)
    except Exception as exception:
        log_hdlr.info("Error opening notecard: {}".format(exception))

    push(card, motor_uuid)

def push(card, motor_uuid):
    try:
        to_send = {}
        to_send["req"] = "web.post"
        to_send["route"] = "datapush"

        while True:
            start_time = time.time()
            da = get_motor_data("table", motor_uuid, 2)
            print(da)

            compressed_body = BytesIO()
            gz = gzip.GzipFile(fileobj=compressed_body, mode="wb")
            sz = gz.write(json.dumps(da).encode("utf-8"))
            gz.close()
            de = compressed_body.getvalue()

            encodedData = base64.b64encode(de).decode('UTF-8')
            to_send["body"] = {"data": encodedData}

            log_hdlr.info("Sending {} bytes of data".format(compressed_body.getbuffer().nbytes))
            resp = card.Transaction(to_send)
            log_hdlr.info("Push Notecard Response {}".format(resp))
            end_time = time.time()

            lapsed_time = end_time - start_time
            log_hdlr.info("Total Lapsed Time {}".format(lapsed_time))

            time.sleep(__PUSH_INTERVAL__-lapsed_time)

            """
            if 'err' in resp:
                log_hdlr.info("Restarting the card. Wait... ")
                restart(card)
            """
    except Exception as exception:
        log_hdlr.info("Transaction error: {}".format(exception))
        time.sleep(5)
        # Not a correct way to code, as it is recursive. But very rare happening. Will change it later.
        push()

def restart(card):
    try:
        req = {"req": "card.restart"}
        resp = card.Transaction(req)

        log_hdlr.info("Restart Notecard Response {}".format(resp))

        main()
        #Recursive

def main():

    args = getargs()
    productUID = args.puuid
    nodeport = args.port
    noderate = args.rate
    motor_uuid = args.mu

    connect(productUID, nodeport, noderate, motor_uuid)

main()

