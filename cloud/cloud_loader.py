from cassandra.auth import PlainTextAuthProvider
from cassandra.query import BatchStatement, SimpleStatement
import time
import ssl
import cassandra
from cassandra.cluster import Cluster
from cassandra.policies import *
from ssl import PROTOCOL_TLSv1_2, SSLContext, CERT_NONE
from requests.utils import DEFAULT_CA_BUNDLE_PATH

import uuid
from datetime import timezone
import datetime
from datetime import datetime as datetime2
import time
import calendar
import json

# Apache Cassandra DB connection (Edge)
# TODO: CONFIG
COSMOS_DB_INSTANCE = 'aceco-cosmos-iot-db.cassandra.cosmos.azure.com'
COSMOS_DB_PORT = 10350
COSMOS_DB_USER = 'aceco-cosmos-iot-db'
COSMOS_DB_PASSWD = 'HD5QPD0v9zvrrdlXULhDGLqyAMKAEVkt7AuXOVr0jGnmfYjeag2fPVYXXhy0zHrHTNG9zU2zT2Jtqn8Zzk4hLg=='
COSMOS_KEY_SPACE = 'cloud_core'

# Connect to database
class DatabaseConnection:
    def __init__(self):
        self.cosmos_auth_provider = None
        self.cosmos_cluster = None
        self.cosmos_session = None
        self.openSession()

    def openSession(self):

        ssl_context = SSLContext(PROTOCOL_TLSv1_2)
        ssl_context.verify_mode = CERT_NONE
        self.cosmos_auth_provider = PlainTextAuthProvider(username=COSMOS_DB_USER, password=COSMOS_DB_PASSWD)
        self.cosmos_cluster = Cluster([COSMOS_DB_INSTANCE], port=COSMOS_DB_PORT, auth_provider=self.cosmos_auth_provider, ssl_context=ssl_context)
        self.cosmos_session = self.cosmos_cluster.connect()


    def shutCluster(self):
        self.cosmos_cluster.shutdown()


