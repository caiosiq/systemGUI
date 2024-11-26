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

    # --- ELDEX --- #
    # 'run': 'RU',
    # 'stop': 'ST',
    # 'set flow rate': 'SFxx.xxx',
    # 'read flow rate': ' RF',
    # 'read ID': 'ID',
    # 'read pressure': 'RP',
    # 'set high pressure limit': 'SHxxxx',
    # 'set low pressure limit': 'SLxxxx',
    # 'read high pressure limit': 'RH',
    # 'read low pressure limit': 'RL',
    # 'set compressibility compensation': 'SCxx',
    # 'read compressibility compensation': 'RC',
    # 'set refill rate factor': 'SRx',
    # 'read refill rate factor': 'RR',
    # 'disables keypad': 'KD',
    # 'enables keypad': 'KE',
    # 'set piston diameter': 'SDx',
    # 'read piston diameter': 'RD',
    # 'set stroke': 'SSx',
    # 'read stroke': 'RS',
    # 'set material': 'SMx',
    # 'read material': 'RM',
    # 'read fault status': 'RX',
    # 'set LED to red and stops pump': 'SX',
    # 'read attributes': 'RI',
    # 'reset command buffer': 'Z'

    def eldex_pump_command(self, ser, command, value=''):
        # Format the command string and encode it to bytes
        command_str = f'{command}{value}\r\n'
        ser.write(command_str.encode('ascii'))

        # Read and print the response from the pump
        response = ser.readline().decode('ascii')
        print(f'{ser.portstr}: {response}')

    # --- UI-22 -- #
    # 'stop pump':'G1,0',
    # 'start pump': 'G1,1',
    # 'stop priming': 'G5,0',
    # 'start priming': 'G5,1',
    # 'fixed control mode': 'S2,1',
    # 'self-learning mode': 'S2,2',
    # 'flow rate': 'S3,aaaaa', #in units of μL/min
    # 'pressure limit': 'S6,aaa,bbb', #in 0.1MPa units, no decimals
    # 'errors not transmitted': 'SE,0',
    # 'errors transmitted': 'SE,1',
    # 'request pump info': 'Q1',
    # 'request pump stats': 'Q2',
    # 'request for setting values': 'Q3'

    def UI22_pump_command(self, ser, command, address='01', value=''):
        # Format the command string and encode it to bytes
        command_str = f';{address},{command},{value}\r\n'
        ser.write(command_str.encode('ascii'))

        # Read and print the response from the pump
        response = ser.readline().decode('ascii')
        print(f'{ser.portstr}: {response}')


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
    def __init__(self, host_num, port_num = None) -> None:
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
        self.client.write_coil(address=address_num, value=boolean)

class write_floats_class(PLC):
    def write_float(self, data, reg1, reg2=None):
        data = [data]
        address = 0

        for i in range(10):
            # print('-' * 5, 'Cycle ', i, '-' * 30)
            # sleep(1.0)  # why sleep

            # increment data by one
            for i, d in enumerate(data):
                data[i] = d + 1

            # write holding registers
            # print('Write:', data)
            builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
            for d in data:
                builder.add_16bit_int(int(d))
            payload = builder.build()
            self.client.write_registers(reg1, payload, skip_encode=True, unit=address)  # only reg 1?