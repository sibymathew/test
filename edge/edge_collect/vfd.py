from vilimbu.client.sync import ModbusSerialClient as ModbusClient
from edge_loader import ingest_stream,ingest_stream2
from edge_loader import get_motor_data

import argparse
import json
import time
import logging
from logging.handlers import RotatingFileHandler
import ast

__PULL_INTERVAL__ = 250
__SAMPLES_PER_SECOND__ = 1000/250

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
        resp = self.client.read_holding_registers(start_addr, count, unit=int(self.vfd_addr, 16))
        print(resp)
        return resp.registers

def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', action='store', help='VFD Comm Address', type=str)
    parser.add_argument('-p', action='store', help='ModBus RTU Comm Port', type=str)
    parser.add_argument('-r', action='store', help='ModBus RTU Baud Rate', type=int, default=115200)
    parser.add_argument('-eu', action='store', help='Edge UUID', type=str)
    parser.add_argument('-mu', action='store', help='Motor UUID', nargs="+", type=str)
    parser.add_argument('-mt', action='store', help='Motor Type', type=int)
    parser.add_argument('-rf', action='store', help='Motor Reduction Factor', type=float)
    parser.add_argument('-c', action='store', help='Total Motors', type=int)
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
    datapoint["u"] = "TBD"
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

def read(drive_obj, edge_uuid, motor_uuid, count, motor_type, reduction_factor, test):

    counter = 1
    push_counter = (1000 / __PULL_INTERVAL__) * 60

    # To get the latest record for each motor
    content = get_motor_data("table", motor_uuid, 0)

    if not json.loads(content):
        run_time = 0
    else:
        for row in json.loads(content):
            i = json.loads(row)
            k = ast.literal_eval(i["motor_data"])
            for s in k:
                if s["k"] == "run_time":
                    run_time = s["v"]
                    break

    while True:
        start_time = round(time.time() * 1000)
        datapoints = []

        log_hdlr.info(test)
        if not test:
            resp = drive_obj.read(68, 11)
            i = 0
            for reg in resp:
                datapoint = {}
                if i == 0:
                    datapoint["k"] = "motor_speed"
                    datapoint["v"] = reg
                    motor_speed = datapoint["v"]
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

            if motor_type == 0:
                if direction == 1 or direction == 3 or direction == 5 or direction == 7:
                    push_counter -= 1
                    if push_counter == 0:
                        push_counter = (1000 / __PULL_INTERVAL__) * 60
                        # To get the latest record for each motor
                        content = get_motor_data("table", motor_uuid, 0)

                        if not json.loads(content):
                            run_time = 0
                        else:
                            for row in json.loads(content):
                                i = json.loads(row)
                                k = ast.literal_eval(i["motor_data"])
                                for s in k:
                                    if s["k"] == "run_time":
                                        run_time = s["v"]
                                        break

                            run_time += 1

                    datapoint = {}
                    datapoint["k"] = "run_time"
                    datapoint["v"] = run_time
                    datapoint["u"] = "Minutes"
                    datapoint["d"] = "Run Time"   
                    datapoints.append(datapoint)                        

            resp = drive_obj.read(38, 1)
            datapoint = {}
            datapoint["k"] = "motor_amps"
            datapoint["v"] = resp[0]/(10*count)
            datapoint["d"] = "Motor Amps"
            datapoints.append(datapoint)

            if motor_type == 1:
                resp = drive_obj.read(117, 1)
            elif motor_type == 0:
                resp = drive_obj.read(2068, 1)
            else:
                resp = drive_obj.read(117, 1)
            datapoint = {}
            datapoint["k"] = "number_of_start_stop"
            datapoint["v"] = resp[0]
            datapoint["d"] = "Total Motor Start/Stop"
            datapoints.append(datapoint)

            resp = drive_obj.read(1797, 3)
            datapoint = {}
            datapoint["k"] = "motor_in_rpm"
            datapoint["v"] = (motor_speed/resp[0])*resp[2]
            motor_in_rpm = datapoint["v"]
            datapoint["d"] = "Motor in RPM"
            datapoints.append(datapoint)

            datapoint = {}
            datapoint["k"] = "speed_in_fpm"
            datapoint["v"] = motor_in_rpm/reduction_factor
            datapoint["d"] = "Speed in FPM"
            datapoints.append(datapoint)

        else:
            datapoints = generate_test_data()

        data = {}
        data["edge_uuid"] = edge_uuid
        data["total_motors"] = count
        data["timestamp"] = start_time
        data["motor_data"] = datapoints

        for motor in motor_uuid:
            data["motor_uuid"] = motor
            print(json.dumps(data, indent=4, sort_keys=True))
            ingest_stream(data)

        if counter == __SAMPLES_PER_SECOND__:
            for motor in motor_uuid:
                data["motor_uuid"] = motor
                ingest_stream2(data)
            counter = 1
        else:
            counter += 1

        end_time = round(time.time() * 1000)
        lapsed_time = end_time - start_time
        log_hdlr.info("Total Lapsed Time {}".format(lapsed_time))

        time.sleep((__PULL_INTERVAL__-lapsed_time)/1000)

if __name__ == "__main__":

    args = getargs()
    vfd_addr = args.a
    vfd_port = args.p
    vfd_rate = args.r
    edge_uuid = args.eu
    motor_uuid = args.mu
    motor_type = args.mt
    reduction_factor = args.rf
    count = args.c
    test = args.m

    log_hdlr.info(args)

    while True:
        if not test:
          try:
              drive_obj = connect(vfd_addr, vfd_port, vfd_rate, "rtu")
          except Exception as err:
              log_hdlr.info("Error in connection \n {}".format(err))
              time.sleep(5)
          else:
              try:
                  read(drive_obj, edge_uuid, motor_uuid, count, motor_type, reduction_factor, test)
              except Exception as err:
                  log_hdlr.info("Error in reading \n {}".format(err))
                  time.sleep(5)
        else:
            try:
                read(False, edge_uuid, motor_uuid, count, motor_type, reduction_factor, test)
            except Exception as err:
                log_hdlr.info("Error in reading \n {}".format(err))
                time.sleep(5)

