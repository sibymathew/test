from vilimbu.client.sync import ModbusSerialClient as ModbusClient

vilimbu_modbus = ModbusClient(method='rtu', port='/dev/ttyUSB0', timeout=1, baudrate=115200)

print ('vilimbu modbus connected?: ' + str(vilimbu_modbus.connect()))

print(vilimbu_modbus)

resp = vilimbu_modbus.read_holding_registers(68,11,unit=0x1F)
print('vilimbu modbus registers:') 
print(resp)

for reg in resp.registers:
    print(reg)
