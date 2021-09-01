"""'
YW Gen
===============
"""
import kivy
import six
import struct
from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation
from kivy.uix.textinput import TextInput
from kivy.uix.settings import SettingsWithSidebar
from kivy.uix.listview import ListView, ListItemButton
from kivy.adapters.listadapter import ListAdapter
from yw.yw_generator.utils.constants import BLOCK_TYPES
from yw.yw_generator.utils import YWGen
from yw.yw_generator.utils.threadingJob import ThreadingJob

import re
import os
import platform

from json import load, dump
from kivy.config import Config
from kivy.lang import Builder
from pkg_resources import resource_filename
from serial.serialutil import SerialException

from distutils.version import LooseVersion

kivy.require('1.4.2')

if six.PY3:
    xrange = range

IS_DARWIN = platform.system().lower() == "darwin"
OSX_SIERRA = LooseVersion("10.12")
if IS_DARWIN:
    IS_HIGH_SIERRA_OR_ABOVE = LooseVersion(platform.mac_ver()[0])
else:
    IS_HIGH_SIERRA_OR_ABOVE = False

DEFAULT_SERIAL_PORT = '/dev/ptyp0' if not IS_HIGH_SIERRA_OR_ABOVE else '/dev/ttyp0'



MAP = {
    "coils": "coils",
    'discrete inputs': 'discrete_inputs',
    'input registers': 'input_registers',
    'holding registers': 'holding_registers'
}
PARENT = __name__.split(".")[0]





