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

productUID = "world.youtopian.siby.mathew:drill_bit"
port = "/dev/tty.usbmodemNOTE1"
rate = 9600


def configure_notecard(productUID, card):
    req = {"req": "hub.set"}
    req["product"] = productUID
    req["mode"] = "continuous"

    try:
        card.Transaction(req)
    except Exception as exception:
        print("Transaction error: {}".format(exception))
        time.sleep(5)

def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-puuid', action='store', help='Notecard Product UUID', type=str)
    parser.add_argument('-port', action='store', help='Notecard Comm Port', type=str)
    parser.add_argument('-rate', action='store', help='Notecard Baud Rate', type=int, default=115200)

    return parser.parse_args()

def main():

    args = getargs()
    productUID = args.puuid
    nodeport = args.port
    noderate = args.rate

    print("Opening port...")
    try:
        port = Serial(nodeport, noderate)
    except Exception as exception:
        raise Exception("error opening port: {}".format(exception))

    print("Opening Notecard...")
    try:
        card = notecard.OpenSerial(port)
    except Exception as exception:
        raise Exception("error opening notecard: {}".format(exception))

    try:
        configure_notecard(productUID, card)

        da = get_motor_data("table", 2)
        print(da)
        # To collect data from database. Example below.
        # da = {'motor_data': [{'d': 'Motor Speed in Hz', 'k': 'motor_speed', 'u': 'Hz', 'v': 0}, {'d': 'Output Voltage', 'k': 'output_voltage', 'u': 'Volt', 'v': 0}, {'d': 'DC Bus Voltage', 'k': 'dc_bus_voltage', 'u': 'Volt', 'v': 298}, {'d': 'Output Horsepower', 'k': 'output_hp', 'u': 'HP', 'v': 0}, {'d': 'Drive Ready', 'k': 'drive_ready', 'v': 1}, {'d': 'Alarm/Minor Fault', 'k': 'drive_alarm', 'v': 0}, {'d': 'Major Fault', 'k': 'drive_fault', 'v': 0}, {'d': 'Drive Direction', 'k': 'drive_direction'}, {'d': 'Run Time', 'k': 'run_time', 'u': 'TBD', 'v': 7}, {'d': 'Motor Amps', 'k': 'motor_amps', 'v': 0.0}, {'d': 'Total Motor Start/Stop', 'k': 'number_of_start_stop', 'v': 172}, {'d': 'Motor in RPM', 'k': 'motor_in_rpm', 'v': 0.0}, {'d': 'Speed in FPM', 'k': 'speed_in_fpm', 'v': 0.0}], 'timestamp': 1623452329314}

        to_send = {}
        to_send["req"] = "web.post"
        to_send["route"] = "datapush"

        compressed_body = BytesIO()
        gz = gzip.GzipFile(fileobj=compressed_body, mode="wb")
        sz = gz.write(json.dumps(da).encode("utf-8"))
        gz.close()
        de = compressed_body.getvalue()

        encodedData = base64.b64encode(de).decode('UTF-8')
        to_send["body"] = {"data": encodedData}

        print(round(time.time() * 1000))
        r = card.Transaction(to_send)
        print(round(time.time() * 1000))
    except Exception as exception:
        print("Transaction error: {}".format(exception))
        time.sleep(5)

main()
