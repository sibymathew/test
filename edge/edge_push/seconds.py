from edge_loader import check_rules, ingest_notifications
import time
import ast

try:
	to_time = round(time.time() * 1000)
	from_time = to_time - 3600000
	ingest_hourly_stream(from_time, to_time)
except Exception as err:
	pass
