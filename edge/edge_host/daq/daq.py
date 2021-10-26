from subprocess import Popen, PIPE
from edge_loader import get_motor_data
import time
import json
import argparse

def check_signal(motor_list, pstate_port0, pstate_port1):
    while True:
        resp = Popen(["./StaticDI"], stdout=PIPE, stderr=PIPE)
        o, e = resp.communicate()
        print(o)
        print(e)

        x = o.decode("utf-8")
        s = bin(int(x[0]))[2:]
        if len(s) == 1:
            s = "0" + s
        ping_time = round(time.time() * 1000)

        if not "error" in s:
            if s[1] == "0":
                msg = {}
                stop_mode = 5
                content = get_motor_data("table", motor_list, 0)

                print(content)

                if not content or "Error" in content:
                    stop_mode = 5
                else:
                    for row in json.loads(content):
                        i = json.loads(row)
                        if "vfd_status" in i:
                            k = i["vfd_status"]
                            if k == 3:
                                stop_mode = 6
                                break

                msg["status"] = stop_mode
                msg["timestamp"] = ping_time
                if pstate_port0 != stop_mode:
                    with open("/etc/daq_port0", "w") as hdlr:
                        hdlr.write(json.dumps(msg))
                        pstate_port0 = stop_mode
            elif s[1] == "1":
                resp = Popen(["rm", "-rf", "/etc/daq_port0"], stdout=PIPE, stderr=PIPE)
                o, e = resp.communicate()
                pstate_port0 = 0

            if s[0] == "0":
                msg = {}
                msg["status"] = 8
                msg["timestamp"] = ping_time

                if pstate_port1 != 8:
                    with open("/etc/daq_port1", "w") as hdlr:
                        hdlr.write(json.dumps(msg))
                        pstate_port1 = 8
                else:
                    with open("/etc/daq_port1", "r") as hdlr:
                        content = json.loads(hdlr.read())
                        if "state" in content:
                            if content["state"] == "Pushed":
                                resp = Popen(["supervisorctl stop all"], stdout=PIPE, stderr=PIPE, shell=True)
                                o, e = resp.communicate()
                                resp = Popen(["systemctl stop cassandra.service"], stdout=PIPE, stderr=PIPE, shell=True)
                                o, e = resp.communicate()
            elif s[0] == "1":
                resp = Popen(["rm", "-rf", "/etc/daq_port1"], stdout=PIPE, stderr=PIPE)
                o, e = resp.communicate()
                pstate_port1 = 0
        else:
            print("Error")
        time.sleep(5)

def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-mu', action='store', help='Motor UUID', nargs="+", type=str)

    return parser.parse_args()

if __name__ == "__main__":

    args = getargs()
    motor_list = args.mu

    try:
        with open("/etc/daq_port0", "r") as hdlr:
            a = json.loads(hdlr.read())

            if "status" in a:
                previous_state_port0 = a["status"]
            else:
                previous_state_port0 = 0
    except:
        previous_state_port0 = 0

    try:
        with open("/etc/daq_port1", "r") as hdlr:
            a = json.loads(hdlr.read())

            if "status" in a:
                previous_state_port1 = a["status"]
            else:
                previous_state_port1 = 0
    except:
        previous_state_port1 = 0

    check_signal(motor_list, previous_state_port0, previous_state_port1)