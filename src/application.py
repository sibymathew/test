"""
xcloud API services

Copyright (C) 2014-2015 Ruckus Wireless, Inc.
 All Rights Reserved.

Provides a minimal system for managing AP's via AWS DynamoDB.
xxxxx
Manage xcloud tenants, tenant aws credentials, claims on AP's by tenants, and AP AWS credentials

"""

import boto.sts as sts
import boto.dynamodb2 as ddb
from boto.dynamodb2.fields import HashKey, RangeKey, KeysOnlyIndex, AllIndex
from boto.dynamodb2.exceptions import ItemNotFound
from boto.dynamodb2.table import Table
import stormpath
from stormpath.client import Client
from flask import Flask, request, Response, jsonify
import sys, time, traceback, os
from os.path import expanduser
import json
import logging
import string
import random
from  logging.handlers import SysLogHandler


app = Flask(__name__)


'''def config_logging():
    if sys.platform == "darwin":
        address = "/var/run/syslog"
    else:
        address = '/dev/log'
    syslog_handler = SysLogHandler(address)
    syslog_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)s: %(message)s')
    syslog_handler.setFormatter(formatter)
    app.logger.name = "xcloud"
    app.logger.addHandler(syslog_handler)
    app.logger.setLevel(logging.DEBUG)

config_logging()'''


# load stormpath credentials
try:
    if 'STORMPATH_ID' in os.environ:
        key_id = os.environ['STORMPATH_ID']
        secret = os.environ['STORMPATH_SECRET']
        client = Client(id=key_id, secret=secret)
    else:
        client = Client(api_key_file_location=expanduser('~/.stormpath/apiKey.properties'))
except:
    app.logger.error("unable to create stormpath client. Missing API keys?")
    raise

# get stormpath Xcloud application context
application = client.applications.search('xcloud')[0]



# load pubnub credentials
try:
    if 'PUBNUB_SUBSCRIBE' in os.environ:
        pubnub_publish_key   = os.environ['PUBNUB_SUBSCRIBE']
        pubnub_subscribe_key = os.environ['PUBNUB_PUBLISH']
    else:
        api_key_file_location=expanduser('~/.pubnub/pubnub.properties')
        pubnub = dict([x.strip() for x in line.split('=')] for line in open(api_key_file_location))
        pubnub_publish_key   = pubnub['publish_key']
        pubnub_subscribe_key = pubnub['subscribe_key']
except:
    app.logger.error("unable to create stormpath client. Missing API keys?")
    raise



supported_aws_regions =  [ u'us-east-1', u'ap-northeast-1', u'eu-west-1', u'ap-southeast-1', u'ap-southeast-2', u'us-west-2', u'us-west-1', u'eu-central-1', u'sa-east-1']




# specify the AP IAM policy that will be used for the tempory IAM tokens for the AP's
ap_policy_template =  """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
          "dynamodb:GetItem"
      ],
      "Resource": [
           "arn:aws:dynamodb:$region:929087638556:table/XcloudConfig",
           "arn:aws:dynamodb:$region:929087638556:table/TenantConfig",
           "arn:aws:dynamodb:$region:929087638556:table/AccessPointConfig",
           "arn:aws:dynamodb:$region:929087638556:table/WlanConfig"
      ],
      "Condition": {
          "ForAllValues:StringEquals": {
              "dynamodb:LeadingKeys": "$xtenant"
          }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:BatchGetItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:DescribeTable"
      ],
      "Resource": [
           "arn:aws:dynamodb:$region:929087638556:table/AccessPointStatus",
           "arn:aws:dynamodb:$region:929087638556:table/WlanStatus",
           "arn:aws:dynamodb:$region:929087638556:table/StationStatus"
      ],
      "Condition": {
          "ForAllValues:StringEquals": {
              "dynamodb:LeadingKeys": "$xtenant"
          }
      }
    }
  ]
}
"""


