import sys
import os
import time
import notecard

from serial import Serial
import ast
import argparse
import json

from edge_loader import ingest_config, get_config_data
import requests

#import serial

__EDGE_MAC__ = os.popen("ip addr show $(awk 'NR==3{print $1}' /proc/net/wireless | tr -d :) | awk '/ether/{print $2}'").read().rstrip()
__EDGE_MAC__ = "00:0a:bb:11:22:22"

def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-puuid', action='store', help='Notecard Product UUID', type=str)
    parser.add_argument('-port', action='store', help='Notecard Comm Port', type=str)
    parser.add_argument('-rate', action='store', help='Notecard Baud Rate', type=int, default=115200)

    return parser.parse_args()

def store(data):

    ingest_config(data)
    res = requests.post("http://10.0.1.20:5000/cranes/version/update", json={"token": "def05f77d7541bfa8a9c61f551d45639"})

    if res.status_code == 400 or res.status_code == 401:
        return False

    return True

def main():

    args = getargs()
    productUID = args.puuid
    nodeport = args.port
    noderate = args.rate

    print("Opening port...")
    try:
        port = Serial(nodeport, noderate)
        #port = serial.Serial(nodeport, noderate)
    except Exception as exception:
        raise Exception("error opening port: {}".format(exception))

    print("Opening Notecard...")
    try:
        update_flag = False
        card = notecard.OpenSerial(port)

        to_send = {}
        to_send["req"] = "web.post"
        to_send["route"] = "configpull"

        data = {}
        data["edge_mac"] = __EDGE_MAC__

        try:
            with open("/var/run/version", "r") as hdlr:
                version = int(hdlr.readline().rstrip())
                if version == '':
                    version = 0
        except FileNotFoundError:
            version = 0


        while True:
            data["version"] = version
            to_send["body"] = data
            print(to_send)
            resp = card.Transaction(to_send)

            try:
                main_config = ast.literal_eval(resp["body"]["msg"])
                edge_config = json.loads(main_config[0])
            except Exception as e:
                print("Error \n {}".format(e))
            else:
                if edge_config["edge_mac"] == __EDGE_MAC__ and edge_config["version"] != version:
                    with open("/var/run/yconfig.json", "w") as hdlr:
                        hdlr.write(json.dumps(edge_config))
                        update_flag = True

            if update_flag:
                config = ast.literal_eval(edge_config["config_data"])[0]
                with open("config.supervisor") as hdlr:
                    supervisor_conf = hdlr.read()
                with open("config.supervisor.template") as hdlr:
                    supervisor_tmpl = hdlr.read()

                result = supervisor_conf
                all_motor_list = ""

                edge_uuid = config["edge_uuid"]
                port_map = {"1":[], "2":[], "3":[], "4": []}
                for mapping in config["crane_details"]["vfd_mapping"]:
                    port = mapping["network"]["usb_port"]
                    port_map[str(port)].append(mapping["vfd_uuid"]) 

                for port in port_map:
                    if port_map[port]:
                        port_name = "/dev/ttyUSB0"
                        address = []
                        speciality = []
                        types = []
                        red_factor = []
                        label = []
                        motors = []
                        loadcell = []
                        for mapping in config["crane_details"]["vfd_mapping"]:
                            addr = mapping["network"]["address"]
                            address.append(addr[2:])
                            rate = mapping["network"]["baud_rate"]
                            for m in mapping["vfd_motor_mapping"]:
                                motors.append(addr + ":" + m)
                            speciality.append(addr+":"+str(mapping["vfd_speciality"]))
                            types.append(addr+":"+str(mapping["vfd_type"]))

                            if 'loadcell' in mapping:
                                params = str(mapping["loadcell"]["register"]) + "," + \
                                            str(mapping["loadcell"]["mode"]) + "," + \
                                            str(mapping["loadcell"]["calibration"]["a"]) + "," + \
                                            str(mapping["loadcell"]["calibration"]["b"]) + "," + \
                                            str(mapping["loadcell"]["calibration"]["c"])
                                loadcell.append(addr+":"+params)

                            for motor in config["crane_details"]["motor_config"]:
                                if addr+":"+motor["uuid"] in motors:
                                    red_factor.append(addr+":"+str(motor["motor_reduction_factor"]))
                                    label.append(addr+":" + motor["drive_direction"]["forward_label"] + " " + addr + ":" + motor["drive_direction"]["backward_label"])
                                    to_apply = True
                                    break             

                        address_list = " ".join(address)
                        speciality_list = " ".join(speciality)
                        types_list = " ".join(types)
                        red_factor_list = " ".join(red_factor)
                        label_list = " ".join(label)
                        motor_list = " ".join(motors)
                        loadcell_list = " ".join(loadcell)

                        name = "Collect_Service_" + port
                        cmd = "sudo docker run --privileged -e CASSANDRA_IP='10.0.1.20' sibymath/edge_collect:v1 -a {} -p {} -r {} -eu {} -mu {} -mt {} -ms {} -rf {} -lb {} -lc {} -m {}".format(address_list, port_name, rate, edge_uuid, motor_list, types_list, speciality_list, red_factor_list, label_list, loadcell_list, "0")

                        temp_tmpl = supervisor_tmpl.replace("name", name)
                        temp_tmpl = temp_tmpl.replace("cmd", cmd)

                        result = result + temp_tmpl

                        all_motor_list += motor_list + " "

                cmd = "sudo docker run --privileged -e CASSANDRA_IP='10.0.1.20' sibymath/edge_push:v1 -puuid 'world.youtopian.siby.mathew:drill_bit' -port '/dev/ttyACM0' -rate 9600 -mu {}".format(all_motor_list)
                name = "Cloud_Push_Service"

                temp_tmpl = supervisor_tmpl.replace("name", name)
                temp_tmpl = temp_tmpl.replace("cmd", cmd)

                result = result + temp_tmpl

                with open("supervisord.conf", "w") as hdlr:
                    hdlr.write(result)

                if store(main_config):
                    res = os.popen("supervisorctl restart all")
                    with open("/var/run/version", "w") as hdlr:
                        hdlr.write(str(edge_config["version"]))
                        
                        update_flag = False
                        version = edge_config["version"]

            time.sleep(30)
    except Exception as exception:
        raise Exception("error opening notecard: {}".format(exception))

main()