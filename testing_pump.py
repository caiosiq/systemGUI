# import serial
# import time
#
# # === Configuration ===
# COM_PORT = 'COM9'  # Port to test
# BAUD_RATE = 9600  # Common default baud rate; adjust if needed
# TEST_COMMAND = b'SF005.00\r\n'  # Example: Set Flow to 5.00 (adjust depending on your pump model)
# READ_TIMEOUT = 1.0  # Timeout in seconds for reading
#
# # === Test Script ===
# try:
#     # Connect to COM9
#     ser = serial.Serial(
#         port=COM_PORT,
#         baudrate=BAUD_RATE,
#         bytesize=serial.EIGHTBITS,
#         parity=serial.PARITY_NONE,
#         stopbits=serial.STOPBITS_ONE,
#         timeout=READ_TIMEOUT
#     )
#
#     print(f"[✓] Connected to {COM_PORT}")
#
#     # Send a test command to set speed (adjust based on pump protocol!)
#     print(f"[→] Sending command: {TEST_COMMAND}")
#     ser.write(TEST_COMMAND)
#
#     # Wait a bit and try to read a response
#     time.sleep(0.5)
#     response = ser.read(100)  # Read up to 100 bytes
#     if response:
#         print(f"[←] Response from pump: {response.decode(errors='ignore')}")
#     else:
#         print("[…] No response received.")
#
#     ser.close()
#     print(f"[×] Closed connection to {COM_PORT}")
#
# except Exception as e:
#     print(f"[ERROR] Could not connect to {COM_PORT}: {e}")

# import serial, time
#
# def send_recv(cmd):
#     ser.write(f"{cmd}\r\n".encode())
#     time.sleep(1.0)
#     resp = ser.read(ser.in_waiting or 64).decode(errors='ignore')
#     print(f"[→] {cmd}")
#     print(f"[←] {resp.strip()}")
#     return resp
#
# ser = serial.Serial("COM9", baudrate=9600, timeout=1)
# time.sleep(2)  # give pump serial time to wake up
#
# # 1. Query pump head model (contains channel count)
# resp = send_recv("1?")  # Query pump head – returns a code with number of channels :contentReference[oaicite:15]{index=15}
#
# # 2. Read current speed on channel 1
# send_recv("1SS1")
#
# # 3. Set speed to 5.00 RPM on channel 1
# # send_recv("1S0105.00")
#
# # send_recv("1S15")
#
# # send_recv("1S110.00")
#
# # send_recv("1SC110.00")  # Channel 1 Current set?
#
# send_recv("1I")  # Information or status dump
# send_recv("1Q")  # Query current config
# send_recv("1ID")
# send_recv("1VR")
# # 4. Confirm speed set
# send_recv("1SS1")
#
# ser.close()
# print("[×] Closed COM9")

# import serial, time
#
# PORT = "COM9"
# BAUD = 9600
#
# def send(ser, cmd):
#     line = f"{cmd}\r\n".encode()
#     print(f"[→] {cmd}")
#     ser.write(line)
#     time.sleep(0.05)
#     reply = ser.readline().decode(errors="ignore").strip()
#     print(f"[←] {reply}")
#     return reply
#
# with serial.Serial(PORT, BAUD, timeout=1) as ser:
#     print("[✓] Connected")
#
#     # Enter remote
#     send(ser, "1ST1")          # remote ON
#     send(ser, "1ID")           # identify
#     send(ser, "1VR")           # firmware rev
#
#     # Set and read flow on channel 1
#     send(ser, "1S15.00")       # 15 ml/min
#     send(ser, "1SS1")          # read back
#
#     # Exit remote if you wish
#     # send(ser, "1ST0")
import serial, time

PORT = "COM9"            # ← change if needed
BAUD = 9600

# cmds = [
#     "\r",                  # wake-up
#     "1S0103.00\r",         # Ch1 → 3 mL/min
#     "1S0205.00\r",         # Ch2 → 5 mL/min
#     "1H\r",                # start them
#     "1SS1\r",              # query Ch1
#     "1SS2\r"               # query Ch2
# ]
# cmds = ["1ID\r", "1VR\r", "1VR?\r", "1@?\r", "1!\r"]
# with serial.Serial(PORT, BAUD, timeout=1) as ser:
#     print("Connected to", PORT)
#     for c in cmds:
#         ser.write(c.encode("ascii"))
#         time.sleep(2.0)                   # pump answers fast; small pause is enough
#         reply = ser.readline().decode().strip()
#         print(f"[→] {c.strip() or '<CR>'}")
#         print(f"[←] {reply!r}")

