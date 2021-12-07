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
                vfd_status = json_motor_data["vfd_status"]
                query_timestamp = json_motor_data["query_timestamp"]
                utc_query_timestamp = datetime2.strptime(query_timestamp, "%Y-%m-%d %H:%M:%S.%fZ")
                epoch_query_timestamp = (utc_query_timestamp - datetime2(1970, 1, 1)).total_seconds()
                epoch_query_timestamp = int(epoch_query_timestamp * 1000)
                # print(epoch_query_timestamp)
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
        config_query = "select json edge_uuid ,edge_mac ,version,config_sync_flag,config_data ,created_by,created_on from cloud_core.crane_config where  edge_mac = '" + edge_mac + "' and version > " + str(version) + " order by version desc LIMIT 1 ALLOW FILTERING"

        for config_row in dbSession.cosmos_session.execute(config_query):
            #config_rows.append(config_row[0].replace("'", '"'))
            config_rows.append(config_row[0])


            # where version > " + version + " order by version DESC LIMIT 1"

        dbSession.shutCluster()
        return json.dumps(config_rows)

    except Exception as e:
        error_msg = {"Status": "Failed to pull data for Edge MAC=" + edge_mac, "Error": str(e)}
        return error_msg


def update_config_data(edge_mac, version, sync_flag):
    # TODO: Log

    try:

        # Create a DB connection instance
        dbSession = DatabaseConnection()


        if edge_mac is None:
            edge_mac = '00:0a:bb:11:22:22'

        # if version is None:
        #    version = 1

        # if sync_flag is None:
        #    sync_flag = True

        # single update Statement
        update_query = "update cloud_core.crane_config set config_sync_flag = " + str(sync_flag) + "  where edge_mac='" + edge_mac + "' and version = " + str(version)
        dbSession.cosmos_session.execute(update_query )

        dbSession.shutCluster()
        return "Flag Updated as " + str(sync_flag) + "  at Cloud Config"


    except Exception as e:
        error_msg = {"Status": "Failed to ingest for Edge MAC=" + edge_mac, "Error": str(e)}
        return error_msg


def ingest_notifications(notify_json):
    # TODO: Log

    try:

        # Create a DB connection instance
        dbSession = DatabaseConnection()

        # Check the given JSON is a list
        if (isinstance(notify_json, list)):
            # Loop thru the given JsON
            print("List but single row expected, Exiting")
        else:
            edge_uuid = notify_json["edge_uuid"]
            motor_uuid = notify_json["motor_uuid"]
            event_uuid = notify_json["event_uuid"]
            event_name = notify_json["event_name"]
            event_action = notify_json["event_action"]
            action_status = notify_json["action_status"]
            created_on = notify_json["created_on"]

            # single Insert Statement
            dbSession.cosmos_session.execute(
                """
                insert into cloud_core.crane_notifications(motor_uuid, event_uuid, action_status, created_on, edge_uuid, event_action, event_name)
                values (%s,%s,%s,%s,%s,%s,%s)
                """,
                (motor_uuid, event_uuid, action_status, created_on, edge_uuid, event_action, event_name)
            )

        dbSession.shutCluster()
        return "Notification Ingested"

    except Exception as e:
        error_msg = {"Status": "Failed to ingest for Event UUID=" + event_uuid, "Error": str(e)}
        return error_msg

def update_notify_data(motor_uuid, event_uuid, action_status, created_on):
    # TODO: Log

    try:

        # Create a DB connection instance
        dbSession = DatabaseConnection()

        # convert created_on to epoch
        #utc_created_on = time.strptime(created_on, "%Y-%m-%d %H:%M:%S.%fZ")
        #epoch_created_on = str(calendar.timegm(utc_created_on)) + '000'

        utc_created_on = datetime.datetime.strptime(created_on, "%Y-%m-%d %H:%M:%S.%fZ")
        epoch_created_on = (utc_created_on - datetime.datetime(1970, 1, 1)).total_seconds() * 1000
        epoch_created_on = int(epoch_created_on)

        #if edge_mac is None:
        #    edge_mac = '00:0a:bb:11:22:22'

        # if version is None:
        #    version = 1

        # if sync_flag is None:
        #    sync_flag = True

        # single update Statement
        update_query = "update cloud_core.crane_notifications set action_status = " + str(action_status) + "  where motor_uuid='" + motor_uuid + "' and event_uuid = '" + event_uuid + "' and created_on = " + str(epoch_created_on)
        dbSession.cosmos_session.execute(update_query)

        dbSession.shutCluster()
        return "Event Action Status Updated as " + str(action_status) + " at Edge Notifications"


    except Exception as e:
        error_msg = {"Status": "Failed to update for Event UUID =" + event_uuid, "Error": str(e)}
        return error_msg


def get_notify_data(motor_list, interval):
    # TODO: Log
    # TODO: CONFIG

    try:

        # Create a DB connection instance
        dbSession = DatabaseConnection()

        #if table_name is None:
        #    table_name = 'edge_core.crane_details2'

        if interval is None:
            interval = 5

        #edge_uuid = 'b03108db-65f2-4d7c-b884-bb908d111400'

        now = datetime.datetime.now(timezone.utc)
        query_timestamp = now - datetime.timedelta(minutes=interval)
        epoch_query_timestamp = str(calendar.timegm(query_timestamp.timetuple())) + '000'


        motor_rows = []

        for motor_id in motor_list:

            motor_query = "select json motor_uuid, event_uuid, action_status, created_on, edge_uuid, event_action, event_name from cloud_core.crane_notifications where  motor_uuid = '" + motor_id + "' and created_on >= " + epoch_query_timestamp + "  and action_status  = False ALLOW FILTERING "


            for motor_row in dbSession.cosmos_session.execute(motor_query):
                #motor_rows.append(motor_row[0].replace("'", '"'))
                motor_rows.append(motor_row[0])
                # print( motor_rows)
                # print(json.dumps( motor_rows))
                #

        dbSession.shutCluster()
        return json.dumps(motor_rows)
    except Exception as e:
        error_msg = {"Status": "Failed to update for Event UUID =" + event_uuid, "Error": str(e)}
        return error_msg