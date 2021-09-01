"""


"""
#supported block types
COILS = 1
DISCRETE_INPUTS = 2
HOLDING_REGISTERS = 3
ANALOG_INPUTS = 4

ADDRESS_RANGE = {
    COILS: 10,
    DISCRETE_INPUTS: 200001,
    HOLDING_REGISTERS: 660001,
    ANALOG_INPUTS: 70008

}

REGISTER_QUERY_FIELDS = {"bit": range(0, 32),
                         "byteorder": ["big", "little"],
                         "formatter": ["default", "float1"],
                         "scaledivisor": 1,
                         "scalemultiplier": 1,
                         "wordcount": 100,
                         "wordorder": ["big", "little"]}


BLOCK_TYPES = {"coils": COILS,
               "discrete_inputs": DISCRETE_INPUTS,
               "holding_registers": HOLDING_REGISTERS,
               "input_registers": ANALOG_INPUTS}
MODBUS_TCP_PORT = 8080