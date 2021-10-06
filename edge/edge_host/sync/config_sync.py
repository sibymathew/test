import sys
import os
import time
import notecard

from periphery import Serial
import ast
import argparse

#import serial

__EDGE_MAC__ = os.popen("ip addr show $(awk 'NR==3{print $1}' /proc/net/wireless | tr -d :) | awk '/ether/{print $2}'").read().rstrip()


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
        port = serial.Serial(nodeport, noderate)
    except Exception as exception:
        raise Exception("error opening port: {}".format(exception))

    print("Opening Notecard...")
    try:
        update_flag = False
        card = notecard.OpenSerial(port)

        to_send = {}
        to_send["req"] = "web.get"
        to_send["route"] = "configpull"

        data = {}
        data["edge_mac"] = __EDGE_MAC__

        try:
            with open("/var/run/version", "r") as hdlr:
                version = hdlr.readline()
        except FileNotFoundError:
            version = "0"


        while True:
            data["version"] = version
            to_send["body"] = data
            edge_config = card.Transaction(to_send)

            if edge_config["edge_mac"] == __EDGE_MAC__ and edge_config["version"] != version:
                with open("/var/run/yconfig.json", "w") as hdlr:
                    hdlr.write(config)
                    update_flag = True

            if update_flag:
                with open("config.supervisor") as hdlr:
                    supervisor_conf = hdlr.read()
                with open("config.supervisor.template") as hdlr:
                    supervisor_tmpl = hdlr.read()

                result = supervisor_conf
                all_motor_uuid_str = ""

                edge_uuid = config["edge_uuid"]
                port = "/dev/ttyUSB0"
                print(edge_uuid)
                for mapping in config["crane_details"]["vfd_mapping"]:
                    to_apply = False
                    motors = mapping["vfd_motor_mapping"]

                    for motor in config["crane_details"]["motor_config"]:
                        if motor["uuid"] in motors:
                            address = motor["network"]["address"]
                            rate = motor["network"]["baud_rate"]
                            motor_type = motor["motor_type"]
                            red_factor = motor["motor_reduction_factor"]
                            to_apply = True
                            break

                    if to_apply:
                        motor_uuid_str = " ".join(motors)

                        name = "Collect_Service_" + motor_uuid_str.replace(" ", "_")
                        cmd = "sudo docker run --privileged -e CASSANDRA_IP='192.168.1.35' sibymath/edge_collect:v1 -a {} -p {} -r {} -eu {} -mu {} -mt {} -rf {} -c {}".format(address, port, rate, edge_uuid, motor_uuid_str, motor_type, red_factor, len(motors))
                        to_apply = False

                        temp_tmpl = supervisor_tmpl.replace("name", name)
                        temp_tmpl = temp_tmpl.replace("cmd", cmd)

                        result = result + temp_tmpl

                        all_motor_uuid_str += motor_uuid_str + " "

                cmd = "sudo docker run --privileged -e CASSANDRA_IP='192.168.1.35' sibymath/edge_push:v1 -puuid 'world.youtopian.siby.mathew:drill_bit' -port '/dev/ttyACM0' -rate 9600 -mu {}".format(all_motor_uuid_str)
                name = "Cloud_Push_Service"

                temp_tmpl = supervisor_tmpl.replace("name", name)
                temp_tmpl = temp_tmpl.replace("cmd", cmd)

                result = result + temp_tmpl

                with open("supervisord.conf", "w") as hdlr:
                    hdlr.write(result)

                with open("/var/run/version", "w") as hdlr:
                    hdlr.write(edge_config["version"])
                    
                    update_flag = False
                    version = edge_config["version"]

            time.sleep(5)
    except Exception as exception:
        raise Exception("error opening notecard: {}".format(exception))

main()