@app.route("/1/ap/credentials", methods=['GET'])
def ap_credentials():
    """lookup an AP based on serial number and return The AP's access credentials and key state if it has been registered

    input args:  ap_serial
    returned json:

    "access_key_id":      AWS IAM Access Key
    "secret_access_key":  AWS IAM Secret Accces 
    "session_token":      AWS IAM Session Token
    "aws_region":         AWS region to use for aws connections
    "xtenant":            xcloud xtenant ID to use as key for all database operations

    Note this code only supports a single default_aws_region at this time and will need to be extended to find AP's across dynamo table in different regions.
"""
    # XXX need to verify server certificate in order to trust the serial number
    t0 = time.time()

    ap_serial = int(request.args.get('ap_serial'))
    if not ap_serial:
        app.logger.warn("ap_credentials: missing ap_serial")
        return Response("missing ap_serial", 400)

    # check the claim cache for this AP serial number
    ap_claim_cache = Table('AccessPointClaimCache', connection=ddb.connect_to_region('us-east-1'))

    try:
        claim = ap_claim_cache.get_item(ap_serial=ap_serial)
    except ItemNotFound:
        app.logger.debug("ap_credentials: AP %s not found", ap_serial)
        return Response("{}", 200)

    xtenant = claim['xtenant']
    region  = claim['region']

    # verify the AP hasn't been deleted 
    ap_config = Table('AccessPointConfig', connection=ddb.connect_to_region(region))

    try:
        ap_config.get_item(xtenant=xtenant, ap_serial=ap_serial)
    except ItemNotFound:
        app.logger.info("ap_credentials: AP Serial %d Not Found xtenant %s region %s" % (ap_serial, xtenant, region))
        return Response("{}", 200)

    app.logger.info("ap_credentials: Found xtenant %s region %s for ap_serial %d" % (xtenant, region, ap_serial))

    # get IAM temporary credentials for AP with appropriate policy
    stsc = sts.connect_to_region(region)
    # customize the ap_policy based on the region and xtenant ID    
    policy = string.Template(ap_policy_template).substitute(region=region, xtenant=xtenant)
    tokens = stsc.get_federation_token(name=xtenant, policy=policy, duration=129600)

    # send the credentials directly back in the response
    response = tokens.credentials.to_dict()

    # add aws_region and xtenant id to the reponse
    response['aws_region'] = region
    response['xtenant']    = xtenant

    # add pubnub credentials
    response['pubnub_subscribe_key'] = pubnub_subscribe_key
    response['pubnub_publish_key']   = pubnub_publish_key

    dt = time.time() - t0
    app.logger.info("ap_credentials: ap_serial %d xtenant %s dt %.3f" % (ap_serial, xtenant, dt))

    return jsonify(response)





@app.route("/1/ap/claim", methods=['POST'])
def ap_claim():
    """

   Claim an AP for management by a specific user.

   Request Body must include the following json attributes:

    "username":  previously registered username
    "password":  associated password
    "ap_serial": serial number of AP as found on AP barcode

"""
    t0 = time.time()

    req = json.loads(request.data)
    try:
        username  = req["username"]
        password  = req["password"]
    except:
        app.logger.info("ap_claim: missing required username/password")
        return Response("missing required username or password attributes", 400)

    try:
        ap_serial = req['ap_serial']
    except:
        app.logger.info("ap_claim: %s missing ap_serial" % username)
        return Response("missing required ap_serial", 400)

    # authenticate user
    try:
         account = application.authenticate_account(username, password).account
    except stormpath.error.Error as err:
        app.logger.info("ap_claim: %s authentication failed" % username)
        return Response(err.message, err.status)

    # get xtenant's AWS region from account custom_data
    region = account.custom_data['aws_region']

    # get xtenant id
    xtenant = account.custom_data['xtenant']

    # verify AP has not been claimed by some other xtenant
    # The AccessPointClaimCache caches the xtenant and region of the last claim operation
    ap_claim_cache = Table('AccessPointClaimCache', connection=ddb.connect_to_region('us-east-1'))

    try:
        previous_claim = ap_claim_cache.get_item(ap_serial=ap_serial)
    except ItemNotFound:
        previous_claim = None

    if previous_claim:
        # found this serial number in the claim cache
        # see if it really still is registered (since it could have been deleted to give to someone else
        prev_xtenant = previous_claim['xtenant']
        prev_region  = previous_claim['region']
        prev_ap_config = Table('AccessPointConfig', connection=ddb.connect_to_region(prev_region))

        try:
            prev_ap = prev_ap_config.get_item(xtenant=prev_xtenant, ap_serial=ap_serial)
        except ItemNotFound:
            prev_ap = None   # the AP was deleted, the cache is out of date
        if prev_ap:
            if prev_xtenant != xtenant:
                app.logger.warning("ap_claim: username %s ap_serial %s claimed by another xtenant %s region %s" % (username, ap_serial, prev_xtenant, prev_region))
                return Response("AP previously claimed by someone else.", 400)
            else:
                # AP has already been claimed by this same xtenant so nothing more to do here.
                app.logger.info("ap_claim: username %s ap_serial %s already claimed by this customer" % (username, ap_serial))
                return Response("OK", 200)
    # No claim to this AP

    ddbc = ddb.connect_to_region(region)  # xtenant's region
    ap_config = Table('AccessPointConfig', connection=ddbc)

    # create user,serial entry in AccessPointConfig table
    ap_config.put_item(data={'xtenant':xtenant, 'ap_serial':ap_serial})

    # record this claim in the claim cache
    ap_claim_cache.put_item(data={'ap_serial':ap_serial, 'xtenant':xtenant, 'region':region})

    app.logger.info("ap_claim: username %s xtenant %s ap_serial %s" % (username, xtenant, ap_serial))
    return Response("OK", 200)
    


