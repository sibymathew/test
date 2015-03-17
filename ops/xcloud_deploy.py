"""

Python Deploy Framework
=======================

This framework is used to deploy the code in CI/CD fashion

Contact: Siby Mathew siby.mathew@ruckuswireless.com
Copyright (C) 2014 Ruckus Wireless, Inc.
All Rights Reserved.

"""

import os
import sys
import getopt
import json
import time
import string
import boto

def get_env():
	
	try:
		region=os.environ['AWS_REGION']
		id=os.environ['AWS_ACCESS_KEY_ID']
		key=os.environ['AWS_SECRET_ACCESS_KEY']
		r53_id=os.environ['R53_AWS_ACCESS_KEY_ID']
		r53_key=os.environ['R53_AWS_SECRET_ACCESS_KEY']
		pubnub_pub=os.environ['PUBNUB_PUBLISH']
		pubnub_sub=os.environ['PUBNUB_SUBSCRIBE']
		stormpath_id=os.environ['STORMPATH_ID']
		stormpath_secret=os.environ['STORMPATH_SECRET']
		docker_branch=os.environ['DOCKER_BRANCH']
	except:
		print ("AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, R53_AWS_ACCESS_KEY_ID, R53_AWS_SECRET_KEY_ID, PUBNUB_PUBLISH, PUBNUB_SUBSCRIBE, STORMPATH_ID, STORMPATH_SECRET should be set as an environment variable")
	else:
		return region, id, key, r53_id, r53_key, pubnub_pub, pubnub_sub, stormpath_id, stormpath_secret, docker_branch
	sys.exit(2)

def create_content_zip(bucket):

	#Create Dockerrun.aws.json
	content = '{"AWSEBDockerrunVersion": "1","Authentication": {"Bucket": "' + bucket + '","Key": "docker/dockercfg"},"Image": {"Name": "' + 'sibymath/circletest:v4' + '","Update": "true"},"Ports": [{"ContainerPort": "5000"}],"Logging": "/var/log"}'
	with open("ops/Dockerrun.aws.json", "w") as file_write:
		file_write.write(content)
	file_write.close()

	#Create content.zip Dockerun.aws.json and .ebextensions/*
	cmd = "cd ops " + "&&" + " zip content.zip Dockerrun.aws.json .ebextensions/*"
	os.system(cmd)

