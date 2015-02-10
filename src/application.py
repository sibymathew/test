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

application= Flask(__name__)
app = application

@app.route("/1/ping/srv", methods=['GET'])
def ping():
    """test server"""
    app.logger.debug("ping from DINESH")
    return "SRV Alive at time %s\n" % time.time()

@app.route("/1/ping/cli", methods=['GET'])
def ping():
    """test server"""
    app.logger.debug("ping from DINESH")
    return "CLI Alive at time %s\n" % time.time()

if __name__ == "__main__":
    app.run(host='0.0.0.0')

