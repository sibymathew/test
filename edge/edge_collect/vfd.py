from yw.edge.interface import YWSerialClient as ModbusClient
from edge_loader import ingest_stream,ingest_stream2
from edge_loader import get_motor_data

import argparse
import json
import time
import logging
from logging.handlers import RotatingFileHandler
import ast

__PULL_INTERVAL__ = 1000
__SAMPLES_PER_SECOND__ = (1000/1000)*30 

LOG_PATH = "/var/log/collect.log"
log_hdlr = logging.getLogger(__name__)
log_hdlr.setLevel(logging.DEBUG)

hdlr = RotatingFileHandler(LOG_PATH,maxBytes=5 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
hdlr.setFormatter(formatter)
log_hdlr.addHandler(hdlr)

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
    parser.add_argument('-m', action='store', help='Test Data', type=int)

    return parser.parse_args()

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
            data["vfd_status"] = "Not Reachable"
            data["motor_data"] = {}
            for vfd in vfd_addrs:
                for motor in motor_uuid[vfd]:
                    data["motor_uuid"] = motor
                    print(json.dumps(data, indent=4, sort_keys=True))
                    ingest_stream(data)

            time.sleep(5)

    return r

def read(drive_obj, vfd_addrs, edge_uuid, motor_uuid, motor_type, motor_spl, reduction_factor, test):

    try:
        run_time = {}
        counter = {}
        push_counter = {}
        for vfd_addr in vfd_addrs:
            run_time[vfd_addr] = 0
            counter[vfd_addr] = 1
            push_counter[vfd_addr] = (1000 / __PULL_INTERVAL__) * 60


        while True:
            for vfd_addr in vfd_addrs:
                start_time = round(time.time() * 1000)
                datapoints = []

                log_hdlr.info(test)
                if not test:
                    resp = drive_obj[vfd_addr].read(68, 11)
                    i = 0
                    for reg in resp:
                        datapoint = {}
                        if i == 0:
                            if motor_spl[vfd_addr] == 1:
                                datapoint["k"] = "motor_speed"
                                datapoint["v"] = reg
                                motor_speed = datapoint["v"]
                                rpm = 1200
                                datapoint["u"] = "Hz"
                                datapoint["d"] = "Motor Speed in Hz"
                                datapoints.append(datapoint)
                            elif motor_spl[vfd_addr] == 0:
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
                            datapoint["d"] = "Major Fault"
                            datapoints.append(datapoint)

                            datapoint = {}
                            direction = reg & 5
                            datapoint["k"] = "drive_direction"
                            datapoint["d"] = "Drive Direction"
                            if direction == 1 or direction == 3:
                                datapoint["v"] = 0
                            elif direction == 5 or direction == 7:
                                datapoint["v"] = 1
                            else:
                              #Drive is stopped
                              datapoint["v"] = 3
                            datapoints.append(datapoint)
                        elif i == 10 and motor_type == 1:
                            datapoint = {}
                            datapoint["k"] = "run_time"
                            datapoint["v"] = reg * 60
                            datapoint["u"] = "Minutes"
                            datapoint["d"] = "Run Time"   
                            datapoints.append(datapoint)
                        i+=1

                    print("here1")
                    
                    if motor_type[vfd_addr] == 0:
                        if direction == 1 or direction == 3 or direction == 5 or direction == 7:
                            push_counter[vfd_addr] -= 1

                        print(motor_uuid[vfd_addr])
                        content = get_motor_data("table", motor_uuid[vfd_addr], 0)

                        print(content)
                        if not content:
                            pass
                            #run_time = 0
                        else:
                            for row in json.loads(content):
                                i = json.loads(row)
                                k = ast.literal_eval(i["motor_data"])
                                for s in k:
                                    if s["k"] == "run_time":
                                        run_time[vfd_addr] = s["v"]

                        if push_counter[vfd_addr] == 0:
                            push_counter[vfd_addr] = (1000 / __PULL_INTERVAL__) * 60
                            run_time[vfd_addr] += 1

                        print("here1.2")
                        datapoint = {}
                        datapoint["k"] = "run_time"
                        datapoint["v"] = run_time[vfd_addr]
                        datapoint["u"] = "Minutes"
                        datapoint["d"] = "Run Time"   
                        datapoints.append(datapoint)                        
                    

                    print("here2")
                    resp = drive_obj[vfd_addr].read(38, 1)
                    datapoint = {}
                    datapoint["k"] = "motor_amps"
                    datapoint["v"] = resp[0]/(10*len(motor_uuid[vfd_addr]))
                    datapoint["d"] = "Motor Amps"
                    datapoints.append(datapoint)

                    if motor_type[vfd_addr] == 1:
                        resp = drive_obj[vfd_addr].read(117, 1)
                    elif motor_type[vfd_addr] == 0:
                        resp = drive_obj[vfd_addr].read(2068, 1)
                    else:
                        resp = drive_obj[vfd_addr].read(117, 1)
                    datapoint = {}
                    datapoint["k"] = "number_of_start_stop"
                    datapoint["v"] = resp[0]
                    datapoint["d"] = "Total Motor Start/Stop"
                    datapoints.append(datapoint)

                    resp = drive_obj[vfd_addr].read(1797, 1)
                    datapoint = {}
                    datapoint["k"] = "motor_in_rpm"
                    datapoint["v"] = ((motor_speed/resp[0])*rpm)/10
                    motor_in_rpm = datapoint["v"]
                    datapoint["d"] = "Motor in RPM"
                    datapoints.append(datapoint)

                    print("here3")
                    datapoint = {}
                    datapoint["k"] = "speed_in_fpm"
                    datapoint["v"] = motor_in_rpm/reduction_factor[vfd_addr]
                    datapoint["d"] = "Speed in FPM"
                    datapoints.append(datapoint)

                else:
                    datapoints = generate_test_data()

                print("here4")
                data = {}
                data["edge_uuid"] = edge_uuid
                data["total_motors"] = len(motor_uuid[vfd_addr])
                data["timestamp"] = start_time
                data["vfd_status"] = "Reachable"
                data["motor_data"] = datapoints

                print("here5")
                for motor in motor_uuid[vfd_addr]:
                    data["motor_uuid"] = motor
                    print(json.dumps(data, indent=4, sort_keys=True))
                    ingest_stream(data)

                print("here6")
                if counter[vfd_addr] == __SAMPLES_PER_SECOND__:
                    for motor in motor_uuid[vfd_addr]:
                        data["motor_uuid"] = motor
                        ingest_stream2(data)
                    counter[vfd_addr] = 1
                else:
                    counter[vfd_addr] += 1

                print("here7")
                end_time = round(time.time() * 1000)
                lapsed_time = end_time - start_time
                log_hdlr.info("Total Lapsed Time For Drive {} is {}".format(vfd_addr, lapsed_time))

                time.sleep((__PULL_INTERVAL__-lapsed_time)/1000)
    except Exception as err:
        log_hdlr.info("Error in datapoints collections (read or dummy){}".format(err))
        time.sleep(5)
        read(drive_obj, vfd_addrs, edge_uuid, motor_uuid, motor_type, motor_spl, reduction_factor, test)

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

    log_hdlr.info(args)

    if not test:
      r = connection_check(vfd_addrs, vfd_port, vfd_rate, edge_uuid, motor_map, "rtu")
      if r is True:
          drive_obj_map = {}
          for vfd_addr in vfd_addrs:
              drive_obj_map[vfd_addr] = connect(vfd_addr, vfd_port, vfd_rate, "rtu")

          read(drive_obj_map, vfd_addrs, edge_uuid, motor_map, type_map, spl_map, rf_map, test)
    else:
        read(False, vfd_addrs, edge_uuid, motor_map, type_map, rf_map, spl_map, test)