@app.route('/1/aws_regions', methods=['GET'])
def get_regions():
    """return a json list of the regions we currently support"""
    return json.dumps(supported_aws_regions)




def create_tenant_resources(aws_region, xtenant):
    """create all static AWS resources associated with a new tenant"""
    ddbc = ddb.connect_to_region(aws_region)  # xtenant's region

    # Create per-tenant xtenant configuration data
    xcloud_data = {'xtenant':xtenant, 'creation_time':time.time()}
    # add some additional random element to the channels for this xtenant
    rand = "".join([random.sample(string.digits+string.ascii_letters,1)[0] for i in range(8)])
    xcloud_data['pubnub_all_ap_channel']       = xtenant + "__" + rand + "_aps"
    xcloud_data['pubnub_all_managers_channel'] = xtenant + "__" + rand + "_mgrs"

    # create XcloudConfig Table entry for this xtenant
    xcloud_config = Table('XcloudConfig', connection=ddbc)
    xcloud_config.put_item(data=xcloud_data)
    
    # create TenantConfig Table entry for this xtenant
    tenant_config = Table('TenantConfig', connection=ddbc)
    tenant_config.put_item(data={'xtenant':xtenant})

    


@app.route("/1/account",  methods=['POST'])
def user_create():
    """
    Body must include the following json attributes:

        "given_name": "Joe",  
        "surname": "Stormtrooper",
        "username": "tk421",
        "email": "tk421@stormpath.com",
        "password":"Changeme1"
         "aws_region" : valid AWS region requested for this user (not guaranteed to be assigned)
    """

    t0 = time.time()

    # check for an copy the required user information fields in the POST data
    user = {}
    req_user = json.loads(request.data)
    try:
        user["given_name"] = req_user["given_name"]
        user["surname"]   = req_user["surname"]
        user["username"]  = req_user["username"]
        user["email"]     = req_user["email"]
        user["password"]  = req_user["password"]
        aws_region        = req_user["aws_region"]
    except:
        app.logger.info('user_create: missing required attributes')
        return Response("missing required user attributes", 400)
    
    # Assign an aws region to the user based on their requested region.
    # Use a default region if the requested region is not specified or unavailable.
    if aws_region not in supported_aws_regions:
        app.logger.info("invalid/unsupported aws_region: %s" % aws_region)
        return Response("invalid or unsupported aws_region", 400)

    user['custom_data'] = {'aws_region':aws_region}

    # create a unique xtenant ID based on the username and a random string
    xtenant = user['username'] +"_"+ "".join([random.sample(string.digits+string.ascii_letters,1)[0] for i in range(8)])

    user['custom_data']['xtenant'] = xtenant

    app.logger.info("create user %s email %s xtenant %s" % (user["username"] , user["email"], xtenant))

    try:
        account = application.accounts.create(user)
    except stormpath.error.Error as err:
        app.logger.info(err.message)
        return Response(err.message, err.status)

    # create AWS resources for this xtenant:
    create_tenant_resources(aws_region, xtenant)

    dt = time.time() - t0
    app.logger.info('create_user: dt %.3f' % dt)
    return Response("OK", 200)
  



