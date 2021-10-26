from edge_loader import get_motor_data, ingest_hourly_stream
import time
import ast

try:
	da = get_motor_data("edge_core.crane_details", motor_uuid, 0)

	resp = ast.literal_eval(da)

	for data in resp:
		i = ast.literal_eval(data)
		ingest_hourly_stream(i["query_timestamp"], 3600)
except Exception as err:
	pass
