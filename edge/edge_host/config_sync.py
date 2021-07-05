import sys
import os
import time
import notecard

from periphery import Serial
#import serial

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
        #port = serial.Serial(nodeport, noderate)
    except Exception as exception:
        raise Exception("error opening port: "+ exception)

    print("Opening Notecard...")
    try:
        card = notecard.OpenSerial(port)

        while True:
            req = {"req":"hub.sync"}
            card.Transaction(req)

            req = {"req":"hub.sync.status"}
            card.Transaction(req)

            req = {"req":"note.get", "file":"data.qi", "delete":True}
            while True:
                print(card.Transaction(req))
                time.sleep(60)
    except Exception as exception:
        raise Exception("error opening notecard: " + exception)

main()