@app.route("/1/user/verify", methods=['POST'])
def verify_user():
    """ 
    A non-public interface for test automation purposes.  Verify the username/password without returning any AWS credentials.

    Request Body must include the following json attributes:

    "username":  previously registered username
    "password":  associated password
"""
    t0 = time.time()

    req_user = json.loads(request.data)
    try:
        username  = req_user["username"]
        password  = req_user["password"]
    except:
        return Response("missing required username or password attributes", 400)

    # authenticate via stormpath
    try:
         account = application.authenticate_account(username, password).account
    except stormpath.error.Error as err:
        app.logger.info(err.message)
        return Response(err.message, err.status)

    return Response("OK")




# specify the AP Manager IAM policy that will be used for the tempory IAM tokens for customer management applications.
ap_manager_policy_template = """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:BatchGetItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:DescribeTable"
      ],
      "Resource": [
           "arn:aws:dynamodb:$region:929087638556:table/TenantConfig",
           "arn:aws:dynamodb:$region:929087638556:table/AccessPointConfig",
           "arn:aws:dynamodb:$region:929087638556:table/WlanConfig"
      ],
      "Condition": {
          "ForAllValues:StringEquals": {
              "dynamodb:LeadingKeys": "$xtenant"
          }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
          "dynamodb:GetItem"
      ],
      "Resource": [
           "arn:aws:dynamodb:$region:929087638556:table/XcloudConfig",
           "arn:aws:dynamodb:$region:929087638556:table/AccessPointStatus",
           "arn:aws:dynamodb:$region:929087638556:table/WlanStatus",
           "arn:aws:dynamodb:$region:929087638556:table/StationStatus"
      ],
      "Condition": {
          "ForAllValues:StringEquals": {
              "dynamodb:LeadingKeys": "$xtenant"
          }
      }
    }
  ]
}
"""



@app.route("/1/user/credentials", methods=['POST'])
def ap_manager_credentials():
    """
    Get tempory AWS access credentials for the purpose of managing AP's from an application.

    Request Body must include the following json attributes:

`    "username":  previously registered username
    "password":  associated password
   
    returns JSON:

    "access_key"    - the AccessKeyID
    "secret_key"    - The SecretAccessKey
    "session_token" - The session token that must be passed with requests to use the temporary credentials
    "aws_region"    - The AWS region to use for all AWS operations
    "xtenant"       - The xtenant id to use as the HashKey key for all DynamoDB operations
"""
    t0 = time.time() 
    req_user = json.loads(request.data)
    try:
        username  = req_user["username"]
        password  = req_user["password"]
    except:
        app.logger.info("ap_manager_credentials: missing username/passwd")
        return Response("missing required username or password attributes", 400)

    # authenticate via stormpath
    try:
         account = application.authenticate_account(username, password).account
    except stormpath.error.Error as err:
        app.logger.info("ap_manager_credentials: authentication failure username %s", username)
        return Response(err.message, err.status)

    # get AWS region and xtenant from account custom_data
    region  = account.custom_data['aws_region']
    xtenant = account.custom_data['xtenant']
    
    # get AWS IAM temporary credentials for this user with appropriate policy
    stsc = sts.connect_to_region(region)
    # customize the ap_manager_policy based on the region and xtenant ID    
    policy = string.Template(ap_manager_policy_template).substitute(region=region, xtenant=xtenant)
    tokens = stsc.get_federation_token(name=account.username, policy=policy, duration=129600)

    # send the credentials directly back in the response
    response = tokens.credentials.to_dict()

    # add aws_region and xtenant id to the reponse
    response['aws_region'] = region
    response['xtenant'] = xtenant

    # add pubnub credentials
    response['pubnub_subscribe_key'] = pubnub_subscribe_key
    response['pubnub_publish_key']   = pubnub_publish_key

    dt = time.time() - t0
    app.logger.info("ap_manager_credentials: %s dt %.3f" % (username, dt))

    return jsonify(response)

    



@app.route("/1/ping", methods=['GET'])
def ping():
    """test server"""
    app.logger.debug("ping")
    return "Alive at time %s\n" % time.time()
    
if __name__ == "__main__":
    app.run(host='0.0.0.0')
    app.run(debug=True)
