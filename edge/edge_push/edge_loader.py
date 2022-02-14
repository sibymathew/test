# pip install dse-driver
from dse.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from dse.query import tuple_factory
from dse.cluster import BatchStatement, SimpleStatement
from dse.auth import PlainTextAuthProvider
import uuid
from datetime import timezone
import datetime
import time
import calendar
import json
import os

import math

import pandas as pd
from pandas import json_normalize

# Apache Cassandra DB connection (Edge)
# TODO: CONFIG
# EDGE_DB_INSTANCE = '127.0.0.1'
EDGE_DB_PORT = 9042
EDGE_DB_USER = 'cassandra'
EDGE_DB_PASSWD = 'cassandra'
EDGE_KEY_SPACE = 'edge_core'
FALLBACK_CASSANDRA_IP = '10.0.1.20'

# Connect to database
class DatabaseConnection:
    def __init__(self):
        self.edge_auth_provider = None              
        self.edge_cluster = None
        self.edge_session = None 
        self.openSession()

    def openSession(self):
    
        # EDGE_DB_INSTANCE = os.environ["CASSANDRA_IP"]
        EDGE_DB_INSTANCE = os.getenv("CASSANDRA_IP",FALLBACK_CASSANDRA_IP)
        self.edge_auth_provider = PlainTextAuthProvider(
            username=EDGE_DB_USER, password=EDGE_DB_PASSWD)        
        self.edge_cluster = Cluster(contact_points=[EDGE_DB_INSTANCE],port=EDGE_DB_PORT, auth_provider=self.edge_auth_provider)
        self.edge_session = self.edge_cluster.connect(EDGE_KEY_SPACE)


    def shutCluster(self):
        self.edge_cluster.shutdown()


def pandas_factory(colnames, rows):
    return pd.DataFrame(rows, columns=colnames)


def clean_json(x):
    "Create apply function for decoding JSON"
    return json.loads(x)


def add_column(row,col_name):
    for data in row['motor_data']:
         if (data['k']) == col_name:
                if col_name == 'loadcell':
                    return (data['v']['crane_weight'])
                else:
                    return(data['v'])

def add_column2(row,crane_total_weight):
    for data in row['motor_data']:
         if (data['k']) == 'loadcell':
                load_pct = (((data['v']['crane_weight'])/crane_total_weight)*100)
                if  load_pct >= -99 and load_pct < 5 :
                    return '0%'
                elif load_pct >= 5 and load_pct < 15 :
                    return '10%'
                elif load_pct >= 15 and load_pct < 25 :
                    return '20%'
                elif load_pct >= 25 and load_pct < 35 :
                    return '30%'
                elif load_pct >= 35 and load_pct < 45 :
                    return '40%'
                elif load_pct >= 45 and load_pct < 55 :
                    return '50%'
                elif load_pct >= 55 and load_pct < 65 :
                    return '60%'
                elif load_pct >= 65 and load_pct < 75 :
                    return '70%'
                elif load_pct >= 75 and load_pct < 85 :
                    return '80%'
                elif load_pct >= 85 and load_pct < 95 :
                    return '90%'
                elif load_pct >= 95 and load_pct < 105 :
                    return '100%'
                elif load_pct >= 105 :
                    return '110%'
                else:
                    return 'NA'


def add_loadcell(row, hourly_df, lc_motor_id):
    if row['motor_uuid'] == lc_motor_id:
        for data in row['motor_data']:
            if (data['k']) == 'loadcell':
                return (data['v']['crane_weight'])
    else:
        lc_timestamp = row['query_timestamp']

        from_lc_timestamp = lc_timestamp - datetime.timedelta(seconds=1)
        to_lc_timestamp = lc_timestamp + datetime.timedelta(seconds=1)
        lc_where2 = (hourly_df['motor_uuid'] == lc_motor_id) & (hourly_df['query_timestamp'] >= from_lc_timestamp) & (
                    hourly_df['query_timestamp'] <= to_lc_timestamp)

        loadcell = hourly_df[lc_where2]['motor_data'].iloc[0]
        for data in loadcell:
            if (data['k']) == 'loadcell':
                return (data['v']['crane_weight'])


