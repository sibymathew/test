from pycomm3 import LogixDriver

def dreams_plc_find_info(plc_ip_addr):
  with LogixDriver(plc_ip_addr) as plc:
    return plc.info

def dreams_plc_find_attributes(plc_ip_addr):

    #construct the API return object
    results = [] 
    
    with LogixDriver(plc_ip_addr) as plc:
        ...  # do nothing, we're just letting the plc initialize the tag list
     
    
     
    for typ in plc.data_types:
        #print(f'{typ} attributes: ', plc.data_types[typ]['attributes'])
        #results.append('{typ} attributes: ', plc.data_types[typ]['attributes'])
        results.append(typ)
        results.append(plc.data_types[typ]['attributes'])
    
    return results
    
def dreams_plc_find_pids(plc_ip_addr):

    #construct the API return object
    results = [] 
    
    with LogixDriver(plc_ip_addr) as plc:

        # PIDs are structures, the data_type attribute will be a dict with data type definition.
        # For tag types of 'atomic' the data type will a string, we need to skip those first.
        # Then we can just look for tags whose data type name matches 'PID'
        pid_tags = [
            tag
            for tag, _def in plc.tags.items()
            if _def['tag_type'] == 'struct' and _def['data_type']['name'] == 'PID'
        ]

        #print(pid_tags)
    return pid_tags


def dreams_plc_find_tags(plc_ip_addr):
  
    plc = LogixDriver(plc_ip_addr, init_program_tags=True)
    #print(plc.tags)
    return plc.tags