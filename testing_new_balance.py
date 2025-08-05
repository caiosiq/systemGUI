import serial
import time


def parse_mass_from_line(lines: str) -> float | None:
    """
    Parses a line from the balance and returns the mass in grams as a float.
    Returns None if parsing fails.
    """
    line = lines[0]
    try:
        # Remove any unwanted characters
        line = line.strip()

        # Check if the line ends with 'g' (grams)
        if line.endswith('g'):
            line = line[:-1].strip()  # Remove the 'g' and surrounding spaces

        # Now line should be something like '+  6.4456'
        # Remove the '+' sign and extra spaces
        line = line.replace('+', '').strip()

        # Convert to float
        return float(line)

    except Exception as e:
        print(f"Could not parse line '{line}': {e}")
        return None
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
            mass = parse_mass_from_line(lines)
            print(mass)
            return lines[-1]  # Return the last valid one (most up to date)
        else:
            print("No data received.")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None

read_mass_from_balance(port="COM13", timeout=2)
