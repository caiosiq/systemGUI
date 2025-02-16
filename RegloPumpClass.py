# import serial
# p_in = f'COM{8}'  # put in port number
# ser_in = serial.Serial(port=p_in, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
#                     bytesize=serial.EIGHTBITS, timeout=1)
# print("connected to: " + ser_in.portstr)
# p_out = f'COM{5}'  # put in port number
# ser_out = serial.Serial(port=p_out, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
#                     bytesize=serial.EIGHTBITS, timeout=1)
# print("connected to: " + ser_out.portstr)

# set flow rate
# ser_in.write('1M1300-3[CR]\r\n'.encode('ascii'))
# response = ser_out.readline().decode('ascii')
# print(f'{ser_out.portstr}: {response}')

# # turn on
# ser_in.write('1H[CR]\r\n'.encode('ascii'))
# response = ser_out.readline().decode('ascii')
# print(f'{ser_out.portstr}: {response}')
#
# # #turn off
# ser.write('1I[CR]\r\n'.encode('ascii'))
# response = ser.readline().decode('ascii')
# print(f'{ser.portstr}: {response}')

# p = f'COM{8}'  # put in port number
# ser = serial.Serial(port=p, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
#                     bytesize=serial.EIGHTBITS, timeout=1)
# print("connected to: " + ser.portstr)
#
# # turn on
# ser.write('1H[CR]\r\n'.encode('ascii'))
# response = ser.readline().decode('ascii')
# print(f'{ser.portstr}: {response}')
#
# ser.close()

# set flow rate
# ser.write('1f1300-3[CR]\r\n'.encode('ascii'))
# response = ser.readline().decode('ascii')
# print(f'{ser.portstr}: {response}')

# turn off
# ser.write('1I[CR]\r\n'.encode('ascii'))
# response = ser.readline().decode('ascii')
# print(f'{ser.portstr}: {response}')


# https://blog.darwin-microfluidics.com/how-to-control-the-reglo-icc-pump-using-python-and-matlab/
"""
------------------------------------------
Reglo ICC Peristaltic Pump Control Library
------------------------------------------
"""

import serial
import time

class RegloICC:
    def __init__(self, COM):
        self.COM = COM
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
        time.sleep(0.1)
        print(self.sp.read(self.sp.in_waiting).decode())

    def stop_channel(self, channel):
        command = f"{channel}I\r".encode()
        self.sp.write(command)
        time.sleep(0.1)
        print(self.sp.read(self.sp.in_waiting).decode())

    # Set rotation direction
    def set_direction(self, channel, direction):
        if direction == 1:
            command = f"{channel}K\r".encode()  # counter-clockwise
        else:
            command = f"{channel}J\r".encode()  # clockwise
        self.sp.write(command)
        time.sleep(0.1)
        print(self.sp.read(self.sp.in_waiting).decode())

    # Get rotation direction
    def get_direction(self, channel):
        command = f"{channel}xD\r".encode()
        self.sp.write(command)
        time.sleep(0.1)
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
        time.sleep(0.1)
        print(response)

    def get_speed(self, channel):
        command = f"{channel}S\r".encode()
        self.sp.write(command)
        time.sleep(0.1)
        return self.sp.read(self.sp.in_waiting).decode()

    def set_mode(self, channel, mode):
        if mode == 0:
            command = f"{channel}L\r".encode()  # RPM mode
        elif mode == 1:
            command = f"{channel}M\r".encode()  # Flow rate mode
        else:
            command = f"{channel}G\r".encode()  # Volume (over time) mode
        self.sp.write(command)
        time.sleep(0.1)
        print(self.sp.read(self.sp.in_waiting).decode())

    def get_mode(self, channel):
        command = f"{channel}xM\r".encode()
        self.sp.write(command)
        time.sleep(0.1)
        return self.sp.read(self.sp.in_waiting).decode()



# Usage
pump = RegloICC("COM8")
pump.start_channel(1)
pump.set_mode(1, 1)
print("initial speed:", pump.get_speed(1))
print("set speed:", pump.set_speed(1, 1234))
print("final speed:", pump.get_speed(1))

time.sleep(3)
pump.stop_channel(1)

# Delete the pump object
del pump


from pymodbus.client import ModbusTcpClient
import time


def write_onoff(address_num, boolean):
    client = ModbusTcpClient(host="169.254.83.200")
    client.write_coil(address=address_num, value=boolean)


write_onoff(8353, True)
time.sleep(1)
write_onoff(8353, False)
