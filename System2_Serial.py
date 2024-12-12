import serial
from pymodbus.client import ModbusTcpClient
from time import sleep
import struct
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder
import random


class Pump:
    def pump_connect(self, port_number):
        p = f'COM{port_number}'
        ser = serial.Serial(port=p, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                            bytesize=serial.EIGHTBITS, timeout=1)
        print("connected to: " + ser.portstr)
        return ser

    def pump_disconnect(self, ser):
        ser.close()
        print("disconnected from: " + ser.portstr)

    def eldex_pump_command(self, ser, command, value=''):
        # Format the command string and encode it to bytes
        command_str = f'{command}{value}\r\n'
        ser.write(command_str.encode('ascii'))

        # Read and print the response from the pump
        response = ser.readline().decode('ascii')
        print(f'{ser.portstr}: {response}')

    def UI22_pump_command(self, ser, command, address='01', value=''):
        # Format the command string and encode it to bytes
        command_str = f';{address},{command},{value}\r\n'
        ser.write(command_str.encode('ascii'))

        # Read and print the response from the pump
        response = ser.readline().decode('ascii')
        print(f'{ser.portstr}: {response}')

    def reglo_pump_command(self, ser, addr, command, data_parameter):
        pass


class Balance:
    def balance_connect(self, port_number):
        p = f'COM{port_number}'
        ser = serial.Serial(port=p, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                            bytesize=serial.EIGHTBITS, timeout=0.2)
        print("connected to: " + ser.portstr)
        return ser

    def balance_disconnect(self, ser):
        ser.close()
        print("disconnected from: " + ser.portstr)


class PLC:
    def __init__(self, host_num, port_num=None) -> None:
        if port_num:
            self.client = ModbusTcpClient(host=host_num, port=port_num)
        else:
            self.client = ModbusTcpClient(host=host_num)
        self.reading = False
        self.data = None

    def connect(self):
        self.client.connect()
        print("Connected")

    def disconnect(self):
        self.client.close()
        print("Disconnected")


class read_floats_class(PLC):
    def set_graph_obj(self, graph_obj):
        self.graph_obj = graph_obj

    def reading_onoff(self, boolean):
        self.reading = boolean

    def read_float(self, name, label, reg1, data_type, reg2=None):
        """
        Inputs in two registers. The second register is optional.

        If two registers are entered, the data is a 32 bit data, else
        one register means 16 bit

        Returns a list of the modbus reponses (likely floats). If both
        registers are inputted,
        """
        while self.reading:  # make sure to start a new thread when rechecking / restarting excel sheet
            r2 = None
            r1 = self.client.read_holding_registers(reg1, 1).registers[0]
            if reg2:
                r2 = self.client.read_holding_registers(reg2, 1).registers[0]

            if r2:
                current_value = struct.unpack('f', struct.pack('<HH', int(r1), int(r2)))[0]
            else:
                current_value = struct.unpack('f', struct.pack('<HH', int(r1)))[0]
            current_value = round(current_value, 3)

            label.config(text=str(current_value))

            # write into dict for graph
            self.graph_obj.update_dict(data_type, name, current_value)
            # excel_obj.write[data, data]
            sleep(.5)


class one_bit_class(PLC):
    def write_onoff(self, address_num, boolean):
        address_num = address_num.get()
        self.client.write_coil(address=int(address_num), value=boolean)


class write_floats_class(PLC):
    def write_float(self, reg1, reg2):
        reg1, reg2 = reg1.get(), reg2.get()
        builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.LITTLE)
        builder.add_32bit_float(12.12)
        payload = builder.build()
        result = self.client.write_registers(reg1, payload, skip_encode=True)
        print('here')
