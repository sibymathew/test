def get_env():

	try:
		aws_id=os.environ['AWS_ACCESS_KEY_ID']
		aws_key=os.environ['AWS_SECRET_ACCESS_KEY']
		pn_pub=os.environ['PUBNUB_PUBLISH']
		pn_sub=os.environ['PUBNUB_SUBSCRIBE']
		sp_id=os.environ['STORMPATH_ID']
		sp_key=os.environ['STORMPATH_SECRET']
	except:
		print ("AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, PUBNUB_PUBLISH, PUBNUB_SUBSCRIBE, STORMPATH_ID, STORMPATH_SECRET_should be set as an environment variable")
		sys.exit(2)
	else:
		return aws_id, aws_key, pn_pub, pn_sub, sp_id, sp_key

def get_config():

	print "Get config from file"

def create_user(stp_id, stp_key):

	import stormpath

	given_name = "Test100"
	surname = "100Test"
	username = "tester100"
	email = "tester12983562@mailinator.com"
	password = "tester100"
	aws_region = "us-west-2"
	
	
def main():

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'h:m:c:f:e:b:', ['help', 'mode=', 'count=', 'file='])
	except getopt.GetoptError:
		usage()
		sys.exit(2)

	for opt, arg in opts:
		if opt in ('-h', '--help'):
			usage()
			sys.exit(2)
		elif opt in ('-m', '--mode'):
			version=arg
		elif opt in ('-c', '--count'):
			appname=arg
		elif opt in ('-f', '--file'):
			envname=arg
		else:
			usage()
			sys.exit(2)
	
	aws_id, aws_key, pub_id, pub_key, stp_id, stp_key = get_env()
	get_config()
	create_user(stp_id, stp_key)

def usage():
        print ("Error")


if __name__ == "__main__":
    main()

