import serial
from pymodbus.client import ModbusTcpClient
from time import sleep
import struct
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder

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
    def reading_onoff(self, boolean):
        self.reading = boolean

    def read_float(self, label, reg1, reg2):
        """
        Inputs in two registers. The second register is optional.

        If two registers are entered, the data is a 32 bit data, else
        one register means 16 bit

        Returns a list of the modbus reponses (likely floats). If both
        registers are inputted,
        """
        while self.reading:
            # r2 = None
            r1 = self.client.read_holding_registers(reg1).registers[0]
            # if reg2:
            #     r2 = self.client.read_holding_registers(reg2).registers[0]

            # if r2:
            #     current_value = struct.unpack('f', struct.pack('<HH', int(r1), int(r2)))[0]
            # else:
                # current_value = struct.unpack('f', struct.pack('<HH', int(r1)))[0]
            current_value = struct.unpack('f', struct.pack('<HH', int(r1)))[0]
            current_value = round(current_value, 3)

            label.config(text=str(current_value))
            sleep(.5)


class one_bit_class(PLC):
    def write_onoff(self, address_num, boolean):
        self.client.write_coil(address=int(address_num), value=boolean)


class write_floats_class(PLC):
    def write_float(self, reg1, reg2):
        builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.LITTLE)
        builder.add_32bit_float(12.12)
        payload = builder.build()
        # result = self.client.write_registers(reg1, payload, skip_encode=True)
        result = self.client.write_registers(reg1, payload)
        print(result)