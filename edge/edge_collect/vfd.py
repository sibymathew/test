from yw.edge.interface import YWSerialClient as ModbusClient
from edge_loader import ingest_stream, ingest_stream2
from edge_loader import get_motor_data, ingest_hourly_stream, ingest_notifications

import argparse
import json
import time
import logging
from logging.handlers import RotatingFileHandler
import ast
import sys

#in milliseconds
__PULL_INTERVAL__ = 1000
#in seconds, data to be pushed to ingest_stream2
__PUSH_INTERVAL__ = 60 * 60

__FAULT_STRINGS__ = {
    "1840" : ["PUF - Fuse Blown",
            "UV1 - DC Bus Undervoltage",
            "UV2 - CTL PS Undervoltage",
            "UV3 - MC Answerback",
            "Not Used",
            "GF - Ground Fault",
            "OC - Over Current",
            "OV - Overvoltage",
            "OH - Heatsink Overtemperature",
            "OH1 - Drive Overheat",
            "OL1 - Motor Overload",
            "OL2 - Drive Overload",
            "OT1 - Overtorque 1",
            "OT2 - Overtorque 2",
            "RR - Dynamic Braking Resistor",
            "RH - Dynamic Braking Resistor Overheat"],
    "1841" : ["EF3 - External Fault 3",
            "EF4 - External Fault 4",
            "EF5 - External Fault 5",
            "EF5 - External Fault 6",
            "EF5 - External Fault 7",
            "EF5 - External Fault 8",
            "PGO-1-h - PG CH 1 Open (Hardware Detection)",
            "OS-1 - CH 1 Overspeed",
            "DEV-1 - Speed Deviation",
            "PGO-1-S - PG CH 1 Open (Software Detection)",
            "PF - Input Phase Loss",
            "LF - Output Phase Loss",
            "OH3 - Motor Overheat",
            "OPR - Operator Disconnect",
            "ERR - EEPROM R/W Error",
            "OH4 - Motor Overheat 2"],
    "1842": ["CE - Modbus Com Error",
            "BUS - Option Communication Error",
            "E15 - Serial Communcation Error",
            "E10 - Option CPU Down",
            "CF - Out of Control",
            "SVE - Zero Servo Fault",
            "EFO - Communication Option External Fault",
            "FBL - PID Feedback Loss",
            "UT1 - Undertorque 1",
            "UT2 - Undertorque 2",
            "OL7 - High Speed Slip Braking Overload",
            "PGO-2-H - PG CH2 Open (Hardware Detection)",
            "OS-2 - CH2 Overspeed",
            "DEV-2 - CH2 Speed Deviation",
            "PGO-S-S - PG CH2 Open (Software Detection)",
            "Not Used"],
    "1843": ["Not Used",
            "Not Used",
            "SNAP - Snapped Shaft",
            "LC - Load Check Error",
            "BE1 - Rollback Detected",
            "BE2 - No Current",
            "BE3 - Brake Relase No Good",
            "BE7 - Brake Welded",
            "UL3 - Upper Limit 3",
            "Not Used",
            "Not Used",
            "Not Used",
            "Not Used",
            "Not Used",
            "Not Used",
            "Not Used"
            ]
}

LOG_PATH = "/var/log/collect.log"
log_hdlr = logging.getLogger(__name__)
log_hdlr.setLevel(logging.DEBUG)

