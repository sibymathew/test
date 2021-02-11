from random import randint, random
from time import time

def test_data(data):
    if 'meta_data' in data:
        data['meta_data']['timestamp'] = int(time())
    if 'tags_kv' in data:
        for item in data['tags_kv']:
            if 'id-dev-i72nsj8282' in item:
                item['id-dev-i72nsj8282']['hoist_motor_amps'] = randint(0,3)
                item['id-dev-i72nsj8282']['hoist_motor_rpms'] = randint(1500, 3000)
                item['id-dev-i72nsj8282']['hoist_speed'] = randint(200,300)
                item['id-dev-i72nsj8282']['hoist_motor_direction'] = randint(0,1)
                item['id-dev-i72nsj8282']['hoist_run_time'] = randint(0,500)
                item['id-dev-i72nsj8282']['hoist_start_stop'] = randint(0,20)
    return data

def reduced_test_data(data):
    run_mode = ["rest brake set", "running up", "running down", "rest brake set, but torque proving in process"]
    data["motor_speed"] = randint(1500, 4000)
    data["run_mode"] = run_mode[randint(0, 3)]
    data["output_current"] = randint(10,30)/10
    data["timestamp"] = int(time())

    return data

def enumerate_data(data, id, series):
    resp = {}

    if id == 155:
        if series == 4:
            bit_list = ["running",
                        "zero_speed",
                        "rev_running",
                        "fault_reset",
                        "speed_agree",
                        "ready",
                        "alarm",
                        "faulted",
                        "oPE",
                        "Uv",
                        "local_remote",
                        "multi_function_digital_output",
                        "multi_function_photo_coupler1",
                        "multi_function_photo_coupler2",
                        "notdefined",
                        "ZSV"]

            key_list = ["motor_speed",
                        "torque_actual",
                        "pg_count_value",
                        "frequency_command",
                        "output_frequency",
                        "output_current",
                        "terminal_a2_input",
                        "main_circuit_dc_voltage",
                        "error_alarm_signal1",
                        "error_alarm_signal2",
                        "error_alarm_signal3",
                        "terminal_a3_input",
                        "terminal_s1_to_s8_input",
                        "terminal_a1_input",
                        "pg_counter_ch2"]

        if series == 3:
            bit_list = ["fwd_running",
                        "zsp",
                        "rev_running",
                        "reset",
                        "speed_agree",
                        "ready",
                        "alarm",
                        "fault",
                        "OPE",
                        "UV",
                        "local_remote",
                        "terminal_m1_m2",
                        "terminal_p1",
                        "terminal_p2",
                        "notdefined",
                        "ZSV"]

            key_list = ["output_speed",
                        "torque_reference",
                        "pg_count_value",
                        "frequency_command",
                        "output_frequency",
                        "output_current",
                        "inverter_terminal_a2_output",
                        "main_circuit_dc_voltage",
                        "error_alarm_signal1",
                        "error_alarm_signal2",
                        "error_alarm_signal3",
                        "inverter_terminal_a3",
                        "inverter_terminals_s1_to_s8_input",
                        "inverter_terminal_a1_input",
                        "pg_counter_ch2"]

        for i, dword in enumerate(data):
            if i == 0:
                # For bits 0, 1, 2 the data to be read togather for run_mode
                val = dword & 7
                if val == 2:
                    resp["run_mode"] = "rest brake set"
                elif val == 4:
                    resp["run_mode"] = "running up"
                elif val == 5:
                    resp["run_mode"] = "running down"
                elif val == 4:
                    resp["run_mode"] = "rest brake set, but torque proving in process"
                else:
                    resp["run_mode"] = "unknown " + str(val)

               for x in range(4,15):
                   # Omit the notdefined in the bit_list
                   if x != 14:
                       resp[bit_list[x]] = (dword & (1<<x)) >> x

            if i != 0 and i <16:
                if i == 5:
                    # Output Current
                    resp[key_list[i-1]] = dword * 0.01
                else:
                    resp[key_list[i-1]] = dword

        resp["timestamp"] = int(time())

    return resp
