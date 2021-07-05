# pip install dse-driver
from dse.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from dse.query import tuple_factory
from dse.cluster import BatchStatement, SimpleStatement
from dse.auth import PlainTextAuthProvider
import uuid
import datetime


# Apache Cassandra DB connection (Edge)
# TODO: CONFIG
EDGE_DB_INSTANCE = '10.106.1.73'
EDGE_DB_PORT = 9042
EDGE_DB_USER = 'cassandra'
EDGE_DB_PASSWD = 'cassandra'
EDGE_KEY_SPACE = 'edge_core'

# Connect to database
class DatabaseConnection:
    def __init__(self):
        self.edge_auth_provider = None              
        self.edge_cluster = None
        self.edge_session = None 
        self.openSession()

    def openSession(self):
        self.edge_auth_provider = PlainTextAuthProvider(
            username=EDGE_DB_USER, password=EDGE_DB_PASSWD)        
        self.edge_cluster = Cluster(contact_points=[EDGE_DB_INSTANCE],port=EDGE_DB_PORT, auth_provider=self.edge_auth_provider)
        self.edge_session = self.edge_cluster.connect(EDGE_KEY_SPACE)


    def shutCluster(self):
        self.edge_cluster.shutdown()


def ingest_stream(crane_query_json):
    #TODO: Log
    
    try:
        
        # Create a DB connection instance
        dbSession = DatabaseConnection()
        
        #Check the given JSON is a list
        if (isinstance(crane_query_json,list)):
            #Loop thru the given JsON
            print("List")
        else:  
            edge_uuid = crane_query_json["edge_uuid"]
            # edge_mac =  crane_query_json["edge_mac"]
            total_motors = crane_query_json["total_motors"]
            query_timestamp= crane_query_json["timestamp"]        
            motor_data = crane_query_json["motor_data"]
            load_timestamp =   datetime.datetime.today()
            motor_uuid = crane_query_json["motor_uuid"]

            # single Insert Statement
            dbSession.edge_session.execute(
                    """
                    insert into edge_core.crane_details (edge_uuid, total_motors, query_timestamp,  motor_uuid, motor_data,load_timestamp) 
                    values (%s,%s,%s,%s,%s,%s)
                    """,
                    (edge_uuid, total_motors, query_timestamp, motor_uuid, motor_data, load_timestamp)
                )

        dbSession.shutCluster()
        return "Stream Ingested"
                        
    except Exception as e:
        error_msg = {"Status": "Failed to ingest for Edge UUID="+edge_uuid,"Error":str(e)}
        return error_msg                  
                    