class Gen(BoxLayout):
    """
   
    """

    interfaces = ObjectProperty()

    tcp = ObjectProperty()
    serial = ObjectProperty()

    # Boxlayout to hold interface settings
    interface_settings = ObjectProperty()

    # TCP port
    port = ObjectProperty()

    # Toggle button to start/stop modbus server
    start_stop_server = ObjectProperty()

    # Container for slave list
    slave_pane = ObjectProperty()
    # slave start address textbox
    slave_start_add = ObjectProperty()
    # slave end address textbox
    slave_end_add = ObjectProperty()
    # Slave device count text box
    slave_count = ObjectProperty()
    # Slave list
    slave_list = ObjectProperty()

    def _init_registers(self):
        time_interval = int(eval(self.config.get("generation",
                                                 "time interval")))
        minval = int(eval(self.config.get("Modbus Protocol",
                                          "reg min")))
        maxval = int(eval(self.config.get("Modbus Protocol",
                                          "reg max")))
        self.block_start = int(eval(self.config.get("Modbus Protocol",
                                                    "block start")))
        self.block_size = int(eval(self.config.get("Modbus Protocol",
                                                   "block size")))
        self.word_order = self.config.get("Modbus Protocol", "word order")
        self.byte_order = self.config.get("Modbus Protocol", "byte order")

        self.data_model_input_registers.init(
            blockname="input_registers",
            generate=self.generating,
            time_interval=time_interval,
            minval=minval,
            maxval=maxval,
            _parent=self
        )
        self.data_model_holding_registers.init(
            blockname="holding_registers",
            generate=self.generating,
            time_interval=time_interval,
            minval=minval,
            maxval=maxval,
            _parent=self
        )

    def _register_config_change_callback(self, callback, section, key=None):
        self.config.add_callback(callback, section, key)

    def _update_serial_connection(self, *args):
        self._serial_settings_changed = True

    def _create_modbus_device(self):
        kwargs = {}
        create_new = False
        kwargs['byte_order'] = self.byte_order
        kwargs['word_order'] = self.word_order
        if self.active_server == "rtu":

            kwargs["baudrate"] = int(eval(
                self.config.get('Modbus Serial', "baudrate")))
            kwargs["bytesize"] = int(eval(
                self.config.get('Modbus Serial', "bytesize")))
            kwargs["parity"] = self.config.get('Modbus Serial', "parity")
            kwargs["stopbits"] = int(eval(
                self.config.get('Modbus Serial', "stopbits")))
            kwargs["xonxoff"] = bool(eval(
                self.config.get('Modbus Serial', "xonxoff")))
            kwargs["rtscts"] = bool(eval(
                self.config.get('Modbus Serial', "rtscts")))
            kwargs["dsrdtr"] = bool(eval(
                self.config.get('Modbus Serial', "dsrdtr")))
            kwargs["writetimeout"] = int(eval(
                self.config.get('Modbus Serial', "writetimeout")))
            kwargs["timeout"] = bool(eval(
                self.config.get('Modbus Serial', "timeout")))
        elif self.active_server == 'tcp':
            kwargs['address'] = self.config.get('Modbus Tcp', 'ip')
        if not self.modbus_device:
            create_new = True
        else:
            if self.modbus_device.server_type == self.active_server:

                if str(self.modbus_device.port) != str(self.port.text):
                    create_new = True
                if self._serial_settings_changed:
                    create_new = True
            else:
                create_new = True
        if create_new:

            self.modbus_device = YWGen(server=self.active_server,
                                            port=self.port.text,
                                            **kwargs
                                            )
            if self.slave is None:

                adapter = ListAdapter(
                        data=[],
                        cls=ListItemButton,
                        selection_mode='single'
                )
                self.slave = ListView(adapter=adapter)

            self._serial_settings_changed = False
        elif self.active_server == "rtu":
             self.modbus_device._serial.open()

    def start_server(self, btn):
        if btn.state == "down":
            try:
                self._start_server()
            except SerialException as e:
                btn.state = "normal"
                self.show_error("Error in opening Serial port: %s" % e)
                return
            btn.text = "Stop"
        else:
            self._stop_server()
            btn.text = "Start"

    def _start_server(self):
        self._create_modbus_device()

        self.modbus_device.start()
        self.server_running = True
        self.interface_settings.disabled = True
        self.interfaces.disabled = True
        self.slave_pane.disabled = False
        if len(self.slave_list.adapter.selection):
            self.data_model_loc.disabled = False
            if self.generating:
                self._generate()

    def _stop_server(self):
        self.generating = False
        self._generate()
        self.modbus_device.stop()
        self.server_running = False
        self.interface_settings.disabled = False
        self.interfaces.disabled = False
        self.slave_pane.disabled = True
        self.data_model_loc.disabled = True

    def update_tcp_connection_info(self, checkbox, value):
        self.active_server = "tcp"
        if value:
            self.interface_settings.current = checkbox
            if self.last_active_port['tcp'] == "":
                self.last_active_port['tcp'] = 5440
            self.port.text = self.last_active_port['tcp']
            self._restore()
        else:
            self.last_active_port['tcp'] = self.port.text
            self._backup()

    
    def start_stop_generation(self, btn):
        if btn.state == "down":
            self.generating = True
            self.reset_sim_btn.disabled = True
        else:
            self.generating = False
            self.reset_sim_btn.disabled = False
            if self.restart_simu:
                self.restart_simu = False
        self._generate()

    def _generate(self):
        self.data_model_coil.start_stop_generation(self.generating)
        self.data_model_discrete_inputs.start_stop_generation(self.generating)
        self.data_model_input_registers.start_stop_generation(self.generating)
        self.data_model_holding_registers.start_stop_generation(
            self.generating)

    def reset_generation(self, *args):
        if not self.generating:
            self.data_model_coil.reset_block_values()
            self.data_model_discrete_inputs.reset_block_values()
            self.data_model_input_registers.reset_block_values()
            self.data_model_holding_registers.reset_block_values()

    def _sync_modbus_block_values(self):
        """
        track external changes in modbus block values and sync GUI
        ToDo:
        A better way to update GUI when generation is on going  !!
        """
        if not self.generating:
            if self.active_slave:
                _data_map = self.data_map[self.active_slave]
                for block_name, value in _data_map.items():
                    updated = {}
                    for k, v in value['data'].items():
                        if block_name in ['input_registers',
                                          'holding_registers']:
                            actual_data, count = self.modbus_device.decode(
                                int(self.active_slave), block_name, k,
                                v['formatter']
                            )
                        else:
                            actual_data = self.modbus_device.get_values(
                                int(self.active_slave),
                                block_name,
                                int(k),

                            )
                            actual_data = actual_data[0]
                        try:
                            if actual_data != float(v['value']):
                                v['value'] = actual_data
                                updated[k] = v
                        except TypeError:
                            pass
                    if updated:
                        value['data'].update(updated)
                        self.refresh()

    def _backup(self):
        if self.slave is not None:
            self.slave.adapter.data = self.slave_list.adapter.data
        self._slave_misc[self.active_server] = [
            self.slave_start_add.text,
            self.slave_end_add.text,
            self.slave_count.text
        ]

    def _restore(self):
        if self.slave is None:

            adapter = ListAdapter(
                    data=[],
                    cls=ListItemButton,
                    selection_mode='single'
            )
            self.slave = ListView(adapter=adapter)
        self.slave_list.adapter.data = self.slave.adapter.data
        (self.slave_start_add.text,
         self.slave_end_add.text,
         self.slave_count.text) = self._slave_misc[self.active_server]
        self.slave_list._trigger_reset_populate()

    def save_state(self):
        with open(SLAVES_FILE, 'w') as f:
            slave = [int(slave_no) for slave_no in self.slave_list.adapter.data]
            slaves_memory = []
            for slaves, mem in self.data_map.items():
                for name, value in mem.items():
                    if len(value['data']) != 0:
                        slaves_memory.append((slaves, name,
                                              value['data']
                                              ))

            dump(dict(
                slaves_list=slave, active_server=self.active_server,
                port=self.port.text, slaves_memory=slaves_memory
            ), f, indent=4)

    def load_state(self):
        if not bool(eval(self.config.get("State", "load state"))) or \
                not os.path.isfile(SLAVES_FILE):
            return

        with open(SLAVES_FILE, 'r') as f:
            try:
                data = load(f)
            except ValueError as e:
                self.show_error(
                    "LoadError: Failed to load previous generation state : %s "
                    % e.message
                )
                return

            if ('active_server' not in data
                    or 'port' not in data
                    or 'slaves_list' not in data
                    or 'slaves_memory' not in data):
                self.show_error("LoadError: Failed to load previous "
                                "generation state : JSON Key Missing")
                return

            slaves_list = data['slaves_list']
            if not len(slaves_list):
                return

            if data['active_server'] == 'tcp':
                self.tcp.active = True
                self.serial.active = False
                self.interface_settings.current = self.tcp
            else:
                self.tcp.active = False
                self.serial.active = True
                self.interface_settings.current = self.serial

            self.active_server = data['active_server']
            self.port.text = data['port']
            self.word_order = self.config.get("Modbus Protocol", "word order")
            self.byte_order = self.config.get("Modbus Protocol", "byte order")
            self._create_modbus_device()

            start_slave = 0
            temp_list = []
            slave_count = 1
            for first, second in zip(slaves_list[:-1], slaves_list[1:]):
                if first+1 == second:
                    slave_count += 1
                else:
                    temp_list.append((slaves_list[start_slave], slave_count))
                    start_slave += slave_count
                    slave_count = 1
            temp_list.append((slaves_list[start_slave], slave_count))

            for start_slave, slave_count in temp_list:
                self._add_slaves(
                    self.slave_list.adapter.selection,
                    self.slave_list.adapter.data,
                    (True, start_slave, slave_count)
                )

            memory_map = {
                'coils': self.data_models.tab_list[3],
                'discrete_inputs': self.data_models.tab_list[2],
                'input_registers': self.data_models.tab_list[1],
                'holding_registers': self.data_models.tab_list[0]
            }
            slaves_memory = data['slaves_memory']
            for slave_memory in slaves_memory:
                active_slave, memory_type, memory_data = slave_memory
                _data = self.data_map[active_slave][memory_type]
                _data['data'].update(memory_data)
                _data['item_strings'] = list(sorted(memory_data.keys()))
                self.update_backend(int(active_slave), memory_type, memory_data)
                # self._update_data_models(active_slave,
                #                          memory_map[memory_type],
                #                          memory_data)


