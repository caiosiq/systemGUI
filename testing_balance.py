import serial

# ser = serial.Serial('COM12', baudrate=9600, timeout=1)
# ser.write(b'P\r\n')
# while True:
#     print(ser.readline().decode().strip())

# import serial
#
# # Open serial port
# ser = serial.Serial('COM12', baudrate=9600, timeout=1)
#
# print("Reading from balance... (Press Ctrl+C to stop)")
#
# try:
#     while True:
#         raw = ser.readline()
#         if raw:
#             print("RAW:", repr(raw))  # Shows unprocessed byte data
#             try:
#                 decoded = raw.decode('ascii', errors='replace').strip()
#                 print("DECODED:", decoded)
#             except Exception as e:
#                 print("Decode error:", e)
# except KeyboardInterrupt:
#     print("Stopped reading.")
# finally:
#     ser.close()

# import serial
# import time
# try:
#     ser = serial.Serial('COM12', baudrate=9600, timeout=1)
#     print("Connected to COM12")
#     time.sleep(1)
#
#     # Try triggering a read if in demand mode
#     ser.write(b'P\r\n')  # PX163 uses 'P' for print
#     time.sleep(0.5)
#
#     while ser.in_waiting:
#         print("RECEIVED:", ser.readline().decode(errors='ignore').strip())
#
#     ser.close()
# except Exception as e:
#     print("Failed to connect:", e)

import serial
import time
import re

balance_ser = serial.Serial('COM13', baudrate=9600, timeout=1)
balance_ser.write(b'P\r\n')  # Ask the balance to print
time.sleep(0.1)
lines = []
while balance_ser.in_waiting:
    line = balance_ser.readline().decode(errors='ignore').strip()
    if line:
        lines.append(line)
print(lines)
for l in lines:
    if re.search(r'\d+\s+mg', l):  # Look for something like "7710    mg"
            number_str = re.search(r'(\d+)\s+mg', l).group(1)
            mass_mg = float(number_str)
            mass_in_float = mass_mg/1000
            break
print(f'found this mass {mass_in_float}')