# import serial
#
# ser = serial.Serial('COM9', baudrate=9600, timeout=3)
# print("[✓] Listening on COM9 after power cycle...")
#
# while True:
#     line = ser.readline().decode(errors='ignore').strip()
#     if line:
#         print("[←]", line)

# import serial, time
#
# with serial.Serial("COM9", 9600, timeout=1) as sp:
#     def send(cmd):
#         print("→", cmd.strip())
#         sp.write(cmd.encode())
#         time.sleep(0.1)
#         print("←", sp.read(sp.in_waiting).decode(errors="ignore").strip() or "∅")
#
#     send("0R\r\n")        # remote
#     send("0~1\r\n")       # independent channel mode
#     send("1M\r\n")        # channel 1, flow-rate mode
#     send("1xM\r\n")  # channel 1, flow-rate mode
#     send("1f005.00\r\n")  # 5 mL/min
#     send("1f005-3\r\n")  # 5 mL/min
#
#     send("1S\r\n")        # start
#     time.sleep(1)
#     send("1f?\r\n")       # ask actual flow
#     send("1I\r\n")        # stop


# import serial, time
#
# PORT = "COM9"           # adjust
# CH   = 1                # channel
#
# def send(ser, cmd):
#     cmd = f"{cmd}\r".encode()
#     ser.write(cmd)
#     time.sleep(0.1)
#     resp = ser.read(ser.in_waiting).decode(errors="ignore").strip()
#     print(f"[→] {cmd!r}\n[←] {resp!r}")
#     return resp
#
# with serial.Serial(PORT, 9600, timeout=0.5) as ser:
#     # put pump in independent & remote mode
#     send(ser, f"{CH}~1")            # must reply '*'
#
#     # read model / FW
#     send(ser, f"{CH}@?")            # model & SN
#     send(ser, f"{CH}VR")            # firmware
#
#     # set FLOW-RATE MODE then 5 mL/min
#     send(ser, f"{CH}M")             # flow-rate mode
#     send(ser, f"{CH}f5000-3")       # 5.000 mL/min
#     send(ser, f"{CH}H")             # start
#
#     # query actual rate
#     time.sleep(1)
#     send(ser, f"{CH}f")             # e.g. '5000E-3'
#
#     # stop
#     send(ser, f"{CH}I")

"""
reglo_quicktest.py
Minimal “smoke test” for a Reglo ICC pump using the
commands in Darwin-Microfluidics blog (protocol rev 2.21).

What it does
------------
1.   Opens the selected COM port at 9600 8N1
2.   Puts the pump in remote / independent mode
3.   Queries model & firmware
4.   Switches channel to FLOW-RATE mode
5.   Sets 5.000 mL min-1
6.   Starts the channel, waits 2 s, queries the
     flow again, then stops.
"""

import serial, time, textwrap

PORT = "COM9"     # ← change to the USB-serial port you see in Device Manager
CH   = 2          # channel 1-4

def txrx(ser, body):
    cmd = f"{CH}{body}\r".encode()
    ser.write(cmd)
    time.sleep(0.12)
    reply = ser.read(ser.in_waiting).decode(errors="ignore").strip()
    print(f"[→] {cmd!r}\n[←] {reply!r}")
    return reply                    # returns '', '*', '#', '-' or data

with serial.Serial(PORT, 9600, timeout=0.5,
                   parity=serial.PARITY_NONE,
                   stopbits=serial.STOPBITS_ONE,
                   bytesize=serial.EIGHTBITS) as s:

    print(f"Opened {PORT}")
    txrx(s, "~1")                  # independent / remote  → '*'

    print("\nModel / firmware:")
    txrx(s, "@?")                  # model / SN   (may print nothing on old FW)
    txrx(s, "VR")                  # firmware rev

    # ---------- set & start 5 mL/min ----------
    print("\nSwitch to flow-rate mode & set 5.000 mL min-1")
    txrx(s, "M")                   # flow-rate mode
    txrx(s, "f5000-3")             # 5000 µL/min = 5 mL/min
    txrx(s, "H")                   # start

    time.sleep(2.0)
    rate = txrx(s, "f")            # e.g. '5000E-3'
    txrx(s, "I")                   # stop
