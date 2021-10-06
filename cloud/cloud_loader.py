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
                query_timestamp = json_motor_data["query_timestamp"]
                utc_query_timestamp = datetime2.strptime(query_timestamp, "%Y-%m-%d %H:%M:%S.%fZ")
                epoch_query_timestamp = (utc_query_timestamp - datetime2(1970, 1, 1)).total_seconds()
                epoch_query_timestamp = int(epoch_query_timestamp * 1000)
                #print(epoch_query_timestamp)
                motor_data = str(json_motor_data["motor_data"])
                # print( motor_data )
                load_timestamp = datetime.datetime.now(timezone.utc)
                motor_uuid = json_motor_data["motor_uuid"]

                # single Insert Statement
                dbSession.cosmos_session.execute(
                    """
                    insert into cloud_core.crane_details (edge_uuid, total_motors, query_timestamp,  motor_uuid, motor_data,load_timestamp) 
                    values (%s,%s,%s,%s,%s,%s)
                    """,
                    (edge_uuid, total_motors, query_timestamp, motor_uuid, motor_data, load_timestamp)
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
            load_timestamp = datetime.datetime.now(timezone.utc)
            motor_uuid = crane_query_json["motor_uuid"]

            # single Insert Statement
            dbSession.cosmos_session.execute(
                """
                insert into cloud_core.crane_details (edge_uuid, total_motors, query_timestamp,  motor_uuid, motor_data,load_timestamp) 
                values (%s,%s,%s,%s,%s,%s)
                """,
                (edge_uuid, total_motors, query_timestamp, motor_uuid, motor_data, load_timestamp)
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

        if table_name is None:
            table_name = 'cloud_core.crane_config_data'

        if interval is None:
            interval = 2

        edge_uuid = 'b03108db-65f2-4d7c-b884-bb908d111400'

        now = datetime.datetime.now(timezone.utc)
        query_timestamp = now - datetime.timedelta(minutes=interval)
        epoch_query_timestamp = str(calendar.timegm(query_timestamp.timetuple())) + '000'

        motor_rows = []

        # for motor_id in motor_list:
        #     if interval == 0:
        #         motor_query = "select json edge_uuid, motor_uuid, query_timestamp,  load_timestamp, motor_data, total_motors from edge_core.crane_details where  motor_uuid = '" + motor_id + "' order by query_timestamp desc LIMIT 1"
        #     else:
        #         motor_query = "select json edge_uuid, motor_uuid, query_timestamp,  load_timestamp, motor_data, total_motors from edge_core.crane_details2 where  motor_uuid = '" + motor_id + "' and query_timestamp >= " + epoch_query_timestamp
        #
        #     for motor_row in dbSession.edge_session.execute(motor_query):
        #         #motor_rows.append(motor_row[0].replace("'", '"'))
        #         motor_rows.append(motor_row[0])
                # print( motor_rows)
                # print(json.dumps( motor_rows))
                #

        motor_query = "select json edge_uuid, motor_uuid, query_timestamp,  load_timestamp, motor_data, total_motors from edge_core.crane_details where  edge_mac = '" + motor_id + "' "

        dbSession.shutCluster()
        return json.dumps(motor_rows)

    except Exception as e:
        error_msg = {"Status": "Failed to pull data for Edge UUID=" + edge_uuid, "Error": str(e)}
        return error_msg
