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
    def __init__(self, port_number):
        self.COM = f'COM{port_number}'
        self.sp = serial.Serial(
            self.COM,
            9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
        )

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
        command = f"{channel}M\r".encode()  # set flow rate mode
        self.sp.write(command)

        # Convert speed to scientific notation format (e.g., 4.5 → "0450E-3")
        speed_int = int(speed * 1000)  # Convert to integer in nL/min
        speed_string = f"{speed_int:04d}-3"  # Format as "XXXX-3"

        command = f"{channel}f{speed_string}\r" # set speed command
        self.sp.write(command.encode())
        sleep(0.1)
        print(self.sp.read(self.sp.in_waiting).decode())

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


class ReadFloatsPLC(PLC):
    def reading_onoff(self, boolean):
        self.reading = boolean

    def read_float(self, label, reg1, reg2):
        """
        Inputs in two registers. The second register is optional.

        If two registers are entered, the data is a 32-bit data, else
        one register means 16-bit.

        Returns a list of the modbus responses (likely floats). If both
        registers are inputted, the data will be a 32-bit float.
        """
        while self.reading:
            if reg2 is None:  # Single register (16-bit)
                r1 = self.client.read_holding_registers(reg1).registers[0]
                # Unpack as 16-bit value (using 'H')
                current_value = float(r1)  # Treat it as a 16-bit value
            else:  # Two registers (32-bit)
                r1 = self.client.read_holding_registers(reg1).registers[0]
                r2 = self.client.read_holding_registers(reg2).registers[0]
                # Pack two 16-bit registers as a 32-bit float
                packed = struct.pack('<HH', r1, r2)  # Combine the two 16-bit registers into a 32-bit value
                current_value = struct.unpack('f', packed)[0]  # Unpack as a float

            # Round the value to 3 decimal places
            current_value = round(current_value, 4)

            # Update the label with the value
            label.config(text=str(current_value))

            sleep(0.5)


class OneBitClass(PLC):
    def write_onoff(self, address_num, boolean):
        self.client.write_coil(address=int(address_num), value=boolean)


class WriteFloatsPLC(PLC):
    def write_float(self, reg1, value): # reg2 is automatically reg1 + 1 in the code
        try:
            print('this is the value', value)
            builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.LITTLE)
            builder.add_32bit_float(value)
            payload = builder.to_registers()  # Converts to register values instead of raw bytes

            print(f"Writing value: {value} to registers {reg1}, {reg1+1}")

            result = self.client.write_registers(reg1, payload)

        except Exception as e:
            print(f"Exception in write_float: {e}")