def create_iam_role(id, key, region, role):

	role_policy_template = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "dynamodb:*",
                "cloudwatch:DeleteAlarms",
                "cloudwatch:DescribeAlarmHistory",
                "cloudwatch:DescribeAlarms",
                "cloudwatch:DescribeAlarmsForMetric",
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:ListMetrics",
                "cloudwatch:PutMetricAlarm",
                "datapipeline:ActivatePipeline",
                "datapipeline:CreatePipeline",
                "datapipeline:DeletePipeline",
                "datapipeline:DescribeObjects",
                "datapipeline:DescribePipelines",
                "datapipeline:GetPipelineDefinition",
                "datapipeline:ListPipelines",
                "datapipeline:PutPipelineDefinition",
                "datapipeline:QueryObjects",
                "iam:ListRoles",
                "sns:CreateTopic",
                "sns:DeleteTopic",
                "sns:ListSubscriptions",
                "sns:ListSubscriptionsByTopic",
                "sns:ListTopics",
                "sns:Subscribe",
                "sns:Unsubscribe",
                "elasticbeanstalk:*",
                "ec2:*",
                "elasticloadbalancing:*",
                "autoscaling:*",
                "cloudwatch:*",
                "s3:*",
                "sns:*",
                "cloudformation:*",
                "rds:*",
                "sqs:*",
                "iam:PassRole"
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
}"""

	role_policy = role + "_policy"

	print "Creating IAM Role"
	try:
		iam_conn = boto.connect_iam()
		iam_conn.create_instance_profile(role, path='/')
		iam_conn.create_role(role, path='/')
		iam_conn.add_role_to_instance_profile(role, role)
		iam_conn.put_role_policy(role, role_policy, role_policy_template)
	except boto.exception.BotoServerError, err:
		if err.code == "EntityAlreadyExists":
			print "IAM role %s already exists. "%(role_policy)
	finally:
		return role

def apply_security_groups(id, key, region, ec2_sg_name):

	from boto.regioninfo import RegionInfo
	from boto import ec2

	ec2_region = ec2.get_region(aws_access_key_id=id, aws_secret_access_key=key, region_name=region)
	ec2_conn = boto.ec2.connection.EC2Connection(aws_access_key_id=id, aws_secret_access_key=key, region=ec2_region)

	print "Creating ELB Security Group"
	try:
		elb_sg_name = "xcloud-elb-sg"
		ec2_conn.create_security_group(elb_sg_name, elb_sg_name)
		ec2_conn.authorize_security_group(elb_sg_name, ip_protocol='tcp', from_port='443', to_port='443', cidr_ip='0.0.0.0/0')
		ec2_conn.authorize_security_group(elb_sg_name, ip_protocol='tcp', from_port='80', to_port='80', cidr_ip='0.0.0.0/0')
	except boto.exception.EC2ResponseError, err:
		if err.code == "InvalidGroup.Duplicate":
			print err.message + "........  Using it."

	resp = ec2_conn.get_all_security_groups()
	for res in resp:
		if res.name == "xcloud-elb-sg":
			elb_sg_id = res.id

	ec2_conn.authorize_security_group(ec2_sg_name, ip_protocol='tcp', from_port='443', to_port='443', src_security_group_group_id=elb_sg_id)
	ec2_conn.revoke_security_group(ec2_sg_name, ip_protocol='tcp', from_port='80', to_port='80', src_security_group_group_id='sg-83176ae6')
	ec2_conn.authorize_security_group(ec2_sg_name, ip_protocol='tcp', from_port='80', to_port='80', src_security_group_group_id=elb_sg_id)
	#ec2_conn.revoke_security_group('awseb-e-9rbuj5r6ug-stack-AWSEBSecurityGroup-1ICIXVN1UKVG', ip_protocol='tcp', from_port='8443', to_port='8443', cidr_ip='0.0.0.0/0')
	return elb_sg_id

def apply_listener(id, key, region, elb_name, elb_sg_id):

	from boto.ec2 import elb

	endpoint = "elasticloadbalancing." + region + ".amazonaws.com"
	region_info = boto.regioninfo.RegionInfo(None, region, endpoint)

	elb_conn = boto.ec2.elb.ELBConnection(aws_access_key_id=id, aws_secret_access_key=key, region=region_info)

	elb_conn.create_load_balancer_listeners(elb_name, [(['443', '443', 'tcp'])])
	elb_conn.apply_security_groups_to_lb(elb_name, elb_sg_id)

def apply_route53(id, key, new_url, domainname):

	from boto import route53
	from boto.route53.record import ResourceRecordSets
	import re

	r53_conn = boto.route53.connection.Route53Connection(aws_access_key_id=id, aws_secret_access_key=key)
	resp = r53_conn.get_all_hosted_zones()
	resp = resp['ListHostedZonesResponse']['HostedZones']
	for res in resp:
		if res['Name'] == domainname:
			match = re.match(r'/hostedzone/(.*)', res['Id'])
			if match:
				zone_id = match.groups()[0]

	internet_facing_url = "api." + domainname
	print new_url
	print domainname
	print internet_facing_url
	try:
		resp = r53_conn.get_zone(domainname)
		for res in resp.get_records():
			if res.type == "CNAME":
				old_url = res.resource_records[0]
		if not old_url:
			raise
	except:
		print "New mapping is been created"
	else:
		print "Deleting the old url: %s andcreating a new one"%(old_url)
		conn = boto.connect_route53(aws_access_key_id=id, aws_secret_access_key=key)
		changes = ResourceRecordSets(conn, zone_id)
		change = changes.add_change("DELETE", internet_facing_url ,"CNAME")
		change.add_value(old_url)
		changes.commit()
	finally:
		conn = boto.connect_route53(aws_access_key_id=id, aws_secret_access_key=key)
		changes = ResourceRecordSets(conn, zone_id)
		change = changes.add_change("CREATE", internet_facing_url ,"CNAME")
		change.add_value(new_url)
		changes.commit()


def push_to_s3(id, key, region, bucket):

	from boto.s3.connection import S3Connection
	from boto.s3.connection import Location
	from boto.s3.key import Key
	from boto.s3 import connect_to_region

	if region == 'us-east-1':
		loc = Location.DEFAULT
	elif region == 'us-west-1':
		loc = Location.USWest
	elif region == 'us-west-2':
		loc = Location.USWest2

	if not os.path.isfile("ops/dockercfg") or not os.path.isfile("ops/content.zip"):
		print ("dockercfg and content.zip should be present in the folder where this script is executed")
	else:
		s3_conn = boto.connect_s3(aws_access_key_id = id, aws_secret_access_key = key)

		try:
			s3_conn.get_bucket(bucket)
		except:
			s3_conn.create_bucket(bucket, location=loc)
		else:
			full_bucket = s3_conn.get_bucket(bucket)
			for key in full_bucket.list():
				key.delete()
			s3_conn.delete_bucket(bucket)
			s3_conn.create_bucket(bucket, location=loc)
		finally:
			cmd = "aws s3 cp ops/content.zip s3://%s/content.zip"%(bucket)
			os.system(cmd)
			cmd = "aws s3 cp ops/dockercfg s3://%s/docker/dockercfg"%(bucket)
			os.system(cmd)

def deploy_app(id, key, region, r53_id, r53_key, pb_pub, pb_sub, sp_id, sp_secret, role, app, env, ver, bucket, mode):

	from boto.beanstalk.layer1 import Layer1
	import boto.beanstalk.response

	endpoint = "elasticbeanstalk." + region + ".amazonaws.com"
	region_info = boto.regioninfo.RegionInfo(None, region, endpoint)
	ebs_conn = boto.connect_beanstalk(aws_access_key_id = id, aws_secret_access_key = key, region=region_info)

	try:
		print "Creating ElasticBeanStalk Application %s Version %s"%(app,ver)
		ebs_conn.create_application_version(app, ver, s3_bucket=bucket, s3_key='content.zip', auto_create_application='true')
	except boto.exception.BotoServerError, err:
		err.match = "Application Version " + ver + " already exists."
		if err.message == err.match:
			print "Application Version %s already exists for Application %s"%(ver, app)
	else:
		lc = 'aws:autoscaling:launchconfiguration'
		elb = 'aws:elb:loadbalancer'
		denv = 'aws:elasticbeanstalk:application:environment'

		namespace = [lc,lc,lc,denv,denv,denv,denv,denv,denv]
		optionname = ['EC2keyName','IamInstanceProfile','InstanceType','STORMPATH_ID','STORMPATH_SECRET','PUBNUB_PUBLISH','PUBNUB_SUBSCRIBE','AWS_ACCESS_KEY_ID','AWS_SECRET_ACCESS_KEY']
		value = ['siby-aws-ssh',role,'t1.micro',sp_id,sp_secret,pb_pub,pb_sub,id,key]
		options = zip(namespace, optionname, value)

		try:
			print "Creating EC2 Environment %s"%(env)
			ebs_conn.create_environment(app, env, version_label=ver, solution_stack_name='64bit Amazon Linux 2014.09 v1.0.11 running Docker 1.3.3', cname_prefix=env, option_settings=options)
		except:
			print "Environment %s already exists"%(env)
		else:
			print "Sleeping for few minutes... zzzz..zzzzz."
			#resp = ebs_conn.describe_environments(environment_names=env)
			#env_status = resp['DescribeEnvironmentsResponse']['DescribeEnvironmentsResult']['Environments'][0]['Status']
			#r53_url =  resp['DescribeEnvironmentsResponse']['DescribeEnvironmentsResult']['Environments'][0]['EndpointURL']

			time.sleep(120)
			print "Deploying the application"
			resp = ebs_conn.describe_environment_resources(environment_name=env)
			resp = resp['DescribeEnvironmentResourcesResponse']['DescribeEnvironmentResourcesResult']['EnvironmentResources']['Resources']
			for res in resp:
				if res['LogicalResourceId'] == 'AWSEBSecurityGroup':
					env_sg_name = res['PhysicalResourceId']
				elif res['LogicalResourceId'] == 'AWSEBLoadBalancer':
					elb_name = res['PhysicalResourceId']

			elb_sg_id = apply_security_groups(id, key, region, env_sg_name)
			apply_listener(id, key, region, elb_name, elb_sg_id)

			r53_url = env + ".elasticbeanstalk.com"
			if mode == "stage":
				domain = "xcloud-stage.net."
			elif mode == "production":
				domain = "xcloud-ops.net."
		
			apply_route53(r53_id, r53_key, r53_url, domain)

			resp = ebs_conn.describe_environments(environment_names=env)
			env_status = resp['DescribeEnvironmentsResponse']['DescribeEnvironmentsResult']['Environments'][0]['Status']
			print "Environment Status : %s"%(env_status)
			#time.sleep(400)
			#ebs_conn.update_environment(environment_name=env, version_lab

def main():

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'h:d:v:a:e:b:m:', ['help', 'debug', 'version=', 'appname=', 'envname=', 's3bucket=', 'mode='])
	except getopt.GetoptError:
		usage()
		sys.exit(2)

	for opt, arg in opts:
		if opt in ('-h', '--help'):
			usage()
			sys.exit(2)
		elif opt in ('-v', '--version'):
			version=arg
		elif opt in ('-a', '--appname'):
			appname=arg
		elif opt in ('-e', '--envname'):
			envname=arg
		elif opt in ('-b', '--bucket'):
			s3bucket=arg
		elif opt in ('-m', '--mode'):
			mode=arg
		else:
			usage()
			sys.exit(2)

	aws_region, aws_id, aws_key, r53_id, r53_key, pb_pub, pb_sub, sp_id, sp_secret, dock_branch = get_env()
	bucket = "xcloud" + aws_id.lower() + s3bucket + aws_region
	role = "xcloud_" + aws_id.lower() + "_" + s3bucket

	iam_role_name = create_iam_role(aws_id, aws_key, aws_region, role)
	create_content_zip(bucket)
	push_to_s3(aws_id, aws_key, aws_region, bucket)
	#iam_role_name = "xcloud_akiajxuxr6rsnwu3v6ea_bucket400"
	deploy_app(aws_id, aws_key, aws_region, r53_id, r53_key, pb_pub, pb_sub, sp_id, sp_secret, iam_role_name, appname, envname, version, bucket, mode)
	#apply_route53('AKIAJ572DMEWB3MRNHZQ', 'iOZGQmlqZlkVK3A4vCsTAHfFC/v9FXUhB4C4Xb1X', 'xcloud-tadasest.elasticbeanstalk.com', 'xcloud-ops.net.')

def usage():
	print ("Error")


if __name__ == "__main__":
    main()
