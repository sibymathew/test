from subprocess import Popen, PIPE
import time

def check_signal(motor_list):
	resp = Popen(["./StaticDI"], stdout=PIPE, stderr=PIPE)
	o, e = resp.communicate()
	print(o)
	print(e)

	s = o.decode("utf-8")
	time = round(time.time() * 1000)

	if not "error" in s:
	    if s[0] == "0":
	    	msg = {}
	    	stop_mode = 5
            content = get_motor_data("table", motor_list, 0)

            print(content)
            if not content:
                stop_mode = 5
            else:
                for row in json.loads(content):
                    i = json.loads(row)
                    k = ast.literal_eval(i["vfd_status"])
                    if vfd_status == 3:
                        stop_mode = 6
                        break

            msg["status"] = stop_mode
            msg["timestamp"] = time
            with open("/var/run/daq_status", "w") as hdlr:
            	hdlr.write(msg)

	    if s[1] == "0":
	    	msg = {}
	    	msg["status"] = 8
	    	msg["timestamp"] = time

	    	with open("/var/run/daq_status_edge_power", "w") as hdlr:
	    		hdlr.write(msg)
	else:
	    print("Error")

def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-mu', action='store', help='Motor UUID', nargs="+", type=str)

    return parser.parse_args()

if __name__ == "__main__":

    args = getargs()
    motor_uuid = args.mu

    motor_list = []
    motor_list.append(motors.split(' '))

    while True:
    	try:
    	    check_signal(motor_list)
    	except:
    		pass