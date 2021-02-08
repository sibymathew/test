device_to_cloud = {
	"meta_data": {
		"plc_count": 1,
		"device_count": 1
	},
	"plc": [{
		"name": "sample_name",
		"manufacturer": "Allen Bradley",
		"model": "1769-L33ER",
		"ip_addr": "10.0.0.181",
		"unique_id": "id-plc-abj83yeyeybsj96153"
	}],
	"devices": [{
		"name": "vfd1",
		"manufacturer": "yaskawa",
		"model": "F71",
		"ip_addr": "10.0.0.180",
		"unique_id": "id-dev-i72nsj8282",
		"plc": "id-plc-abj83yeyeybsj96153"
	}],
	"tags_kv": [{
		"id-dev-i72nsj8282": {
			"hoist_motor_amps": 2,
			"hoist_motor_rpms": 200,
			"hoist_speed": 1200,
			"hoist_motor_direction": 0,
			"hoist_run_time": 60,
			"hoist_start_stop": 10
		}
	}]
}

reduced_device_to_cloud = {
	"plc_name": "ac_plc",
	"vfd_name": "hoist",
	"motor_speed": 1000,
	"motor_direction": 1,
}