def add_loadrange(row, crane_total_weight):
    loadcell = row['loadcell']

    load_pct = ((loadcell / crane_total_weight) * 100)
    if load_pct >= -99 and load_pct < 5:
        return '0%'
    elif load_pct >= 5 and load_pct < 15:
        return '10%'
    elif load_pct >= 15 and load_pct < 25:
        return '20%'
    elif load_pct >= 25 and load_pct < 35:
        return '30%'
    elif load_pct >= 35 and load_pct < 45:
        return '40%'
    elif load_pct >= 45 and load_pct < 55:
        return '50%'
    elif load_pct >= 55 and load_pct < 65:
        return '60%'
    elif load_pct >= 65 and load_pct < 75:
        return '70%'
    elif load_pct >= 75 and load_pct < 85:
        return '80%'
    elif load_pct >= 85 and load_pct < 95:
        return '90%'
    elif load_pct >= 95 and load_pct < 105:
        return '100%'
    elif load_pct >= 105:
        return '110%'
    else:
        return 'NA'

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
            vfd_status = crane_query_json["vfd_status"]
            motor_data = str(crane_query_json["motor_data"])
            load_timestamp = round(time.time() * 1000)
            motor_uuid = crane_query_json["motor_uuid"]

            # single Insert Statement
            dbSession.edge_session.execute(
                    """
                    insert into edge_core.crane_details (edge_uuid, total_motors, query_timestamp,  motor_uuid, motor_data,load_timestamp,vfd_status) 
                    values (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (edge_uuid, total_motors, query_timestamp, motor_uuid, motor_data, load_timestamp, vfd_status)
                )

        dbSession.shutCluster()
        return "Stream Ingested"
                        
    except Exception as e:
        error_msg = {"Status": "Failed to ingest for Edge UUID="+edge_uuid,"Error":str(e)}
        return error_msg


def ingest_stream2(crane_query_json):
    # TODO: Log

    try:

        # Create a DB connection instance
        dbSession = DatabaseConnection()

        # Check the given JSON is a list
        if (isinstance(crane_query_json, list)):
            # Loop thru the given JsON
            print("List")
        else:
            edge_uuid = crane_query_json["edge_uuid"]
            # edge_mac =  crane_query_json["edge_mac"]
            total_motors = crane_query_json["total_motors"]
            query_timestamp = crane_query_json["timestamp"]
            vfd_status = crane_query_json["vfd_status"]
            motor_data = str(crane_query_json["motor_data"])
            # load_timestamp = datetime.datetime.today()
            load_timestamp = round(time.time() * 1000)
            motor_uuid = crane_query_json["motor_uuid"]

            # single Insert Statement
            dbSession.edge_session.execute(
                """
                insert into edge_core.crane_details2 (edge_uuid, total_motors, query_timestamp,  motor_uuid, motor_data,load_timestamp,vfd_status) 
                values (%s,%s,%s,%s,%s,%s,%s)
                """,
                (edge_uuid, total_motors, query_timestamp, motor_uuid, motor_data, load_timestamp, vfd_status)
            )

        dbSession.shutCluster()
        return "Stream Ingested"

    except Exception as e:
        error_msg = {"Status": "Failed to ingest for Edge UUID=" + edge_uuid, "Error": str(e)}
        return error_msg


def get_motor_data(table_name,motor_list, interval, from_date,to_date):
    # TODO: Log
    # TODO: CONFIG

    try:

        # Create a DB connection instance
        dbSession = DatabaseConnection()

        if table_name is None:
            table_name = 'edge_core.crane_details2'

        if interval is None:
            interval = 2

        edge_uuid = 'b03108db-65f2-4d7c-b884-bb908d111400'

        now = datetime.datetime.now(timezone.utc)
        query_timestamp = now - datetime.timedelta(minutes=interval)
        epoch_query_timestamp = str(calendar.timegm(query_timestamp.timetuple())) + '000'


        motor_rows = []

        for motor_id in motor_list:
            if table_name == 'crane_details' and from_date is not None and to_date is not None:
                motor_query = "select json edge_uuid, motor_uuid, query_timestamp,  load_timestamp,vfd_status, motor_data, total_motors from edge_core.crane_details where  motor_uuid = '" + motor_id + "' and query_timestamp >= " + str(from_date) + " and query_timestamp <= " + str(to_date)

            elif table_name == 'crane_details' and interval == 0:
                #  uncomment it. This is just one time test for Blues Xfer to Cloud.
                motor_query = "select json edge_uuid, motor_uuid, query_timestamp,  load_timestamp,vfd_status, motor_data, total_motors from edge_core.crane_details where  motor_uuid = '" + motor_id + "' order by query_timestamp desc LIMIT 1"

                # comment it. This is just one time test for Blues Xfer to Cloud.
                # motor_query = "select json edge_uuid, motor_uuid, query_timestamp,  load_timestamp,vfd_status, motor_data, total_motors from edge_core.crane_details where  motor_uuid = '" + motor_id + "' and query_timestamp > 1634830958000"
            elif table_name == 'crane_details' and interval > 0:
                motor_query = "select json edge_uuid, motor_uuid, query_timestamp,  load_timestamp,vfd_status, motor_data, total_motors from edge_core.crane_details where  motor_uuid = '" + motor_id + "' and query_timestamp >= " + epoch_query_timestamp

            else:
                motor_query = "select json edge_uuid, motor_uuid, query_timestamp,  load_timestamp,vfd_status, motor_data, total_motors from edge_core.crane_details2 where  motor_uuid = '" + motor_id + "' and query_timestamp >= " + epoch_query_timestamp


            for motor_row in dbSession.edge_session.execute(motor_query):
                #motor_rows.append(motor_row[0].replace("'", '"'))
                motor_rows.append(motor_row[0])
                # print( motor_rows)
                # print(json.dumps( motor_rows))
                #

        dbSession.shutCluster()
        return json.dumps(motor_rows)

    except Exception as e:
        error_msg = {"Status": "Failed to pull data for Edge UUID=" + edge_uuid, "Error": str(e)}
        return error_msg

def ingest_config(config_json):
    # TODO: Log

    try:

        # Create a DB connection instance
        dbSession = DatabaseConnection()

        # Check the given JSON is a list
        if (isinstance(config_json, list)):
            # Loop thru the given JsON
            print("List")
        else:
            edge_uuid = config_json["edge_uuid"]
            edge_mac =  config_json["edge_mac"]
            version = config_json["version"]
            config_sync_flag = config_json["config_sync_flag"]
            config_data = str(config_json["config_data"])
            created_by = config_json["created_by"]
            created_on = config_json["created_on"]

            # single Insert Statement
            dbSession.edge_session.execute(
                """
                insert into edge_core.crane_config (edge_uuid ,edge_mac ,version,config_sync_flag,config_data ,created_by, created_on)
                values (%s,%s,%s,%s,%s,%s,%s)
                """,
                (edge_uuid ,edge_mac ,version,config_sync_flag,config_data ,created_by, created_on)
            )

        dbSession.shutCluster()
        return "Config Ingested"

    except Exception as e:
        error_msg = {"Status": "Failed to ingest for Edge MAC=" + edge_mac, "Error": str(e)}
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
        update_query = "update edge_core.crane_config set config_sync_flag = " + str(sync_flag) + "  where edge_mac='" + edge_mac + "' and version = " + str(
            version)
        dbSession.edge_session.execute(update_query)

        dbSession.shutCluster()
        return "Flag Updated as " + str(sync_flag) + " at Edge Config"


    except Exception as e:
        error_msg = {"Status": "Failed to ingest for Edge MAC=" + edge_mac, "Error": str(e)}
        return error_msg

def ingest_hourly_stream(from_query_timestamp, to_query_timestamp, crane_weight, pull_interval,lc_motor_id):
    try:

        ingest_status = []

        # Create a DB connection instance
        dbSession = DatabaseConnection()

        dbSession.edge_session.row_factory = pandas_factory
        dbSession.edge_session.default_fetch_size = None

        # from_query_timestamp = 1630609200000
        # to_query_timestamp = 1630612800000

        # query for given query_timestamp interval. Should be an hour
        # TO DO:  iteration for multiple hours, loop by hour
        hourly_query = "SELECT edge_uuid,motor_uuid,query_timestamp, motor_data, vfd_status FROM edge_core.crane_details where query_timestamp >= " + str(
            from_query_timestamp) + " and  query_timestamp <= " + str(to_query_timestamp) + " ALLOW FILTERING"

        hourly_df = pd.DataFrame(dbSession.edge_session.execute(hourly_query, timeout=None))

        # Remove empty motor_data
        hourly_df = hourly_df[hourly_df.motor_data.apply(lambda x: len(str(x)) > 5)]
        # Convert motor_data string column with double quotes
        hourly_df['motor_data'] = hourly_df['motor_data'].str.replace("'", '"')

        # hourly_df0 = hourly_df

        # Column names that contain JSON
        json_cols = ['motor_data']

        # Apply the function column wise to each column of interest



        for x in json_cols:
            hourly_df[x] = hourly_df[x].apply(clean_json)

        ####  The following description of items to be uploaded on an 8 hour schedule.
        ####  There may be additional data points added as we incorporate additional sensors/ crane odometer calculations, but this should at least get us started.
        # Run time for all motions (maximum value, per hour*) [to allow evaluation of how much time per hour the unit is being run; to be uploaded as raw data rather than calculated at the edge, otherwise some shorter run times might be lost]
        # Number of starts/ stops for all motions (per hour) [calculated as (value at end of hour) - (value at start of hour)]
        # Load weight (average and maximum values, per hour) [ignoring values < X lbs, configurable]
        # Motor amps for all motors (average and maximum values, per hour) [averaged only while drive is running]
        # Motor RPM for all motors (average absolute** value, per hour) [averaged only while drive is running. Note: over-speeding will be separately defined as an “event” that will trigger a high-res upload, so the “maximum” value is not needed]
        # *Note 1: “per hour” indicates real time periods (i.e.- 7:00:00-7:59:59, 8:00:00-8:59:59, etc.), not just arbitrary 60-minute periods.
        # **Note 2: “absolute” values are listed for items that may have negative values, depending on how they are evaluated in the edge.
        #            For example, I was hoping that we would eventually have “Bridge FWD” RPM shown on the charts as positive and “Bridge REV” RPM shown as negative.
        #            These values should be considered according to their absolute values, regardless of direction.
        ####
        #### Future:
        # Vibration data (average and maximum values, per hour)
        # Temperature data (average and maximum values, per hour)
        #  Crane Odometer calculations (TBD)
        ####

        # TO DO: Add Load Weight   == DONE
        # TO DO: [averaged only while drive is running] == DONE
        # TO DO: [averaged only while drive is running. Note: over-speeding will be separately defined as an “event” that will trigger a high-res upload, so the “maximum” value is not needed]  DONE
        # TO DO: “absolute” values - Motor RPM  == DONE
        # Prepare the required columns and append to the dataframe

        crane_total_weight = crane_weight

        hourly_df['motor_amps'] = hourly_df.apply(lambda row: add_column(row, 'motor_amps'), axis=1)
        hourly_df['motor_in_rpm'] = hourly_df.apply(lambda row: add_column(row, 'motor_in_rpm'), axis=1)

       #hourly_df['loadcell'] = hourly_df.apply(lambda row: add_column(row, 'loadcell'), axis=1)
        hourly_df['loadcell'] = hourly_df.apply(lambda row: add_loadcell(row, hourly_df, lc_motor_id), axis=1)

        hourly_df['run_time'] = hourly_df.apply(lambda row: add_column(row, 'run_time'), axis=1)
        hourly_df['number_of_start_stop'] = hourly_df.apply(lambda row: add_column(row, 'number_of_start_stop'),
                                                                axis=1)

        #hourly_df['load_pct_range'] = hourly_df.apply(lambda row: add_column2(row, crane_total_weight), axis=1)
        hourly_df['load_pct_range'] = hourly_df.apply(lambda row: add_loadrange(row, crane_total_weight), axis=1)

        # only when Drive is running,
        # hourly_odometer = hourly_df[hourly_df['motor_in_rpm'] > 0].groupby(
        #    ['edge_uuid', 'motor_uuid', 'load_pct_range']).agg({'load_pct_range': ['count'], 'motor_in_rpm': ['mean']})
        hourly_odometer = hourly_df[hourly_df['motor_in_rpm'] > 0].groupby(['edge_uuid', 'motor_uuid', 'load_pct_range']).agg(
            {'load_pct_range': ['count'], 'motor_in_rpm': ['mean']})

        # prepare the motor_data for the hour, back to be ingested
        data = {}
        datapoints = []

        hourly_top = (
            hourly_df
                .sort_values('query_timestamp', ascending=False)
                .groupby(['edge_uuid', 'motor_uuid'])
                .head(1)
                .reset_index(drop=True)
        )

        # only one record but "mean" is just for uniform data structure to merge
        # hourly_calc_runtime = hourly_top.groupby(['edge_uuid', 'motor_uuid']).agg(
        #    {'run_time': ['mean', lambda x: abs(x.mean())]})
        # hourly_calc_start = hourly_top.groupby(['edge_uuid', 'motor_uuid']).agg(
        #    {'number_of_start_stop': ['mean', lambda x: abs(x.mean())]})
        # hourly_final_df0 = pd.merge(hourly_calc_runtime, hourly_calc_start, on=['edge_uuid', 'motor_uuid'],
        #                            how="outer")

        hourly_calc_runtime = hourly_df.groupby(['edge_uuid', 'motor_uuid']).agg({'run_time': ['min', 'max']})
        hourly_calc_start = hourly_df.groupby(['edge_uuid', 'motor_uuid']).agg({'number_of_start_stop': ['min', 'max']})
        hourly_final_df0 =  pd.merge(hourly_calc_runtime, hourly_calc_start, on=['edge_uuid', 'motor_uuid'], how="outer")

        hourly_calc_status = hourly_top.groupby(['edge_uuid', 'motor_uuid']).agg({'vfd_status': ['mean', lambda x : abs(x.mean())]})
        hourly_final_df0 = pd.merge(hourly_final_df0, hourly_calc_status, on=['edge_uuid', 'motor_uuid'], how="outer")


        # Run Time, Total Motor Start/Stop
        # hourly_df.sort_values(by='query_timestamp', ascending = False, inplace=True)
        # row1 = hourly_df.iloc[0]
        # datapoint = {"k": "run_time", "v": row1['run_time'], "d": "Run Time"}
        # print(datapoint)
        # datapoints.append(datapoint)

        # datapoint = {"k": "number_of_start_stop", "v": row1['number_of_start_stop'], "d": "Total Motor Start/Stop"}
        # print(datapoint)
        # datapoints.append(datapoint)

        # Average motor_amps
        # to get mean and max values
        # hourly_calc_df1 = hourly_df.groupby(['edge_uuid', 'motor_uuid']).agg({'motor_amps': ['mean', 'max']})
        # only when Drive is running, so select only amps > 0
        hourly_calc_df1 = hourly_df[hourly_df['motor_amps'] > 0].groupby(['edge_uuid', 'motor_uuid']).agg(
            {'motor_amps': ['mean', 'max']})

        # hourly_calc_df1.head()

        # hourly_calc_df2 = hourly_df.groupby(['edge_uuid', 'motor_uuid']).agg({'motor_in_rpm': ['mean']})
        # only when Drive is running, so select only motor_in_rpm > 0  and only absolute values
        hourly_calc_df2 = hourly_df[hourly_df['motor_in_rpm'] > 0].groupby(['edge_uuid', 'motor_uuid']).agg(
            {'motor_in_rpm': [('mean', lambda x : abs(x.mean())),('max', lambda x : abs(x.max()))]})
        # hourly_calc_df2.head()

        # only when Drive is running,
        #hourly_calc_df3 = hourly_df[hourly_df['loadcell'] > 0].groupby(['edge_uuid', 'motor_uuid']).agg(
        #    {'loadcell': ['mean', 'max']})
        # We would want to consider static loads
        # into the hourly load cell average (so that if the crane is sitting idle with a 10 ton load suspended, that load would still contribute to the hourly average load).
        # For the odometer run_time, however, static load would not be included (because a static load does not contribute to bearing/ component wear).
        hourly_calc_df3 = hourly_df.groupby(['edge_uuid', 'motor_uuid']).agg(
            {'loadcell': ['mean', 'max']})

        hourly_final_df = pd.merge(hourly_calc_df1, hourly_calc_df2, on=['edge_uuid', 'motor_uuid'], how="outer")
        hourly_final_df = pd.merge(hourly_final_df, hourly_calc_df3, on=['edge_uuid', 'motor_uuid'], how="outer")

        hourly_final_df = pd.merge(hourly_final_df, hourly_final_df0, on=['edge_uuid', 'motor_uuid'], how="outer")

        # hourly_final_df.head()

        for i, r in hourly_final_df.iterrows():
            datapoints = []

            data["edge_uuid"] = i[0]
            data["motor_uuid"] = i[1]
            data["total_motors"] = 0
            data["timestamp"] = to_query_timestamp
            data["vfd_status"] = int(r['vfd_status']['mean'])

            this_edge_uuid = i[0]
            this_motor_uuid = i[1]

            dt = datetime.datetime.now(timezone.utc)
            utc_time = dt.replace(tzinfo=timezone.utc)
            # utc_timestamp = utc_time.timestamp()
            data["load_timestamp"] = utc_time.timestamp()

            hourly_runtime = int((r['run_time']['max'] - r['run_time']['min']) + 1)

            datapoint = {"k": "run_time", "v": {"cumulative": r['run_time']['max'], "hourly": hourly_runtime},
                         'u': 'Minutes', "d": "Run Time"}
            # print(datapoint)
            datapoints.append(datapoint)

            hourly_starts = int((r['number_of_start_stop']['max'] - r['number_of_start_stop']['min']) + 1)

            datapoint = {"k": "number_of_start_stop",
                         "v": {"cumulative": r['number_of_start_stop']['max'], "hourly": hourly_starts},
                         "d": "Total Motor Start/Stop"}
            # print(datapoint)
            datapoints.append(datapoint)

            if not math.isnan(r['motor_amps']['mean']):
                datapoint = {"k": "motor_amps", "v": {"avg": r['motor_amps']['mean'], "max": r['motor_amps']['max']},
                         "u": "Amps", "d": "Motor Amps"}
                datapoints.append(datapoint)

            # datapoint = {"k": "motor_amps_max", "v": r['motor_amps']['max'], "d": "Motor Amps Max"}
            # datapoints.append(datapoint)

            if not math.isnan(r['motor_in_rpm']['mean']):
                datapoint = {"k": "motor_in_rpm", "v": {"avg": r['motor_in_rpm']['mean'],"max":r['motor_in_rpm']['max']}, "u": "RPM",
                         "d": "Motor In RPM"}
                datapoints.append(datapoint)

            if not math.isnan(r['loadcell']['mean']):
                datapoint = {"k": "loadcell", "v": {"avg": r['loadcell']['mean'], "max": r['loadcell']['max']},
                         "u": {"crane_weight": "ton"}}
                datapoints.append(datapoint)
            # datapoint = {"k": "loadcell_weight_max", "v": r['loadcell']['max'], "d": "Loadcell Crane Weight Max"}
            # datapoints.append(datapoint)

            load_pct_dict = {}
            load_pct_avail = []

            for i, r in hourly_odometer.iterrows():
                load_pct_dict1 = {}

                odo_edge_uuid = i[0]
                odo_motor_uuid = i[1]
                load_pct_range = i[2]

                if load_pct_range =='NA':
                    print('skip')
                else:
                    if this_motor_uuid == odo_motor_uuid:
                        # pull_interval = 60
                        odometer_runtime = ((r['load_pct_range']['count']) * pull_interval) / 60
                        load_pct_desc = "Below " + load_pct_range

                        load_pct_dict1 = {load_pct_range: {"records": r['load_pct_range']['count'],
                                                           "motor_speed_avg": r['motor_in_rpm']['mean'],
                                                           "run_time": odometer_runtime, "desc": load_pct_desc}}
                        load_pct_avail.append(load_pct_range)

                        # print(load_pct_avail)

                        load_pct_dict.update(load_pct_dict1)
                        # print(load_pct_dict)


            iMissing = 0
            load_pct_ranges = ['0%', '10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '90%', '100%', '110%']
            load_pct_ranges_set = set(load_pct_ranges)
            load_pct_avail_set = set(load_pct_avail)

            load_pct_missing_set = list(sorted(load_pct_ranges_set - load_pct_avail_set))
            # print(load_pct_missing_set)
            # print(load_pct_dict)
            # odometer_dict = {"k": "crane_odometer", "v":{load_pct_dict}}

            # Iterating thru missing range
            while iMissing < len(load_pct_missing_set):
                load_pct_desc = "Below " + load_pct_missing_set[iMissing]
                load_pct_dict1 = {load_pct_missing_set[iMissing]: {"records": 0, "motor_speed_avg": 0, "run_time": 0,
                                                                   "desc": load_pct_desc}}
                load_pct_dict.update(load_pct_dict1)
                iMissing += 1

            # print(load_pct_avail)
            # print(datapoints)

            # print(odometer_dict)
            odometer_dict = {"k": "crane_odometer", "v": {}}
            odometer_dict['v'] = load_pct_dict

            datapoint = odometer_dict
            datapoints.append(datapoint)

            data["motor_data"] = datapoints
            # print(json.dumps(data, indent=4, sort_keys=True))

            stream_status = {"motor_uuid": data["motor_uuid"], "msg": ingest_stream2(data)}
            ingest_status.append(stream_status)

        return ingest_status


    except Exception as e:
        error_msg = {"Status": "Failed to ingest for Edge UUID=" + edge_uuid, "Error": str(e)}
        return error_msg

def del_motor_data(table_name,motor_list, interval):
    # TODO: Log
    # TODO: CONFIG

    try:

        # Create a DB connection instance
        dbSession = DatabaseConnection()


        return_status = []

        if table_name is None:
            table_name = 'edge_core.crane_details'

        if interval is None:
            interval = 3

        #edge_uuid = 'b03108db-65f2-4d7c-b884-bb908d111400'

        now = datetime.datetime.now(timezone.utc)
        query_timestamp = now - datetime.timedelta(days=interval)
        epoch_query_timestamp = str(calendar.timegm(query_timestamp.timetuple())) + '000'

        motor_rows = []
        if motor_list:
            for motor_id in motor_list:
                if table_name == 'edge_core.crane_details':
                    motor_query = "delete from edge_core.crane_details where  motor_uuid = '" + motor_id + "' and query_timestamp < " + epoch_query_timestamp
                    dbSession.edge_session.execute(motor_query)
                    msg = "Deleted for " + str(interval) +" days"
                    del_status = {"motor_uuid": motor_id, "msg": msg }
                elif table_name == 'edge_core.crane_details2':
                    motor_query = "delete from edge_core.crane_details2 where  motor_uuid = '" + motor_id + "'"
                    dbSession.edge_session.execute(motor_query)
                    msg = "Deleted for " + str(interval) + " days"
                    del_status = {"motor_uuid": motor_id, "msg": msg}
                else:
                    msg = "No right table passed"
                    del_status = {"motor_uuid": motor_id, "msg": msg}
        else:

            motor_uuid_query = "select distinct motor_uuid from edge_core." + table_name

            for motor_row in dbSession.edge_session.execute(motor_uuid_query):
                motor_id = motor_row[0]
                # print(motor_row[0])
                if table_name == 'edge_core.crane_details':
                    motor_query = "delete from edge_core.crane_details where  motor_uuid = '" + motor_id + "' and query_timestamp < " + epoch_query_timestamp
                    dbSession.edge_session.execute(motor_query)
                    msg = "Deleted for " + str(interval) + " days"
                    del_status = {"motor_uuid": motor_id, "msg": msg }
                elif table_name == 'edge_core.crane_details2':
                    motor_query = "delete from edge_core.crane_details2 where  motor_uuid = '" + motor_id + "'"
                    dbSession.edge_session.execute(motor_query)
                    msg = "Deleted for " + str(interval) + " days"
                    del_status = {"motor_uuid": motor_id, "msg": msg}
                else:
                    msg = "No right table passed"
                    del_status = {"motor_uuid": motor_id, "msg": msg}



        dbSession.shutCluster()
        return del_status

    except Exception as e:
        error_msg = {"Status": "Failed to pull data for Edge UUID=" + edge_uuid, "Error": str(e)}
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
            event_action = str(notify_json["event_action"])
            action_status = notify_json["action_status"]
            created_on = notify_json["created_on"]

            # single Insert Statement
            dbSession.edge_session.execute(
                """
                insert into edge_core.crane_notifications(motor_uuid, event_uuid, action_status, created_on, edge_uuid, event_action, event_name)
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
        update_query = "update edge_core.crane_notifications set action_status = " + str(action_status) + "  where motor_uuid='" + motor_uuid +  "' and created_on = " + str(epoch_created_on)
        dbSession.edge_session.execute(update_query)

        dbSession.shutCluster()
        return "Event Action Status Updated as " + str(action_status) + " at Edge Notifications"


    except Exception as e:
        error_msg = {"Status": "Failed to update for Event UUID =" + event_uuid, "Error": str(e)}
        return error_msg
        #return update_query


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

            motor_query = "select json motor_uuid, event_uuid, action_status, created_on, edge_uuid, event_action, event_name from edge_core.crane_notifications where  motor_uuid = '" + motor_id + "' and created_on >= " + epoch_query_timestamp + "  and action_status  = False ALLOW FILTERING "


            for motor_row in dbSession.edge_session.execute(motor_query):
                #motor_rows.append(motor_row[0].replace("'", '"'))
                motor_rows.append(motor_row[0])
                # print( motor_rows)
                # print(json.dumps( motor_rows))
                #

        dbSession.shutCluster()
        return json.dumps(motor_rows)
    except Exception as e:
        error_msg = {"Status": "Failed to get for Motor List =" + str(motor_list), "Error": str(e)}
        return error_msg

def get_notify_data_all(event_uuid, interval):
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

            motor_query = "select json motor_uuid, event_uuid, action_status, created_on, edge_uuid, event_action, event_name from edge_core.crane_notifications where  event_uuid = '" + event_uuid + "' and created_on >= " + epoch_query_timestamp + " ALLOW FILTERING "


            for motor_row in dbSession.edge_session.execute(motor_query):
                #motor_rows.append(motor_row[0].replace("'", '"'))
                motor_rows.append(motor_row[0])
                # print( motor_rows)
                # print(json.dumps( motor_rows))
                #

        dbSession.shutCluster()
        return json.dumps(motor_rows)
    except Exception as e:
        error_msg = {"Status": "Failed to get for Motor List =" + str(motor_list), "Error": str(e)}
        return error_msg

def check_rules(rules_json):
    try:

        # list of events occured
        events = []
        # Create a DB connection instance
        dbSession = DatabaseConnection()

        dbSession.edge_session.row_factory = pandas_factory
        dbSession.edge_session.default_fetch_size = None

        # from_query_timestamp = 1630609200000
        # to_query_timestamp = 1630612800000

        df_rules = pd.json_normalize(rules_json)

        # check rule by rule
        for i, r in df_rules.iterrows():

            event_uuid = r['event_uuid']
            motor_uuid = r['motor_uuid']
            # motor_uuid='3898072346710690'
            key = r['key']
            rcondition = r['rcondition']
            value = r['value']
            event_seconds = r['event_seconds']

            now = datetime.datetime.now(timezone.utc)
            query_timestamp = now - datetime.timedelta(seconds=event_seconds)
            epoch_query_timestamp = str(calendar.timegm(query_timestamp.timetuple())) + '000'
            # epoch_query_timestamp = 1630609200000

            # query for given query_timestamp interval. Should be an hour
            # TO DO:iteration for multiple hours, loop by hour
            rule_query = "SELECT edge_uuid,motor_uuid,query_timestamp, motor_data, vfd_status FROM edge_core.crane_details where motor_uuid ='" + motor_uuid + "' and query_timestamp >= " + str(
                epoch_query_timestamp) + " ALLOW FILTERING"
            rule_df = pd.DataFrame(dbSession.edge_session.execute(rule_query, timeout=None))

            # Check any data returned
            if len(rule_df.index) > 0:

                # Remove empty motor_data
                rule_df = rule_df[rule_df.motor_data.apply(lambda x: len(str(x)) > 5)]
                # Convert motor_data string column with double quotes
                rule_df['motor_data'] = rule_df['motor_data'].str.replace("'", '"')

                # rule_df0 = rule_df
                # Column names that contain JSON
                json_cols = ['motor_data']

                # Apply the function column wise to each column of interest
                for x in json_cols:
                    rule_df[x] = rule_df[x].apply(clean_json)

                rule_df[key] = rule_df.apply(lambda row: add_column(row, key), axis=1)
                rule_filter = 'motor_uuid == "' + motor_uuid + '" and ' + key + rcondition + value
                # print(rule_filter )
                rule_df_filter = rule_df.query(rule_filter)
                row_kount = len(rule_df_filter.index)
                # print(row_kount)

                if row_kount > 0:
                    events.append(event_uuid)

        dbSession.shutCluster()
        return events


    except Exception as e:
        error_msg = {"Status": "Failed to check rules for Event UUID=" + event_uuid, "Error": str(e)}
        return error_msg