hdlr = RotatingFileHandler(LOG_PATH,maxBytes=5 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
hdlr.setFormatter(formatter)
log_hdlr.addHandler(hdlr)

#EStop UUID
try:
    notify_json = {}
    with open("/etc/yconfig.json", "r") as hdlr:
        content = json.loads(hdlr.read())

        notify_json["edge_uuid"] = content["edge_uuid"]
        # As this event is global event, motor_uuid is replaced with edge_uuid
        notify_json["motor_uuid"] = content["edge_uuid"]
        notify_json["event_name"] = "E-stop"
        notify_json["event_action"] = 3
        notify_json["event_uuid"] = None
        if "event_details" in content:
            events = content["event_details"]

            if events:
                for event in events:
                    if event["event_name"] == "E-stop":
                        notify_json["event_uuid"] = event["event_uuid"]

        if not notify_json["event_uuid"]:
            raise Exception("Configuration Missing")
except Exception as err:
    log_hdlr.info("Read E-stop Event Failed: {}".format(err))
    sys.exit(2)

class Connect_Modbus:

    def __init__(self, modbus_type, vfd_addr, port, rate=115200):
        self.type = modbus_type
        self.vfd_addr = vfd_addr
        self.port = port
        self.rate = int(rate)

    def connect(self):
        try:
            if self.type != 'rtu':
                print("Not supported type")
            else:
                self.client = ModbusClient(method=self.type, port=self.port, timeout=1, baudrate=self.rate)
                log_hdlr.info(self.client.connect())
                print(self.client)
        except:
            pass

    def read(self, start_addr, count):
        resp = self.client.read_yw_registers(start_addr, count, unit=int(self.vfd_addr, 16))
        print(resp)
        return resp.registers


def generate_test_data():
    from random import randint
    datapoints = []
    datapoint = {}

    datapoint["k"] = "motor_speed"
    datapoint["v"] = randint(200,300)
    motor_speed = datapoint["v"]
    datapoint["u"] = "Hz"
    datapoint["d"] = "Motor Speed in Hz"
    datapoints.append(datapoint)

    datapoint["k"] = "output_voltage"
    datapoint["v"] = randint(200,500)
    datapoint["u"] = "Volt"
    datapoint["d"] = "Output Voltage"
    datapoints.append(datapoint)

    datapoint["k"] = "dc_bus_voltage"
    datapoint["v"] = randint(200,500)
    datapoint["u"] = "Volt"
    datapoint["d"] = "DC Bus Voltage"
    datapoints.append(datapoint)

    datapoint["k"] = "output_hp"
    datapoint["v"] = randint(1,20)
    datapoint["u"] = "HP"
    datapoint["d"] = "Output Horsepower"
    datapoints.append(datapoint)

    datapoint = {}
    datapoint["k"] = "drive_ready"
    datapoint["v"] = randint(0,1)
    datapoint["d"] = "Drive Ready"
    datapoints.append(datapoint)

    datapoint = {}
    datapoint["k"] = "drive_alarm"
    datapoint["v"] = randint(0,1)
    datapoint["d"] = "Alarm/Minor Fault"
    datapoints.append(datapoint)

    datapoint = {}
    datapoint["k"] = "drive_fault"
    datapoint["v"] = randint(0,1)
    datapoint["d"] = "Major Fault"
    datapoints.append(datapoint)

    datapoint = {}
    datapoint["k"] = "drive_direction"
    datapoint["d"] = "Drive Direction"
    datapoint["v"] = randint(0,3)
    datapoints.append(datapoint)

    datapoint = {}
    datapoint["k"] = "run_time"
    datapoint["v"] = randint(0,100)
    datapoint["u"] = "Minutes"
    datapoint["d"] = "Run Time"   
    datapoints.append(datapoint)

    datapoint = {}
    datapoint["k"] = "motor_amps"
    datapoint["v"] = randint(100,400)/(10*count)
    datapoint["d"] = "Motor Amps"
    datapoints.append(datapoint)

    datapoint = {}
    datapoint["k"] = "number_of_start_stop"
    datapoint["v"] = randint(0,20)
    datapoint["d"] = "Total Motor Start/Stop"
    datapoints.append(datapoint)

    datapoint = {}
    datapoint["k"] = "motor_in_rpm"
    datapoint["v"] = randint(2000,4000)
    motor_in_rpm = datapoint["v"]
    datapoint["d"] = "Motor in RPM"
    datapoints.append(datapoint)

    # To be read from DB, Customer Input.
    reduction_factor = 1
    datapoint = {}
    datapoint["k"] = "speed_in_fpm"
    datapoint["v"] = motor_in_rpm/reduction_factor
    datapoint["d"] = "Speed in FPM"
    datapoints.append(datapoint)

    return datapoints

def connect(vfd_addr, vfd_port, vfd_rate, mode="rtu"):

    drive_obj = Connect_Modbus(mode, vfd_addr, vfd_port, vfd_rate)
    drive_obj.connect()

    return drive_obj

# As of now this function is deprecated. Could be used later with some changes.
def connection_check(vfd_addrs, vfd_port, vfd_rate, edge_uuid, motor_uuid, mode="rtu"):

    while True:
        start_time = round(time.time() * 1000)
        r = True
        conn_chk = ModbusClient(method=mode, port=vfd_port, timeout=1, baudrate=vfd_rate)
        if conn_chk.connect():
            #Read Sample Register from VFD
            #All VFD to be running for reading to work
            for vfd in vfd_addrs:
                resp = conn_chk.read_yw_registers(1288, 1, unit=int(vfd, 16))
                log_hdlr.info("Connection Response for {}: {}".format(vfd, resp))

                if 'Error' in str(resp):
                    r = False
        else:
            log_hdlr.info("USB Port is not connected or having connectivity issues.")
            r = False

        if r is True:
            break
        else:
            data = {}
            data["edge_uuid"] = edge_uuid
            data["total_motors"] = len(motor_uuid[vfd_addr])
            data["timestamp"] = start_time
            data["vfd_status"] = 1
            data["motor_data"] = {}
            for vfd in vfd_addrs:
                for motor in motor_uuid[vfd]:
                    data["motor_uuid"] = motor

                    content = get_motor_data("table", motor_uuid, 0)

                    run_time = 0
                    if not content:
                        pass
                    else:
                        for row in json.loads(content):
                            i = json.loads(row)
                            k = ast.literal_eval(i["motor_data"])
                            for s in k:
                                if s["k"] == "run_time":
                                    run_time = s["v"]

                    datapoint = {}
                    datapoint["k"] = "run_time"
                    datapoint["v"] = run_time
                    datapoint["u"] = "Minutes"
                    datapoint["d"] = "Run Time" 

                    print(json.dumps(data, indent=4, sort_keys=True))
                    ingest_stream(data)

            time.sleep(5)

    return r

def read_faults(vfd_addr):
    fault_list = []
    fault_reg = 1840
    faults = vfd_addr.read(1840, 4)
    for fault in faults:
        for i in range(15):
            if (fault & (1<<i)) >> i:
                fault_list.append(__FAULT_STRINGS__.get(str(fault_reg))[i])
        fault_reg += 1
    return(fault_list)

def read(drive_obj, vfd_addrs, edge_uuid, motor_uuid, motor_type, motor_spl, reduction_factor, labels, load_cell, previous_state, test):

    try:
        try:
            with open("/etc/runtime", "r") as hdlr:
                resp = json.loads(hdlr.read())
        except:
            resp = {}

        counter = {}
        push_counter = {}
        series3_run_time = {}
        previous_state = previous_state
        drive_idle_ts = {}

        motor_list = []
        for i in motor_uuid:
            for x in motor_uuid[i]:
                motor_list.append(x)

        for vfd_addr in vfd_addrs:
            counter[vfd_addr] = 1
            push_counter[vfd_addr] = (1000 / __PULL_INTERVAL__) * 60

            for motor in motor_uuid[vfd_addr]:
                if motor in resp:
                    series3_run_time[motor] = resp[motor]
                else:
                    series3_run_time[motor] = 0

        print("1")
        while True:
            o_start_time = round(time.time() * 1000)
            log_hdlr.info("Previous State {}".format(previous_state))
            error = 0

            try:
                with open("/etc/daq_port1", "r") as hdlr:
                    content = json.loads(hdlr.read())

                if "status" in content:
                    if content["status"] == 8:
                        error = 1
                        log_hdlr.info("Edge Box power is down!!!!")
            except Exception as err:
                log_hdlr.info("DAQ Port1 Check Exception \n{}".format(err))
                pass

            try:
                for vfd_addr in vfd_addrs:
                    if motor_spl[vfd_addr] == 0:
                        term_s6 = drive_obj[vfd_addr].read(43, 1)
                        power = (term_s6[0] & (1<<5)) >> 5

                        if power == 0:
                            msg = {}
                            log_hdlr.info("May Day... May Day..\n")
                            content = get_motor_data("crane_details", motor_list, 0)
                            log_hdlr.info("Last Record \n {}".format(content))

                            for row in json.loads(content):
                                i = json.loads(row)
                                if "vfd_status" in i:
                                    k = i["vfd_status"]
                                    if k == 3 or k == 6:
                                        error = 2
                                        if k == 3:
                                            msg["status"] = 6
                                            msg["timestamp"] = o_start_time
                                        break

                            if error != 2:
                                for row in json.loads(content):
                                    i = json.loads(row)
                                    if "vfd_status" in i:
                                        k = i["vfd_status"]
                                        if k == 5:
                                            error = 3
                                            break
                                if error != 3:
                                    error = 3
                                    msg["status"] = 5
                                    msg["timestamp"] = o_start_time

                            if msg and (error == 2 or error == 3):
                                with open("/etc/daq_port0", "w") as hdlr:
                                    hdlr.write(json.dumps(msg))
            except Exception as err:
                log_hdlr.info("Power Bit Check Exception \n{}".format(err))
                pass

            if error == 1:
                raise Exception("Edge Box power is down!!!!")
            elif error == 2:
                notify_json["created_on"] = round(time.time() * 1000)
                notify_json["action_status"] = False
                ingest_notifications(notify_json)
                raise Exception("Crane is estopped !!!!")
            elif error == 3:
                raise Exception("Crane is manual stopped !!!!")


            print("2")
            for vfd_addr in vfd_addrs:
                start_time = round(time.time() * 1000)
                rawdata = {}
                datapoints = []
                bit0=bit1=bit2=bit5=0

                log_hdlr.info(test)
                if not test:
                    resp = drive_obj[vfd_addr].read(68, 11)
                    rawdata[68] = resp
                    i = 0
                    for reg in resp:
                        datapoint = {}
                        if i == 0:
                            if motor_spl[vfd_addr] == 1:
                                #Hoist Specific Read
                                datapoint["k"] = "motor_speed"
                                datapoint["v"] = reg
                                motor_speed = datapoint["v"]
                                rpm = 1200
                                datapoint["u"] = "Hz"
                                datapoint["d"] = "Motor Speed in Hz"
                                datapoints.append(datapoint)
                            elif motor_spl[vfd_addr] == 0:
                                #Bridge Specific Read
                                speed = drive_obj[vfd_addr].read(65, 1)
                                datapoint["k"] = "motor_speed"
                                datapoint["v"] = speed[0]
                                motor_speed = datapoint["v"]
                                rpm = 1800
                                datapoint["u"] = "Hz"
                                datapoint["d"] = "Motor Speed in Hz"
                                datapoints.append(datapoint)
                        elif i == 1:
                            datapoint["k"] = "output_voltage"
                            datapoint["v"] = reg
                            datapoint["u"] = "Volt"
                            datapoint["d"] = "Output Voltage"
                            datapoints.append(datapoint)
                        elif i == 2:
                            datapoint["k"] = "dc_bus_voltage"
                            datapoint["v"] = reg
                            datapoint["u"] = "Volt"
                            datapoint["d"] = "DC Bus Voltage"
                            datapoints.append(datapoint)
                        elif i == 3:
                            datapoint["k"] = "output_hp"
                            datapoint["v"] = reg
                            datapoint["u"] = "HP"
                            datapoint["d"] = "Output Horsepower"
                            datapoints.append(datapoint)
                        elif i == 7:
                            bit0 = (reg & (1<<0)) >> 0
                            bit1 = (reg & (1<<1)) >> 1
                            bit2 = (reg & (1<<2)) >> 2
                            bit5 = (reg & (1<<5)) >> 5
                            datapoint = {}
                            datapoint["k"] = "drive_ready"
                            datapoint["v"] = (reg & (1<<5)) >> 5
                            datapoint["d"] = "Drive Ready"
                            datapoints.append(datapoint)

                            datapoint = {}
                            datapoint["k"] = "drive_alarm"
                            datapoint["v"] = (reg & (1<<6)) >> 6
                            datapoint["d"] = "Alarm/Minor Fault"
                            datapoints.append(datapoint)

                            datapoint = {}
                            datapoint["k"] = "drive_fault"
                            datapoint["v"] = (reg & (1<<7)) >> 7
                            fault = (reg & (1<<7)) >> 7
                            datapoint["d"] = "Major Fault"
                            datapoints.append(datapoint)

                            if fault:
                                #Check for the faults registery
                                resp = read_faults(drive_obj[vfd_addr])
                                datapoint = {}
                                datapoint["k"] = "drive_fault_list"
                                datapoint["v"] = resp
                                datapoint["d"] = "Fault List"
                                datapoints.append(datapoint)

                        elif i == 10 and motor_type == 1:
                            datapoint = {}
                            datapoint["k"] = "run_time"
                            datapoint["v"] = reg * 60
                            datapoint["u"] = "Minutes"
                            datapoint["d"] = "Run Time"   
                            datapoints.append(datapoint)
                        i+=1                   
                    

                    print("3")
                    resp = drive_obj[vfd_addr].read(38, 1)
                    datapoint = {}
                    rawdata[38] = resp
                    motor_amps_raw = resp[0]
                    datapoint["k"] = "motor_amps"
                    datapoint["v"] = resp[0]/(10*len(motor_uuid[vfd_addr]))
                    datapoint["d"] = "Motor Amps"
                    datapoints.append(datapoint)

                    datapoint = {}
                    datapoint["k"] = "drive_direction"
                    datapoint["d"] = "Drive Direction"
                    if bit0 == 1 and bit1 == 0 and bit2 == 0 and motor_amps_raw > 0:
                        datapoint["v"] = labels[vfd_addr][0] + " Running"
                    elif bit0 == 1 and bit1 == 0 and bit2 == 1 and motor_amps_raw > 0:
                        datapoint["v"] = labels[vfd_addr][1] + " Running"
                    datapoints.append(datapoint)
                    

                    print("4")
                    if motor_type[vfd_addr] == 0:
                        if bit0 == 1 and bit1 == 0 and motor_amps_raw > 0:
                            push_counter[vfd_addr] -= 1

                        run_time = series3_run_time[motor_uuid[vfd_addr][0]]

                        if int(push_counter[vfd_addr]) == 0:
                            push_counter[vfd_addr] = (1000 / __PULL_INTERVAL__) * 60
                            series3_run_time[motor_uuid[vfd_addr][0]] += 1
                            
                            try:
                                with open("/etc/runtime", "r") as hdlr:
                                    resp = json.loads(hdlr.read())
                            except:
                                resp = {}
                            finally:
                                resp[motor_uuid[vfd_addr][0]] = series3_run_time[motor_uuid[vfd_addr][0]]
                                with open("/etc/runtime", "w") as hdlr:
                                    hdlr.write(json.dumps(resp))

                        print("5")
                        datapoint = {}
                        datapoint["k"] = "run_time"
                        datapoint["v"] = run_time
                        datapoint["u"] = "Minutes"
                        datapoint["d"] = "Run Time"   
                        datapoints.append(datapoint)  

                    if motor_type[vfd_addr] == 1:
                        resp = drive_obj[vfd_addr].read(117, 1)
                        rawdata[117] = resp
                    elif motor_type[vfd_addr] == 0:
                        resp = drive_obj[vfd_addr].read(2068, 1)
                        rawdata[2068] = resp
                    else:
                        resp = drive_obj[vfd_addr].read(117, 1)
                        rawdata[117] = resp
                    datapoint = {}
                    datapoint["k"] = "number_of_start_stop"
                    datapoint["v"] = resp[0]
                    datapoint["d"] = "Total Motor Start/Stop"
                    datapoints.append(datapoint)

                    resp = drive_obj[vfd_addr].read(1797, 1)
                    datapoint = {}
                    rawdata[1797] = resp
                    datapoint["k"] = "motor_in_rpm"
                    datapoint["v"] = ((motor_speed/resp[0])*rpm)/10
                    motor_in_rpm = datapoint["v"]
                    datapoint["d"] = "Motor in RPM"
                    datapoints.append(datapoint)

                    print("6")
                    datapoint = {}
                    datapoint["k"] = "speed_in_fpm"
                    datapoint["v"] = motor_in_rpm/reduction_factor[vfd_addr]
                    datapoint["d"] = "Speed in FPM"
                    datapoints.append(datapoint)

                    resp = drive_obj[vfd_addr].read(27, 1)
                    datapoint = {}
                    rawdata[27] = resp
                    value = []
                    if (resp[0] & (1<<8)) >> 8:
                        value.append(labels[vfd_addr][0] + " Stop")
                    elif (resp[0] & (1<<9)) >> 9:
                        value.append(labels[vfd_addr][1] + " Stop")
                    elif (resp[0] & (1<<10)) >> 10:
                        value.append(labels[vfd_addr][0] + " Slow Down")
                    elif (resp[0] & (1<<11)) >> 11:
                        value.append(labels[vfd_addr][1] + " Slow Down")
                    elif (resp[0] & (1<<15)) >> 15:
                        value.append(labels[vfd_addr][0] + " Weighted")
                    datapoint["k"] = "limit_switch"
                    datapoint["v"] = value
                    datapoint["d"] = "Limit Switch"
                    datapoints.append(datapoint)

                    print("7")
                    if vfd_addr in load_cell:
                        if load_cell[vfd_addr]:
                            lc = load_cell[vfd_addr][0].split(",")

                            resp = drive_obj[vfd_addr].read(int(lc[0]), 1)
                            analog_data = resp[0]
                            status = 0

                            if len(lc) > 1:
                                if int(lc[1]) == 1:
                                    crane_weight = (float(lc[3]) * analog_data) + float(lc[4])
                                elif int(lc[1]) == 2:
                                    crane_weight = (float(lc[2]) * (analog_data^2)) + (float(lc[3]) * analog_data) + float(lc[4])
                            else:
                                crane_weight = 0
                                status = 1

                            datapoint = {}
                            datapoint["k"] = "loadcell"
                            datapoint["v"] = {"status":status, "analog_data": analog_data, "crane_weight":crane_weight}
                            datapoint["u"] = {"analog_data":"Counts", "crane_weight":str(lc[5])}
                            datapoints.append(datapoint)

                    if bit0 == 0 and bit1 == 0 and bit5 == 0:
                        vfd_status = 10
                    elif bit0 == 0 and bit1 == 0 and bit5 == 1:
                        vfd_status = 11
                    elif bit0 == 0 and bit1 == 1 and bit5 == 0 and motor_amps_raw == 0:
                        vfd_status = 4
                    elif bit0 == 0 and bit1 == 1 and bit5 == 1 and motor_amps_raw == 0:
                        vfd_status = 2
                    elif bit0 == 1 and bit1 == 0 and bit5 == 0:
                        vfd_status = 11
                    elif bit0 == 1 and bit1 == 0 and bit5 == 1 and motor_amps_raw > 0:
                        vfd_status = 3
                    elif bit0 == 1 and bit1 == 1 and bit5 == 0:
                        vfd_status = 11
                    elif bit0 == 1 and bit1 == 1 and bit5 == 1 and motor_amps_raw > 0:
                        vfd_status = 9
                    elif bit0 == 1 and bit1 == 1 and bit5 == 1 and motor_amps_raw == 0:
                        vfd_status = 12
                    else:
                        vfd_status = -1
                else:
                    datapoints = generate_test_data()
                    vfd_status = -1

                    
                print("8")
                data = {}
                data["edge_uuid"] = edge_uuid
                data["total_motors"] = len(motor_uuid[vfd_addr])
                data["timestamp"] = start_time
                data["vfd_status"] = vfd_status
                data["motor_data"] = datapoints

                print("9")
                for motor in motor_uuid[vfd_addr]:
                    data["motor_uuid"] = motor
                    log_hdlr.info("Raw Data {} : {}".format(start_time, rawdata))
                    print(json.dumps(data, indent=4, sort_keys=True))
                    ingest_stream(data)

                print("10")
                end_time = round(time.time() * 1000)
                lapsed_time = end_time - start_time
                log_hdlr.info("Total Lapsed Time For Drive {} is {}".format(vfd_addr, lapsed_time))
                previous_state = 0

            o_end_time = round(time.time() * 1000)
            o_lapsed_time = o_end_time - o_start_time
            time.sleep((__PULL_INTERVAL__- o_lapsed_time)/1000)
    except Exception as err:
        log_hdlr.info("Error in datapoints collections (read or dummy){}".format(err))
        time.sleep(1)
        data = {}
        vfd_status = 1

        try:
            with open("/etc/daq_port1", "r") as hdlr:
                content = json.loads(hdlr.read())

            if "status" in content:
                vfd_status = content["status"]
                start_time = content["timestamp"] + 500
        except:
            pass

        try:
            with open("/etc/daq_port0", "r") as hdlr:
                content = json.loads(hdlr.read())

            if "status" in content:
                vfd_status = content["status"]
                start_time = content["timestamp"] + 500
        except:
            pass

        log_hdlr.info("VFD Status {}".format(vfd_status))

        if previous_state != vfd_status:
            for vfd_addr in vfd_addrs:
                data["edge_uuid"] = edge_uuid
                data["total_motors"] = len(motor_uuid[vfd_addr])
                data["timestamp"] = start_time
                data["vfd_status"] = vfd_status
                data["motor_data"] = []

                for motor in motor_uuid[vfd_addr]:
                    data["motor_uuid"] = motor
                    print(json.dumps(data, indent=4, sort_keys=True))
                    ingest_stream(data)
                    previous_state = vfd_status

        time.sleep(4)

        read(drive_obj, vfd_addrs, edge_uuid, motor_uuid, motor_type, motor_spl, reduction_factor, labels, load_cell, previous_state, test)

def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', action='store', help='VFD Comm Address', nargs="+", type=str)
    parser.add_argument('-p', action='store', help='ModBus RTU Comm Port', type=str)
    parser.add_argument('-r', action='store', help='ModBus RTU Baud Rate', type=int, default=115200)
    parser.add_argument('-eu', action='store', help='Edge UUID', type=str)
    parser.add_argument('-mu', action='store', help='Motor UUID', nargs="+", type=str)
    parser.add_argument('-mt', action='store', help='Motor Type', nargs="+", type=str)
    parser.add_argument('-ms', action='store', help='Motor Speciality', nargs="+", type=str)
    parser.add_argument('-rf', action='store', help='Motor Reduction Factor', nargs="+", type=str)
    parser.add_argument('-lc', action='store', help='Load Cell Config', nargs="+", type=str)
    parser.add_argument('-lb', action='store', help='Label Config', nargs="+", type=str)
    parser.add_argument('-m', action='store', help='Test Data', type=int)

    return parser.parse_args()

if __name__ == "__main__":

    args = getargs()
    vfd_addrs = args.a
    vfd_port = args.p
    vfd_rate = args.r
    edge_uuid = args.eu
    motor_uuid = args.mu
    motor_types = args.mt
    motor_spls = args.ms
    reduction_factors = args.rf
    load_cell = args.lc
    label_conf = args.lb
    test = args.m

    motor_map = {}
    for vfd_addr in vfd_addrs:
        motor_list = []
        for motors in motor_uuid:
            if vfd_addr in motors:
                motor_list.append(motors.split(':')[1])
        motor_map[vfd_addr] = motor_list

    type_map = {}
    for vfd_addr in vfd_addrs:
        for motor_type in motor_types:
            if vfd_addr in motor_type:
                type_map[vfd_addr] = int(motor_type.split(':')[1])

    spl_map = {}
    for vfd_addr in vfd_addrs:
        for motor_spl in motor_spls:
            if vfd_addr in motor_spl:
                spl_map[vfd_addr] = int(motor_spl.split(':')[1])

    rf_map = {}
    for vfd_addr in vfd_addrs:
        for rf in reduction_factors:
            if vfd_addr in rf:
                rf_map[vfd_addr] = float(rf.split(':')[1])

    lb_map = {}
    for vfd_addr in vfd_addrs:
        lb_map[vfd_addr] = []
        for lb in label_conf:
            if vfd_addr in lb:
                lb_map[vfd_addr].append(lb.split(':')[1])

    lc_map = {}
    for vfd_addr in vfd_addrs:
        lc_map[vfd_addr] = []
        for lc in load_cell:
            if vfd_addr in lc:
                lc_map[vfd_addr].append(lc.split(':')[1])

    log_hdlr.info(args)

    if not test:
      drive_obj_map = {}
      for vfd_addr in vfd_addrs:
          drive_obj_map[vfd_addr] = connect(vfd_addr, vfd_port, vfd_rate, "rtu")

      read(drive_obj_map, vfd_addrs, edge_uuid, motor_map, type_map, spl_map, rf_map, lb_map, lc_map, "Connected", test)
    else:
        read(False, vfd_addrs, edge_uuid, motor_map, type_map, rf_map, spl_map, rf_map, lb_map, lc_map, "Connected", test)

