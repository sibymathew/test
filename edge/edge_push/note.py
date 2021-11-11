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
from edge_loader import get_motor_data, del_motor_data

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

# in seconds
__SLEEP__ = 5
# in minutes    
__CLOUD_PUSH__ = 60
# DB Check time, in seconds
__PUSH_COUNTER__ = (__CLOUD_PUSH__ * 60) / __SLEEP__

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
        counter = 0
        to_send = {}
        to_send["req"] = "web.post"
        to_send["route"] = "datapush"

        while True:
            push_mode = 0
            try:
                with open("/etc/daq_port0", "r") as hdlr:
                    content = json.loads(hdlr.read())
                    if "status" in content:
                        if content["status"] == 6:
                            if "state" in content:
                                if content["state"] != "Pushed":
                                    push_mode = 1
                            else:
                                push_mode = 1
            except:
                pass

            try:
                with open("/etc/daq_port1", "r") as hdlr:
                    content = json.loads(hdlr.read())
                    if "status" in content:
                        if content["status"] == 8:
                            if "state" in content:
                                if content["state"] != "Pushed":
                                    push_mode = 2
                            else:
                                push_mode = 2
            except:
                pass

            if push_mode == 1 or push_mode == 2:
                start_time = time.time()
                to_send["route"] = "datapushrt"

                for m in motor_uuid:
                    da = get_motor_data("crane_details", m, 3)

                    if da != "[]":
                        log_hdlr.info("Push Mode {}. Push Data for Motor {}".format(push_mode, m))
                        push_blues(card, da)
                    else:
                        log_hdlr.info("Push Mode {}. But nothing to push to cloud.".format(push_mode))
                
            else:
                if counter == 0:
                    start_time = time.time()
                    push_mode = 3
                    da = get_motor_data("edge_core.crane_details2", motor_uuid, __CLOUD_PUSH__)

                    if da != "[]":
                        log_hdlr.info("Push Mode {}. Push Data for All Motors".format(push_mode))
                        push_blues(card, da)

                        # Delete all the entries in edge_core.crane_details2
                        del_motor_data("edge_core.crane_details2", motor_uuid, None)
                    else:
                        log_hdlr.info("Push Mode {}. But nothing to push to cloud.".format(push_mode))

                    counter +=1 
                elif counter >= __PUSH_COUNTER__:
                    counter = 0
                else:
                    counter +=1


            if push_mode != 0:
                end_time = time.time()
                lapsed_time = end_time - start_time
                log_hdlr.info("Push Mode {}. Total Lapsed Time {}".format(push_mode, lapsed_time))            

            if push_mode == 1:
                with open("/etc/daq_port0", "r") as hdlr:
                    content = json.loads(hdlr.read())
                    if "status" in content:
                        if content["status"] == 6:
                            content["state"] = "Pushed"

                with open("/etc/daq_port0", "w") as hdlr:
                    hdlr.write(json.dumps(content))

            if push_mode == 2:
                with open("/etc/daq_port1", "r") as hdlr:
                    content = json.loads(hdlr.read())
                    if "status" in content:
                        if content["status"] == 8:
                            content["state"] = "Pushed"

                with open("/etc/daq_port1", "w") as hdlr:
                    hdlr.write(json.dumps(content))

            push_mode = 0
            time.sleep(__SLEEP__)

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

def push_blues(card, da):

    try:
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
    except Exception as err:
        raise(err)

def restart(card):
    try:
        req = {"req": "card.restart"}
        resp = card.Transaction(req)

        log_hdlr.info("Restart Notecard Response {}".format(resp))
    except:
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

