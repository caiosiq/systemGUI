import serial
import time

def read_mass_from_balance(port="COM13", timeout=2):
    try:
        ser = serial.Serial(
            port=port,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout
        )

        time.sleep(1)  # Wait for initialization

        ser.reset_input_buffer()  # Clear any junk in buffer

        ser.write(b'P\r\n')  # Request weight

        time.sleep(0.5)  # Wait for response

        # Read all available lines (sometimes >1)
        lines = []
        while ser.in_waiting:
            line = ser.readline().decode(errors="ignore").strip()
            if line:
                lines.append(line)

        ser.close()

        if lines:
            print("Received lines:", lines)
            return lines[-1]  # Return the last valid one (most up to date)
        else:
            print("No data received.")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None

read_mass_from_balance(port="COM13", timeout=2)
