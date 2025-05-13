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

    def set_independent_channel_control(self):
        # Enable independent channel control mode
        command = "1~1\r".encode()
        self.sp.write(command)
        sleep(0.1)
        print(self.sp.read(self.sp.in_waiting).decode())

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
        command = f"{channel}f\r".encode()
        self.sp.write(command)
        sleep(0.1)
        response = self.sp.read(self.sp.in_waiting).decode().strip()

        # Parse the response to get the flow rate value
        value = float(response)

        # Convert from μL/min to mL/min if needed (for values like 30003.0)
        if value > 100:  # Assume values over 100 are in μL/min
            value = value / 1000.0

        # Round to 2 decimal places
        return round(value, 2)

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


# Modified ReadFloatsPLC class to support callbacks
class ReadFloatsPLC(PLC):
    def __init__(self, host_num, port_num=None) -> None:
        super().__init__(host_num, port_num)
        self.reading = False
        self.data = None

    def reading_onoff(self, boolean):
        self.reading = boolean

    def read_float(self, label_or_callback, reg1, reg2=None):
        """
        Inputs in two registers. The second register is optional.

        If two registers are entered, the data is a 32-bit data, else
        one register means 16-bit.

        The label_or_callback parameter can be either:
        1. A tk.Label to update directly (for backward compatibility)
        2. A callback function that receives the value (preferred for graph integration)
        """
        while self.reading:
            try:
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

                # Update the label or call the callback
                if callable(label_or_callback):
                    # It's a callback function
                    label_or_callback(current_value)
                else:
                    # It's a label widget (for backward compatibility)
                    label_or_callback.config(text=str(current_value))

            except Exception as e:
                print(f"Error reading float: {e}")
                
            sleep(0.5)

class OneBitClass(PLC):
    def write_onoff(self, address_num, boolean):
        self.client.write_coil(address=int(address_num), value=boolean)


class WriteFloatsPLC(PLC):
    def write_float(self, reg1, value): # reg2 is automatically reg1 + 1 in the code
        try:
            builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.LITTLE)
            builder.add_32bit_float(value)
            payload = builder.to_registers()  # Converts to register values instead of raw bytes

            print(f"Writing value: {value} to registers {reg1}, {reg1+1}")

            result = self.client.write_registers(reg1, payload)

        except Exception as e:
            print(f"Exception in write_float: {e}")