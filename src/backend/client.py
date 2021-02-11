from paho.mqtt import client as mqtt
import ssl
import data_structure
from data_collector import reduced_test_data 
from data_collector import enumerate_data
import json, time
from plc import read_tags
from pycomm3 import LogixDriver
import argparse
import sys
from db import Database

path_to_root_cert = "src/backend/digi.crt"

def collect_and_publish(mode="test", plc_ip_addr=None, plc_tag_name=None, iot_hub_name=None, device_id=None, sas_token=None):

    def on_connect(client, userdata, flags, rc):
        print("Device connected with result code: " + str(rc))

    def on_disconnect(client, userdata, rc):
        print("Device disconnected with result code: " + str(rc))

    def on_publish(client, userdata, mid):
        print("Device sent message")

    client = mqtt.Client(client_id=device_id, protocol=mqtt.MQTTv311)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish

    client.username_pw_set(username=iot_hub_name+".azure-devices.net/" +
                           device_id + "/?api-version=2018-06-30", password=sas_token)

    client.tls_set(ca_certs=path_to_root_cert, certfile=None, keyfile=None,
                   cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
    client.tls_insecure_set(False)

    client.connect(iot_hub_name+".azure-devices.net", port=8883)

    i = 0
    while True:
        time.sleep(5)
        i+=1
        if i < 101:
            if mode != "test":
                with LogixDriver(plc_ip_addr) as plc:
                    # return the value as dict for the given Tag
                    resp = plc.read(plc_tag_name)

                    result = {}
                    result["Data"] = resp[1]['Data']
                    msg = enumerate_data(resp[1]['Data'], 155, 3)
                    result["Msg"] = msg

                    data = Database('data.json')
                    length= data.length()
                    result["index"] = length + 1
                    data.insert(result)

            else:
                msg = reduced_test_data(data_structure.reduced_device_to_cloud)

            client.publish("devices/" + device_id + "/messages/events/", json.dumps(msg), qos=1)
        else:
            break

    client.loop_forever()

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-m', '--mode', action='store', help="test or realtime")
    parser.add_argument('-i', '--ipaddr', action='store', help="plc ip address")
    parser.add_argument('-t', '--tagname', action='store', help="plc tag name")
    parser.add_argument('-ih', '--iothub', action='store', help="iot hub name")
    parser.add_argument('-id', '--iotdevice', action='store', help="iot device name")
    parser.add_argument('-idt', '--iotdevicesastoken', action='store', help="iot device sas token")

    args = parser.parse_args()

    if len(sys.argv)<1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    if args.ipaddr and args.tagname:
        collect_and_publish(args.mode, args.ipaddr, args.tagname, args.iothub, args.iotdevice, args.iotdevicesastoken)
    else:
        collect_and_publish(args.mode, "None", "None", args.iothub, args.iotdevice, args.iotdevicesastoken)
    
if __name__ == '__main__':
    main()
