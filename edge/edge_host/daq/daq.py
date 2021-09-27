from subprocess import Popen, PIPE

def check_signal(motor_list):
	print("here")
	resp = Popen(["./StaticDI"], stdout=PIPE, stderr=PIPE)
	o, e = resp.communicate()
	print(o)
	print(e)

	s = o.decode("utf-8")
	print(type(s))
	print(s)

	if not "error" in s:
	    print(s[0])
	    print(s[1])
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