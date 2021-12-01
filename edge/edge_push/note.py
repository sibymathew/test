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
import time
from edge_loader import get_motor_data, del_motor_data, get_notify_data, update_notify_data

sys.path.insert(0, os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..')))

import notecard
import logging
from logging.handlers import RotatingFileHandler

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

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

def connect(productUID, nodeport, noderate, motor_uuid, edge_uuid):

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

    push(card, motor_uuid, edge_uuid)

def push(card, motor_uuid, edge_uuid):
    try:
        counter = 0
        to_send = {}
        to_send["req"] = "web.post"

        while True:
            push_mode = 0

            # Read Active System Events
            try:
                active_notifications = get_notify_data([edge_uuid], 30)

                h_time = 0
                l_time = round(time.time() * 1000)
                for notif in active_notifications:
                    cloud_notification("add", notif, card)
                    if notif["event_action"] == 1 or notif["event_action"] == 3:
                        send_email(notif["event_uuid"])
                    if notif["event_action"] == 2 or notif["event_action"] == 3:
                        if notif["created_on"] > h_time:
                            h_time = notif["created_on"]
                            interval = h_time - 180000

                            if l_time <= interval:
                                l_time = interval

                if h_time != 0:
                    push_mode = 4
                    start_time = time.time()
                    to_send["route"] = "datapush"

                    da = get_motor_data("crane_details", [m], h_time, l_time)
                    if da != "[]":
                        log_hdlr.info("Push Mode {}. Push Data for Motor {}".format(push_mode, m))
                        push_blues(card, da, to_send)
                    else:
                        log_hdlr.info("Push Mode {}. But nothing to push to cloud.".format(push_mode))
                    end_time = time.time()
                    lapsed_time = end_time - start_time
                    log_hdlr.info("Push Mode {}. Total Lapsed Time {}".format(push_mode, lapsed_time))

                for notif in active_notifications:
                    update_notify_data(notif["motor_uuid"], notif["event_uuid"], True)
                    cloud_notification("update", notif, card)
            except Exception as err:
                raise Exception(err)

            try:
                # Read Active User Events
                active_notifications = get_notify_data([edge_uuid], 30)
                for notif in active_notifications:
                    notif
            except Exception as err:
                raise Exception(err)

            if counter == 0:
                to_send["route"] = "datapush"
                start_time = time.time()
                push_mode = 3
                da = get_motor_data("edge_core.crane_details2", motor_uuid, __CLOUD_PUSH__)

                if da != "[]":
                    log_hdlr.info("Push Mode {}. Push Data for All Motors".format(push_mode))
                    push_blues(card, da, to_send)

                    # Delete all the entries in edge_core.crane_details2
                    del_motor_data("edge_core.crane_details2", motor_uuid, None)
                    end_time = time.time()
                    lapsed_time = end_time - start_time
                    log_hdlr.info("Push Mode {}. Total Lapsed Time {}".format(push_mode, lapsed_time))
                else:
                    log_hdlr.info("Push Mode {}. But nothing to push to cloud.".format(push_mode))

                counter +=1 
            elif counter >= __PUSH_COUNTER__:
                counter = 0
            else:
                counter +=1

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

                if push_mode == 2:
                    start_time = time.time()
                    to_send["route"] = "datapushrt"
                    for m in motor_uuid:
                        da = get_motor_data("crane_details", [m], 3)
                        if da != "[]":
                            log_hdlr.info("Push Mode {}. Push Data for Motor {}".format(push_mode, m))
                            push_blues(card, da, to_send)
                        else:
                            log_hdlr.info("Push Mode {}. But nothing to push to cloud.".format(push_mode))
                    end_time = time.time()
                    lapsed_time = end_time - start_time
                    log_hdlr.info("Push Mode {}. Total Lapsed Time {}".format(push_mode, lapsed_time))

                    with open("/etc/daq_port1", "r") as hdlr:
                    content = json.loads(hdlr.read())
                    if "status" in content:
                        if content["status"] == 8:
                            content["state"] = "Pushed"

                    with open("/etc/daq_port1", "w") as hdlr:
                        hdlr.write(json.dumps(content))
            except Exception as err:
                raise Exception(err)

            # Read Active System Events
            try:
                for m in motor_uuid:
                    active_notifications = get_notify_data([m], 30)

                    h_time = 0
                    l_time = round(time.time() * 1000)
                    for notif in active_notifications:
                        cloud_notification("add", notif, card)
                        if notif["event_action"] == 1 or notif["event_action"] == 3:
                            send_email(notif["event_uuid"])
                        if notif["event_action"] == 2 or notif["event_action"] == 3:
                            if notif["created_on"] > h_time:
                                h_time = notif["created_on"]
                                interval = h_time - 180000

                                if l_time <= interval:
                                    l_time = interval

                    if h_time != 0:
                        push_mode = 4
                        start_time = time.time()
                        to_send["route"] = "datapush"

                        da = get_motor_data("crane_details", [m], h_time, l_time)
                        if da != "[]":
                            log_hdlr.info("Push Mode {}. Push Data for Motor {}".format(push_mode, m))
                            push_blues(card, da, to_send)
                        else:
                            log_hdlr.info("Push Mode {}. But nothing to push to cloud.".format(push_mode))
                        end_time = time.time()
                        lapsed_time = end_time - start_time
                        log_hdlr.info("Push Mode {}. Total Lapsed Time {}".format(push_mode, lapsed_time))

                    for notif in active_notifications:
                        update_notify_data(notif["motor_uuid"], notif["event_uuid"], True)
                        cloud_notification("update", notif, card)
            except Exception as err:
                raise Exception(err)

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
        push(card, motor_uuid)

def cloud_notification(method, notif, card):
    to_send = {}
    to_send["req"] = "web.post"
    to_send["route"] = "notification"
    data = {}
    data["method"] = method
    data["notif"] = notif
    to_send["body"] = data

    push_blues(card, None, to_send)

def push_blues(card, da, to_send):

    try_send = 0
    try:
        if da:
            compressed_body = BytesIO()
            gz = gzip.GzipFile(fileobj=compressed_body, mode="wb")
            sz = gz.write(json.dumps(da).encode("utf-8"))
            gz.close()
            de = compressed_body.getvalue()

            encodedData = base64.b64encode(de).decode('UTF-8')
            to_send["body"] = {"data": encodedData}

            log_hdlr.info("\nSending {} bytes of data".format(compressed_body.getbuffer().nbytes))
        while try_send < 3:
            resp = card.Transaction(to_send)
            log_hdlr.info("Push Notecard Response {}".format(resp))
            if "err" in resp:
                try_send += 1
            else:
                break
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

def send_mail():
    message = Mail(
        from_email='siby.mathew@youtopian.world',
        to_emails='siby.mathew@youtopian.world',
        subject='Sending with Twilio SendGrid is Fun',
        html_content='<strong>and easy to do anywhere, even with Python</strong>')
    try:
        print(os.environ.get('SENDGRID_API_KEY'))
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)

def main():

    args = getargs()
    productUID = args.puuid
    nodeport = args.port
    noderate = args.rate
    motor_uuid = args.mu
    edge_uuid = args.eu

    connect(productUID, nodeport, noderate, motor_uuid, edge_uuid)

main()

