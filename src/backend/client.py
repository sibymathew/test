from paho.mqtt import client as mqtt
import ssl
import data_structure
from data_collector import reduced_test_data 
import json, time
from plc import read_tags
from pycomm3 import LogixDriver
import argparse

path_to_root_cert = "./digi.crt"
#device_id = "plc_data_collector"
#sas_token = "SharedAccessSignature sr=siby-iothub.azure-devices.net%2Fdevices%2Fplc_data_collector&sig=wgzNjjZdzuMyeHVQFKh3pb0XCQf4QDDmNSNJ5zxlPGY%3D&se=1612551913"
#iot_hub_name = "siby-iothub"
#plc_tag_name = "F71"
#plc_ip_addr = "10.0.0.180"

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

                    msg = test_data(data_structure.device_to_cloud)
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

    collect_and_publish(args.mode, "None", "None", args.iothub, args.iotdevice, args.iotdevicesastoken)
    
if __name__ == '__main__':
    main()
