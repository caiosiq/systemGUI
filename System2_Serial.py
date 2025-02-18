import serial
from pymodbus.client import ModbusTcpClient
from time import sleep
import struct
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder

# https://blog.darwin-microfluidics.com/how-to-control-the-reglo-icc-pump-using-python-and-matlab/
class Pump:
    """
    Reglo ICC Pump Control Library
    """
    def __init__(self, COM):
        self.COM = COM
        self.sp = serial.Serial(
            self.COM,
            9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
        )
        return self.sp

    def __del__(self):
        self.sp.close()

    def start_channel(self, channel):
        command = f"{channel}H\r".encode()
        self.sp.write(command)
        sleep(0.1)
        print(self.sp.read(self.sp.in_waiting).decode())

    def stop_channel(self, channel):
        command = f"{channel}I\r".encode()
        self.sp.write(command)
        sleep(0.1)
        print(self.sp.read(self.sp.in_waiting).decode())

    # Set rotation direction
    def set_direction(self, channel, direction):
        if direction == 1:
            command = f"{channel}K\r".encode()  # counter-clockwise
        else:
            command = f"{channel}J\r".encode()  # clockwise
        self.sp.write(command)
        sleep(0.1)
        print(self.sp.read(self.sp.in_waiting).decode())

    # Get rotation direction
    def get_direction(self, channel):
        command = f"{channel}xD\r".encode()
        self.sp.write(command)
        sleep(0.1)
        return self.sp.read(self.sp.in_waiting).decode()

    def set_speed(self, channel: int, speed: float) -> str:
                
        # Convert speed to required format (3 digits before decimal, 2 after)
        # Multiply by 100 to handle 2 decimal places without floating point issues
        speed_int = int(round(speed * 100))
        
        # Format as 5 digits (3 before decimal, 2 after)
        # For example: 24.00 RPM becomes "02400"
        speed_string = f"{speed_int:05d}"

        command = f"{channel}f{speed_string}\r"
        self.sp.write(command.encode())
        response = self.sp.read(self.sp.in_waiting).decode()
        sleep(0.1)
        print(response)

    def get_speed(self, channel):
        command = f"{channel}S\r".encode()
        self.sp.write(command)
        sleep(0.1)
        return self.sp.read(self.sp.in_waiting).decode()

    def set_mode(self, channel, mode):
        if mode == 0:
            command = f"{channel}L\r".encode()  # RPM mode
        elif mode == 1:
            command = f"{channel}M\r".encode()  # Flow rate mode
        else:
            command = f"{channel}G\r".encode()  # Volume (over time) mode
        self.sp.write(command)
        sleep(0.1)
        print(self.sp.read(self.sp.in_waiting).decode())

    def get_mode(self, channel):
        command = f"{channel}xM\r".encode()
        self.sp.write(command)
        sleep(0.1)
        return self.sp.read(self.sp.in_waiting).decode()

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