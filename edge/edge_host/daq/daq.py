from subprocess import Popen, PIPE, check_output, STDOUT
from edge_loader import get_motor_data
import time
import json
import argparse
import logging
from logging.handlers import RotatingFileHandler

LOG_PATH = "/var/log/daq.log"
log_hdlr = logging.getLogger(__name__)
log_hdlr.setLevel(logging.DEBUG)

hdlr = RotatingFileHandler(LOG_PATH,maxBytes=5 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
hdlr.setFormatter(formatter)
log_hdlr.addHandler(hdlr)

def check_signal(motor_list, pstate_port0, pstate_port1):
    command = "/home/utopia/test/edge/edge_host/daq/StaticDI"
    seconds = 5
    while True:
        log_hdlr.info("Pre State P0:{} P1:{}".format(pstate_port0, pstate_port1))
        try:
            o = check_output(command, stderr=STDOUT, timeout=seconds)
            log_hdlr.info("DAQ Port Read {}".format(o))
            print(o)
        except Exception as err:
            log_hdlr.info("DAQ Read Port Timedout")
        else:
            x = o.decode("utf-8")
            s = bin(int(x[0]))[2:]
            if len(s) == 1:
                s = "0" + s
            ping_time = round(time.time() * 1000)
            log_hdlr.info("{} Formatted String {}".format(ping_time, s))

            # Overriding Port0 as per ACECO we should read Power status from 02BH register.
            t0 = s[0]
            s = t0+"2"
            if s[1] == "0":
                # If pstate_port0 is already 6, then stop checking.
                if pstate_port0 == 0 or pstate_port0 == 5:
                    msg = {}
                    stop_mode = 5
                    content = get_motor_data("crane_details", motor_list, 5)

                    log_hdlr.info(content)

                    if "Error" in content:
                        stop_mode = 5
                    else:
                        for row in json.loads(content):
                            i = json.loads(row)
                            if "vfd_status" in i:
                                k = i["vfd_status"]
                                if k == 3 or k == 6:
                                    stop_mode = 6
                                    break


                    msg["status"] = stop_mode
                    msg["timestamp"] = ping_time
                    log_hdlr.info("Msg: {}".format(msg))
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
                log_hdlr.info("Msg: {}".format(msg))

                if pstate_port1 != 8:
                    with open("/etc/daq_port1", "w") as hdlr:
                        hdlr.write(json.dumps(msg))
                        pstate_port1 = 8
                else:
                    with open("/etc/daq_port1", "r") as hdlr:
                        content = json.loads(hdlr.read())
                        if "state" in content:
                            if content["state"] == "Pushed":
                                resp = Popen(["supervisorctl stop API_Int"], stdout=PIPE, stderr=PIPE, shell=True)
                                o, e = resp.communicate()
                                resp = Popen(["supervisorctl stop Cloud_Push_Service"], stdout=PIPE, stderr=PIPE, shell=True)
                                o, e = resp.communicate()
                                resp = Popen(["supervisorctl stop Collect_Service_1"], stdout=PIPE, stderr=PIPE, shell=True)
                                o, e = resp.communicate()
                                resp = Popen(["supervisorctl stop Config_Sync"], stdout=PIPE, stderr=PIPE, shell=True)
                                o, e = resp.communicate()
                                resp = Popen(["systemctl stop cassandra.service"], stdout=PIPE, stderr=PIPE, shell=True)
                                o, e = resp.communicate()
                                resp = Popen(["systemctl restart sshd"], stdout=PIPE, stderr=PIPE, shell=True)
                                o, e = resp.communicate()
            elif s[0] == "1":
                resp = Popen(["rm", "-rf", "/etc/daq_port1"], stdout=PIPE, stderr=PIPE)
                o, e = resp.communicate()
                if pstate_port1 == 8:
                    pstate_port1 = 0
                    resp = Popen(["reboot --reboot"], stdout=PIPE, stderr=PIPE, shell=True)
                    o, e = resp.communicate()

        time.sleep(0.1)

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
