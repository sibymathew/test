from pycomm3 import LogixDriver

def dreams_plc_find_info(plc_ip_addr):
  with LogixDriver(plc_ip_addr) as plc:
    return plc.info