setting_panel = """
[
  {
    "type": "title",
    "title": "Modbus TCP Settings"
  },
  {
    "type": "string",
    "title": "IP",
    "desc": "Modbus Server IP address",
    "section": "Modbus Tcp",
    "key": "IP"
  },
  {
    "type": "title",
    "title": "Modbus Serial Settings"
  },
  {
    "type": "numeric",
    "title": "baudrate",
    "desc": "Modbus Serial baudrate",
    "section": "Modbus Serial",
    "key": "baudrate"
  },
  {
    "type": "options",
    "title": "bytesize",
    "desc": "Modbus Serial bytesize",
    "section": "Modbus Serial",
    "key": "bytesize",
    "options": ["5", "6", "7", "8"]

  },
  {
    "type": "options",
    "title": "parity",
    "desc": "Modbus Serial parity",
    "section": "Modbus Serial",
    "key": "parity",
    "options": ["N", "E", "O", "M", "S"]
  },
  {
    "type": "options",
    "title": "stopbits",
    "desc": "Modbus Serial stopbits",
    "section": "Modbus Serial",
    "key": "stopbits",
    "options": ["1", "1.5", "2"]

  },
  {
    "type": "bool",
    "title": "xonxoff",
    "desc": "Modbus Serial xonxoff",
    "section": "Modbus Serial",
    "key": "xonxoff"
  },
  {
    "type": "bool",
    "title": "rtscts",
    "desc": "Modbus Serial rtscts",
    "section": "Modbus Serial",
    "key": "rtscts"
  },
  {
    "type": "bool",
    "title": "dsrdtr",
    "desc": "Modbus Serial dsrdtr",
    "section": "Modbus Serial",
    "key": "dsrdtr"
  },
  {
    "type": "numeric",
    "title": "timeout",
    "desc": "Modbus Serial timeout",
    "section": "Modbus Serial",
    "key": "timeout"
  },
  {
    "type": "numeric",
    "title": "write timeout",
    "desc": "Modbus Serial write timeout",
    "section": "Modbus Serial",
    "key": "writetimeout"
  },
  {
    "type": "title",
    "title": "Modbus Protocol Settings"
  },
  {
    "type": "numeric",
    "title": "Block Start",
    "desc": "Modbus Block Start index",
    "section": "Modbus Protocol",
    "key": "Block Start"
  },
  { "type": "options",
    "title": "Byte Order",
    "desc": "Modbus Byte Order",
    "section": "Modbus Protocol",
    "key": "Byte Order",
    "options": ["big", "little"]
  },
  { "type": "options",
    "title": "Word Order",
    "desc": "Modbus Word Order",
    "section": "Modbus Protocol",
    "key": "Word Order",
    "options": ["big", "little"]
  },
  { "type": "numeric",
    "title": "Block Size",
    "desc": "Modbus Block Size for various registers/coils/inputs",
    "section": "Modbus Protocol",
    "key": "Block Size"
  },
  {
    "type": "numeric_range",
    "title": "Coil/Discrete Input MinValue",
    "desc": "Minimum value a coil/discrete input can hold (0).An invalid value will be discarded unless Override flag is set",
    "section": "Modbus Protocol",
    "key": "bin min",
    "range": [0,0]
  },
  {
    "type": "numeric_range",
    "title": "Coil/Discrete Input MaxValue",
    "desc": "Maximum value a coil/discrete input can hold (1). An invalid value will be discarded unless Override flag is set",
    "section": "Modbus Protocol",
    "key": "bin max",
    "range": [1,1]

  },
  {
    "type": "numeric_range",
    "title": "Holding/Input register MinValue",
    "desc": "Minimum value a registers can hold (0).An invalid value will be discarded unless Override flag is set",
    "section": "Modbus Protocol",
    "key": "reg min",
    "range": [0,65535]
  },
  {
    "type": "numeric_range",
    "title": "Holding/Input register MaxValue",
    "desc": "Maximum value a register input can hold (65535). An invalid value will be discarded unless Override flag is set",
    "section": "Modbus Protocol",
    "key": "reg max",
    "range": [0,65535]
  },
  {
    "type": "title",
    "title": "Logging"
  },
  { "type": "bool",
    "title": "Modbus Master Logging Control",
    "desc": " Enable/Disable Modbus Logging (console/file)",
    "section": "Logging",
    "key": "logging"
  },
  { "type": "bool",
    "title": "Modbus Console Logging",
    "desc": " Enable/Disable Modbus Console Logging",
    "section": "Logging",
    "key": "console logging"
  },
  {
    "type": "options",
    "title": "Modbus console log levels",
    "desc": "Log levels for modbus_tk",
    "section": "Logging",
    "key": "console log level",
    "options": ["INFO", "WARNING", "DEBUG", "CRITICAL"]
  },
  { "type": "bool",
    "title": "Modbus File Logging",
    "desc": " Enable/Disable Modbus File Logging",
    "section": "Logging",
    "key": "file logging"
  },
  {
    "type": "options",
    "title": "Modbus file log levels",
    "desc": "file Log levels for modbus_tk",
    "section": "Logging",
    "key": "file log level",
    "options": ["INFO", "WARNING", "DEBUG", "CRITICAL"]
  },

  {
    "type": "path",
    "title": "Modbus log file",
    "desc": "Modbus log file (changes takes place only after next start of app)",
    "section": "Logging",
    "key": "log file"
  },
  {
    "type": "title",
    "title": "generation"
  },
  {
    "type": "numeric",
    "title": "Time interval",
    "desc": "When generation is enabled, data is changed for every 'n' seconds defined here",
    "section": "generation",
    "key": "time interval"
  },
  {
    "type": "title",
    "title": "State"
  },
  {
    "type": "bool",
    "title": "Load State",
    "desc": "Whether the previous state should be loaded or not, if not the original state is loaded",
    "section": "State",
    "key": "load state"
  }

]
"""


