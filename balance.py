import serial

balance_ser = serial.Serial(port='COM9', baudrate=9600, parity=serial.PARITY_NONE, 
                    stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0.2)
print("connected to: " + balance_ser.portstr)

while True:
    balance_data = balance_ser.read(1000)
    value = balance_data.split()[1].decode('ascii').strip()

    if value.startswith('+') or value.startswith('-'):
        print('skip')
        continue
    else:
        mass_in_float = float(value.split('g')[0])
        print(mass_in_float)