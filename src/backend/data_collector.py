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
    data["motor_speed"] = randint(1500, 4000)
    data["motor_direction"] = randint(0, 1)
    data["timestamp"] = int(time())

    return data