class YWGenApp(App):
    '''The kivy App that runs the main root. All we do is build a Gui
    widget into the root.'''
    gui = None
    title = "YW Generator"
    settings_cls = None
    use_kivy_settings = True
    settings_cls = SettingsWithSidebar

    def build(self):
        self.gui = Gui(
            modbus_log=os.path.join(self.user_data_dir, 'modbus.log')
        )
        self.gui.load_state()
        return self.gui

    def on_pause(self):
        return True

    def on_stop(self):
        if self.gui.server_running:
            if self.gui.generating:
                self.gui.generating = False
                self.gui._generate()
            self.gui.modbus_device.stop()
        self.gui.sync_modbus_thread.cancel()
        self.config.write()
        self.gui.save_state()

    def show_settings(self, btn):
        self.open_settings()

    def build_config(self, config):
        config.add_section('Modbus Tcp')
        config.add_section('Modbus Protocol')
        config.add_section('Modbus Serial')
        config.set('Modbus Tcp', "ip", '127.0.0.1')
        config.set('Modbus Protocol', "block start", 0)
        config.set('Modbus Protocol', "block size", 100)
        config.set('Modbus Protocol', "byte order", 'big')
        config.set('Modbus Protocol', "word order", 'big')
        config.set('Modbus Protocol', "bin min", 0)
        config.set('Modbus Protocol', "bin max", 1)
        config.set('Modbus Protocol', "reg min", 0)
        config.set('Modbus Protocol', "reg max", 65535)
        config.set('Modbus Serial', "baudrate", 9600)
        config.set('Modbus Serial', "bytesize", "8")
        config.set('Modbus Serial', "parity", 'N')
        config.set('Modbus Serial', "stopbits", "1")
        config.set('Modbus Serial', "xonxoff", 0)
        config.set('Modbus Serial', "rtscts", 0)
        config.set('Modbus Serial', "dsrdtr", 0)
        config.set('Modbus Serial', "writetimeout", 2)
        config.set('Modbus Serial', "timeout", 2)

        config.add_section('Logging')
        config.set('Logging', "log file",  os.path.join(self.user_data_dir,
                                                        'modbus.log'))

        config.set('Logging', "logging", 1)
        config.set('Logging', "console logging", 1)
        config.set('Logging', "console log level", "DEBUG")
        config.set('Logging', "file log level", "DEBUG")
        config.set('Logging', "file logging", 1)

        config.add_section('generation')
        config.set('generation', 'time interval', 1)

        config.add_section('State')
        config.set('State', 'load state', 1)

    def build_settings(self, settings):
        settings.register_type("numeric_range", SettingIntegerWithRange)
        settings.add_json_panel('Modbus Settings', self.config,
                                data=setting_panel)

    def on_config_change(self, config, section, key, value):
        if config is not self.config:
            return
        token = section, key
        if token == ("generation", "time interval"):
            self.gui.change_generation_settings(time_interval=eval(value))
        if section == "Modbus Protocol" and key in ("bin max",
                                           "bin min", "reg max",
                                           "reg min", "override",
                                                    "word order", "byte order"):
            self.gui.change_datamodel_settings(key, value)
        if section == "Modbus Protocol" and key == "block start":
            self.gui.block_start = int(value)
        if section == "Modbus Protocol" and key == "block size":
            self.gui.block_size = int(value)

    def close_settings(self, *args):
        super(YWGenApp, self).close_settings()


def run():
    YWGenApp().run()
