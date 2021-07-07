from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from edge_loader import ingest_stream

import argparse
import json
import time
import logging

__PULL_INTERVAL__ = 250
__SAMPLES_PER_SECOND__ = 1000/250

class Connect_Modbus:

    def __init__(self, modbus_type, vfd_addr, port, rate=115200):
        self.type = modbus_type
        self.vfd_addr = vfd_addr
        self.port = port
        self.rate = int(rate)

    def connect(self):
        print("{} {} {} {}".format(self.type, self.vfd_addr, self.port, self.rate))
        try:
            if self.type != 'rtu':
                print("Not supported type")
            else:
                self.client = ModbusClient(method=self.type, port=self.port, timeout=1, baudrate=self.rate)
                print(self.client.connect())
                print(self.client)
        except:
            pass

    def read(self, start_addr, count):
        resp = self.client.read_holding_registers(start_addr, count, unit=0x1F)
        print(resp)
        return resp.registers

def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', action='store', help='VFD Comm Address', type=str)
    parser.add_argument('-p', action='store', help='ModBus RTU Comm Port', type=str)
    parser.add_argument('-r', action='store', help='ModBus RTU Baud Rate', type=int, default=115200)
    parser.add_argument('-eu', action='store', help='Edge UUID', type=str)
    parser.add_argument('-mu', action='store', help='Motor UUID', type=str)
    parser.add_argument('-c', action='store', help='Total Motors', type=int)

    return parser.parse_args()

def connect(mode="rtu", vfd_addr, vfd_port, vfd_rate):

    drive_obj = Connect_Modbus(mode, vfd_addr, vfd_port, vfd_rate)
    drive_obj.connect()

    return drive_obj

def read(drive_obj, edge_uuid, motor_uuid, count):

    counter = 0
    while True:
      start_time = round(time.time() * 1000)
      datapoints = []
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
              if direction == 1:
                  datapoint["v"] = 0
              elif direction == 5:
                  datapoint["v"] = 1
              datapoints.append(datapoint)
          elif i == 10:
              datapoint = {}
              datapoint["k"] = "run_time"
              datapoint["v"] = reg
              datapoint["u"] = "TBD"
              datapoint["d"] = "Run Time"   
              datapoints.append(datapoint)
          i+=1

      resp = drive_obj.read(38, 1)
      datapoint = {}
      datapoint["k"] = "motor_amps"
      datapoint["v"] = resp[0]/10
      datapoint["d"] = "Motor Amps"
      datapoints.append(datapoint)

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

      # To be read from DB, Customer Input.
      reduction_factor = 1
      datapoint = {}
      datapoint["k"] = "speed_in_fpm"
      datapoint["v"] = motor_in_rpm/reduction_factor
      datapoint["d"] = "Speed in FPM"
      datapoints.append(datapoint)

      data = {}
      data["edge_uuid"] = edge_uuid
      data["motor_uuid"] = motor_uuid
      data["total_motors"] = count
      data["timestamp"] = start_time
      data["motor_data"] = datapoints

      print(json.dumps(data, indent=4, sort_keys=True))

      ingest_stream(data)
      if counter == __SAMPLES_PER_SECOND__:
          #Another table for one second data storage
          ingest_stream(data)
          counter = 0
      else:
          counter += 1

      end_time = round(time.time() * 1000)
      lapsed_time = end_time - start_time
      print("Total Lapsed Time {}".format(lapsed_time))

      time.sleep((__PULL_INTERVAL__-lapsed_time)/1000)

if __name__ == "__main__":

    args = getargs()
    vfd_addr = args.a
    vfd_port = args.p
    vfd_rate = args.r
    edge_uuid = args.eu
    motor_uuid = args.mu
    count = args.c

    while True:
        try:
          drive_obj = connect("rtu", vfd_addr, vfd_port, vfd_rate)
        except Exception as err:
          print("Error in connection \n {}".format(err.message))
          time.sleep(5)
        else:
            try:
              read(drive_obj, edge_uuid, motor_uuid, count)
            except Exception as err:
              print("Error in reading \n {}".format(err.message))
              time.sleep(5)