def ingest_stream(crane_query_json):
    # TODO: Log

    try:

        # Create a DB connection instance
        dbSession = DatabaseConnection()

        # Check the given JSON is a list
        if (isinstance(crane_query_json, list)):
            # Loop thru the given JsON
            for motor_data in crane_query_json:
                json_motor_data = motor_data
                edge_uuid = json_motor_data["edge_uuid"]
                # edge_mac =  json_motor_data["edge_mac"]
                total_motors = json_motor_data["total_motors"]
                vfd_status = crane_query_json["vfd_status"]
                query_timestamp = json_motor_data["query_timestamp"]
                utc_query_timestamp = datetime2.strptime(query_timestamp, "%Y-%m-%d %H:%M:%S.%fZ")
                epoch_query_timestamp = (utc_query_timestamp - datetime2(1970, 1, 1)).total_seconds()
                epoch_query_timestamp = int(epoch_query_timestamp * 1000)
                #print(epoch_query_timestamp)
                motor_data = str(json_motor_data["motor_data"])
                # print( motor_data )
                # load_timestamp = datetime.datetime.now(timezone.utc)
                load_timestamp = round(time.time() * 1000)
                motor_uuid = json_motor_data["motor_uuid"]

                # single Insert Statement
                dbSession.cosmos_session.execute(
                    """
                    insert into cloud_core.crane_details (edge_uuid, total_motors, query_timestamp,  motor_uuid, motor_data,load_timestamp, vfd_status) 
                    values (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (edge_uuid, total_motors, query_timestamp, motor_uuid, motor_data, load_timestamp, vfd_status)
                )

            dbSession.shutCluster()
            return "Stream(s) Ingested"

        else:
            edge_uuid = crane_query_json["edge_uuid"]
            # edge_mac =  crane_query_json["edge_mac"]
            total_motors = crane_query_json["total_motors"]
            query_timestamp = crane_query_json["timestamp"]
            motor_data = str(crane_query_json["motor_data"])
            # load_timestamp = datetime.datetime.today()
            # load_timestamp = datetime.datetime.now(timezone.utc)
            load_timestamp = round(time.time() * 1000)
            vfd_status = crane_query_json["vfd_status"]
            motor_uuid = crane_query_json["motor_uuid"]

            # single Insert Statement
            dbSession.cosmos_session.execute(
                """
                insert into cloud_core.crane_details (edge_uuid, total_motors, query_timestamp,  motor_uuid, motor_data,load_timestamp, vfd_status) 
                values (%s,%s,%s,%s,%s,%s,%s)
                """,
                (edge_uuid, total_motors, query_timestamp, motor_uuid, motor_data, load_timestamp, vfd_status)
            )

        dbSession.shutCluster()
        return "Stream Ingested"


    except Exception as e:
        error_msg = {"Status": "Failed to ingest for Edge UUID=" + edge_uuid, "Error": str(e)}
        return error_msg

def ingest_stream_hourly(crane_query_json):
    # TODO: Log

    try:

        # Create a DB connection instance
        dbSession = DatabaseConnection()

        # Check the given JSON is a list
        if (isinstance(crane_query_json, list)):
            # Loop thru the given JsON
            for motor_data in crane_query_json:
                json_motor_data = motor_data
                edge_uuid = json_motor_data["edge_uuid"]
                # edge_mac =  json_motor_data["edge_mac"]
                total_motors = json_motor_data["total_motors"]
                vfd_status = json_motor_data["vfd_status"]
                query_timestamp = json_motor_data["query_timestamp"]
                utc_query_timestamp = datetime2.strptime(query_timestamp, "%Y-%m-%d %H:%M:%S.%fZ")
                epoch_query_timestamp = (utc_query_timestamp - datetime2(1970, 1, 1)).total_seconds()
                epoch_query_timestamp = int(epoch_query_timestamp * 1000)
                #print(epoch_query_timestamp)
                motor_data = str(json_motor_data["motor_data"])
                # print( motor_data )
                # load_timestamp = datetime.datetime.now(timezone.utc)
                load_timestamp = round(time.time() * 1000)
                motor_uuid = json_motor_data["motor_uuid"]

                # single Insert Statement
                dbSession.cosmos_session.execute(
                    """
                    insert into cloud_core.crane_details_hourly (edge_uuid, total_motors, query_timestamp,  motor_uuid, motor_data,load_timestamp, vfd_status) 
                    values (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (edge_uuid, total_motors, query_timestamp, motor_uuid, motor_data, load_timestamp, vfd_status)
                )

            dbSession.shutCluster()
            return "Stream(s) Ingested"

        else:
            edge_uuid = crane_query_json["edge_uuid"]
            # edge_mac =  crane_query_json["edge_mac"]
            total_motors = crane_query_json["total_motors"]
            query_timestamp = crane_query_json["timestamp"]
            motor_data = str(crane_query_json["motor_data"])
            # load_timestamp = datetime.datetime.today()
            # load_timestamp = datetime.datetime.now(timezone.utc)
            load_timestamp = round(time.time() * 1000)
            vfd_status = crane_query_json["vfd_status"]
            motor_uuid = crane_query_json["motor_uuid"]

            # single Insert Statement
            dbSession.cosmos_session.execute(
                """
                insert into cloud_core.crane_details_hourly (edge_uuid, total_motors, query_timestamp,  motor_uuid, motor_data,load_timestamp, vfd_status) 
                values (%s,%s,%s,%s,%s,%s,%s)
                """,
                (edge_uuid, total_motors, query_timestamp, motor_uuid, motor_data, load_timestamp, vfd_status)
            )

        dbSession.shutCluster()
        return "Stream Ingested"


    except Exception as e:
        error_msg = {"Status": "Failed to ingest for Edge UUID=" + edge_uuid, "Error": str(e)}
        return error_msg


def get_config_data(edge_mac, version):
    # TODO: Log
    # TODO: CONFIG

    try:

        # Create a DB connection instance
        dbSession = DatabaseConnection()

        if edge_mac is None:
            edge_mac = '00:0a:bb:11:22:22'

        if version is None:
            version = 0

        # TO DO: Fix select  for multiple version with False
        config_rows = []
        config_query = "select json edge_uuid ,edge_mac ,version,config_sync_flag,config_data ,created_by,created_on from cloud_core.crane_config where  edge_mac = '" + edge_mac + "' "

        for config_row in dbSession.cosmos_session.execute(config_query):
            #config_rows.append(config_row[0].replace("'", '"'))
            config_rows.append(config_row[0])


            # where version > " + version + " order by version DESC LIMIT 1"

        dbSession.shutCluster()
        return json.dumps(config_rows)

    except Exception as e:
        error_msg = {"Status": "Failed to pull data for Edge MAC=" + edge_mac, "Error": str(e)}
        return error_msg


def update_config_data(edge_mac, version):
    # TODO: Log

    try:

        # Create a DB connection instance
        dbSession = DatabaseConnection()

        # single update Statement
        update_query = "update cloud_core.crane_config set config_sync_flag=True where edge_mac='" + edge_mac + "' and version= " + str(version)
        dbSession.cosmos_session.execute(update_query )

        dbSession.shutCluster()
        return "Flag Updated as True at Cloud Config"


    except Exception as e:
        error_msg = {"Status": "Failed to ingest for Edge MAC=" + edge_mac, "Error": str(e)}
        return error_msg
