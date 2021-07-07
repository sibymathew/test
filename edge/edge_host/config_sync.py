import sys
import os
import time
import notecard

from periphery import Serial
import ast
import argparse

#import serial

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
        pass
        #port = Serial(nodeport, noderate)
        #port = serial.Serial(nodeport, noderate)
    except Exception as exception:
        raise Exception("error opening port: {}".format(exception))

    print("Opening Notecard...")
    try:
        #card = notecard.OpenSerial(port)

        while True:
            to_send = {}
            to_send["req"] = "web.get"
            to_send["route"] = "configpull"
            while True:
                #config = card.Transaction(to_send)
                with open("config.local", "r") as hdlr:
                    content = hdlr.read()
                    config = ast.literal_eval(content)

                print(config)

                if config["edge_serial"] == "5adc6718fdef":
                    with open("config.supervisor") as hdlr:
                        supervisor_conf = hdlr.read()
                    with open("config.supervisor.template") as hdlr:
                        supervisor_tmpl = hdlr.read()

                    cmd = "docker run sibymath/edge_push:v1 -puuid 'world.youtopian.siby.mathew:drill_bit' -port '/dev/ttyACM0' -rate 9600"
                    name = "Cloud Push Service"

                    temp_tmpl = supervisor_tmpl.replace("name", name)
                    temp_tmpl = temp_tmpl.replace("cmd", cmd)

                    result = supervisor_conf + temp_tmpl

                    edge_uuid = config["edge_uuid"]
                    total_motors = config["total_motors"]
                    port = "/dev/ttyUSB0"
                    print(edge_uuid)
                    print(total_motors)
                    for motor in config["motor_config"]:
                        address = motor["network"]["address"]
                        rate = motor["network"]["baud_rate"]
                        motor_uuid = motor["uuid"]

                        name = "Collect Service " + motor_uuid
                        cmd = "docker run sibymath/edge_collect:v1 -a {} -p {} -r {} -eu {} -mu {} -c {}".format(address, port, rate, edge_uuid, motor_uuid, total_motors)

                        temp_tmpl = supervisor_tmpl.replace("name", name)
                        temp_tmpl = temp_tmpl.replace("cmd", cmd)

                        result = result + temp_tmpl

                with open("supervisord.conf", "w") as hdlr:
                    hdlr.write(result)

                sys.exit(2)
                time.sleep(60)
                #Serial number from the box to be checked against the incoming configuration
    except Exception as exception:
        raise Exception("error opening notecard: {}".format(exception))

main()
