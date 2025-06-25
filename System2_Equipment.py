from pymodbus.client import ModbusTcpClient
import struct
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder
import serial, threading, re
from time import sleep


# https://blog.darwin-microfluidics.com/how-to-control-the-reglo-icc-pump-using-python-and-matlab/
# class Pump:
#     """
#     Reglo ICC Pump Control Library
#     """
#     def __init__(self, port_number):
#         self.lock = threading.Lock()  # Add this
#         self.COM = f'COM{port_number}'
#         self.sp = serial.Serial(
#             self.COM,
#             9600,
#             parity=serial.PARITY_NONE,
#             stopbits=serial.STOPBITS_ONE,
#             bytesize=serial.EIGHTBITS,
#         )
#
#     def __del__(self):
#         self.sp.close()
#
#     def set_independent_channel_control(self):
#         # Enable independent channel control mode
#         command = "1~1\r".encode()
#         self.sp.write(command)
#         sleep(0.1)
#         print(self.sp.read(self.sp.in_waiting).decode())
#
#     def start_channel(self, channel):
#         command = f"{channel}H\r".encode()
#         self.sp.write(command)
#         sleep(0.1)
#         print(self.sp.read(self.sp.in_waiting).decode())
#
#     def stop_channel(self, channel):
#         command = f"{channel}I\r".encode()
#         self.sp.write(command)
#         sleep(0.1)
#         print(self.sp.read(self.sp.in_waiting).decode())
#
#     # Set rotation direction
#     def set_direction(self, channel, direction):
#         if direction == 1:
#             command = f"{channel}K\r".encode()  # counter-clockwise
#         else:
#             command = f"{channel}J\r".encode()  # clockwise
#         self.sp.write(command)
#         sleep(0.1)
#         print(self.sp.read(self.sp.in_waiting).decode())
#
#     # Get rotation direction
#     def get_direction(self, channel):
#         command = f"{channel}xD\r".encode()
#         self.sp.write(command)
#         sleep(0.1)
#         return self.sp.read(self.sp.in_waiting).decode()
#
#     def set_speed(self, channel: int, speed: float) -> str:
#         with self.lock:
#             self.sp.write(f"{channel}M\r".encode())
#             speed_int = int(speed * 1000)
#             speed_string = f"{speed_int:04d}-3"
#             command = f"{channel}f{speed_string}\r"
#             self.sp.write(command.encode())
#             sleep(0.1)
#             return self.sp.read(self.sp.in_waiting).decode(errors='ignore')
#
#     def get_speed(self, channel):
#         with self.lock:
#             self.sp.reset_input_buffer()
#             self.sp.write(f"{channel}f\r".encode())
#             sleep(0.1)
#             raw_response = self.sp.read(self.sp.in_waiting).decode(errors='ignore').strip()
#             lines = [line.strip() for line in raw_response.splitlines() if line.strip()]
#
#             for line in reversed(lines):
#                 try:
#                     value = float(line)
#                     if value > 100:
#                         value = value / 1000.0
#                     return round(value, 2)
#                 except ValueError:
#                     continue
#
#             raise ValueError("No response from pump")
#
#     def set_mode(self, channel, mode):
#         if mode == 0:
#             command = f"{channel}L\r".encode()  # RPM mode
#         elif mode == 1:
#             command = f"{channel}M\r".encode()  # Flow rate mode
#         else:
#             command = f"{channel}G\r".encode()  # Volume (over time) mode
#         self.sp.write(command)
#         sleep(0.1)
#         print(self.sp.read(self.sp.in_waiting).decode())
#
#     def get_mode(self, channel):
#         command = f"{channel}xM\r".encode()
#         self.sp.write(command)
#         sleep(0.1)
#         return self.sp.read(self.sp.in_waiting).decode()
class Pump:
    """
    Reglo-ICC peristaltic pump (older firmware ≤ v2.1).
    All commands are sent **ASCII + CR** (no LF) and the pump echoes
    either  ‘*’  (OK)   or   ‘#’  (error / unsupported).

    The class exposes the handful of operations used by the GUI:
        • set_independent_channel_control()
        • start_channel(ch), stop_channel(ch)
        • set_speed(ch, flow_mL_min)   – flow-rate mode, mL min-¹
        • get_speed(ch)                – returns float (mL min-¹)
    """

    BAUD = 9600

    def __init__(self, port_number: int):
        self.lock = threading.Lock()
        self.com = f"COM{port_number}"
        self.sp = serial.Serial(self.com,
                                self.BAUD,
                                parity=serial.PARITY_NONE,
                                stopbits=serial.STOPBITS_ONE,
                                bytesize=serial.EIGHTBITS,
                                timeout=0.4)          # short, non-blocking
        # Make sure echoes don’t pile up
        self.sp.reset_input_buffer()

    # ---------- low-level helpers ---------- #

    def _write(self, cmd: str) -> str:
        """
        Send a raw command **without newline handling** and return the
        immediate echo (whatever is waiting after 150 ms).
        """
        with self.lock:
            self.sp.write(cmd.encode())          # already contains '\r'
            sleep(0.15)
            return self.sp.read(self.sp.in_waiting).decode(errors="ignore")

    @staticmethod
    def _check_ack(resp: str, cmd_name="cmd"):
        if resp.strip() == "#":
            raise RuntimeError(f"Pump returned ERROR (‘#’) after {cmd_name}")

    # ---------- pump API ---------- #

    def set_independent_channel_control(self):
        # ‘~1’ enables remote / independent mode
        resp = self._write("1~1\r")
        self._check_ack(resp, "~1")

    def start_channel(self, ch: int):
        resp = self._write(f"{ch}H\r")
        self._check_ack(resp, f"{ch}H")

    def stop_channel(self, ch: int):
        resp = self._write(f"{ch}I\r")
        self._check_ack(resp, f"{ch}I")

    # direction: 0 = CW, 1 = CCW
    def set_direction(self, ch: int, direction: int):
        cmd = "K" if direction else "J"
        resp = self._write(f"{ch}{cmd}\r")
        self._check_ack(resp, f"{ch}{cmd}")

    # ---------------- flow-rate ---------------- #

    @staticmethod
    def _format_flow_string(flow_mL_min: float) -> str:
        """
        Convert 0.000 – 9.999 mL min-¹ to ‘xxxx-3’ (uL/min × 10^-3)
        10.00 – 99.99 mL min-¹  → ‘xxxx-2’, etc.
        """
        # print(f'Trying to make the flow to be equal to: {flow_mL_min}ml/min')
        # μL_min = flow_mL_min * 1000
        # # choose exponent so mantissa fits 4 digits
        # for exp in (3, 2, 1, 0):
        #     mant = int(round(μL_min / (10 ** (3 - exp))))
        #     if mant <= 9999:
        #         return f"{mant:04d}-{exp}"
        #         print(f'For flux of {μL_min} had a mant of {mant} at exp of {exp}')
        # raise ValueError("Flow out of range for Reglo ICC format")
        f=flow_mL_min
        if f == 0:
            return "0000+0"

        from math import log10, floor

        exp = int(floor(log10(abs(f))))
        mant = f / (10 ** exp)
        mant_int = int(round(mant * 1000))  # Keep 4 digits total
        if mant_int >= 10000:
            # Rounding might push us to 5 digits (e.g. 9.9995 → 10000)
            mant_int = 1000
            exp += 1

        sign = "+" if exp >= 0 else "-"
        return f"{mant_int:04d}{sign}{abs(exp)}"

    def set_speed(self, ch: int, flow_mL_min: float):
        self._check_ack(self._write(f"{ch}M\r"), f"{ch}M")
        flow_str = self._format_flow_string(flow_mL_min)
        echo = self._write(f"{ch}f{flow_str}\r").strip()
        print(f"[DEBUG] Sent flow string: {flow_str}, Echo: {echo!r}")
        if not (echo.startswith(str(int(flow_mL_min * 1000))) or echo.startswith(flow_str[:4])):
            raise RuntimeError(f"Pump did not echo flow correctly ({echo!r})")
        ack = self._write(f"{ch}H\r")
        print(f"[DEBUG] Start pump ack: {ack!r}")
        self._check_ack(ack, f"{ch}H")

    def get_speed(self, ch: int) -> float:
        """
        Query the stored flow for channel (does NOT start/stop the pump).
        Returns mL min-¹  (float, rounded 2 dp).
        """
        resp = self._write(f"{ch}f\r").strip()     # e.g. '5000E-3' or '5000-3'
        # m = re.match(r"(\d+)(?:E-| -)(\d)", resp)
        m = re.match(r"(\d+)(?:E[+-]?| -)(\d)", resp)
        if not m:
            raise RuntimeError(f"Unparsable flow echo: {resp!r}")
        mant, exp = int(m.group(1)), int(m.group(2))
        μL_min = mant * (10 ** -exp)
        return round(μL_min / 1000.0, 2)           # → mL/min

    # -------------- cleanup -------------- #

    def close(self):
        with self.lock:
            if self.sp.is_open:
                self.sp.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
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