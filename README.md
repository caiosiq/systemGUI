# System Two Control GUI

This repository contains a Tkinter-based interface for controlling pumps, sensors, and other equipment in a laboratory setup. It was originally developed by a UROP student at MIT and is intended to manage real-time data acquisition and PID regulation for multiple devices.

## Repository layout

```
.
├── System2_GUI.py        # Main GUI application
├── System2_Equipment.py  # Serial/Modbus communication wrappers
├── System2_utils.py      # Graphing and synchronized data collection utilities
├── pid_control.py        # PID feedback controller used by the GUI
├── __init__.py           # Empty module placeholder
└── system2_data_*.xlsx   # Example data files produced by the GUI
```

## Overview of modules

### `System2_GUI.py`
Creates the application window and orchestrates all GUI elements. The `System2` class builds sections for pumps, temperatures, pressures, valves, stirrers and drums. Each section has Connect buttons and controls mapped to the appropriate equipment. The file also manages:

- **Pump control** – start/stop individual channels, set flow rates and poll the current speed.
- **PID control UI** – allows a separate PID loop for each pump channel through `pid_control.PIDControl`.
- **Equipment assignment** – menu to override default Modbus registers or serial ports.
- **Graph display** – embeds a `Graph` object from `System2_utils` to plot temperatures, pressures, balances and flow rates.
- **Data synchronization** – uses `DataCollector` to ensure values are logged with the same timestamp.
- **Export and clear functions** – export collected data to Excel and reset the graphs.

The script instantiates `System2` at the bottom so running `python System2_GUI.py` launches the interface.

### `System2_Equipment.py`
Provides low level wrappers around the physical equipment:

- **`Pump`** – Talks to a Reglo ICC pump over serial. Supports enabling channel control, starting/stopping channels, and querying speed.
- **`PLC`** – Base class for Modbus TCP connections. Subclasses handle reading or writing.
    - `ReadFloatsPLC` continuously polls float registers and can update a Tkinter label or call a callback.
    - `OneBitClass` writes single coil values for on/off control (valves, drums, etc.).
    - `WriteFloatsPLC` writes 32‑bit floats to Modbus registers.

### `System2_utils.py`
Holds utility classes for real-time plotting and synchronized logging.

- **`Graph`** – Manages four Matplotlib subplots for temperatures, pressures, balances and flow rates. It stores series in dictionaries, supports hiding/showing lines, setting a time window, clearing data, and exporting all data to a formatted Excel workbook.
- **`DataCollector`** – Ensures sensors update together by buffering readings and pushing them to the `Graph` at a fixed interval.

### `pid_control.py`
Implements the PID algorithm used for automatic pump regulation. The `PIDControl` class reads mass from a balance, computes the current flow rate using a sliding linear regression, and adjusts the pump speed accordingly. It runs in a background thread and provides parameters for the PID gains, integral limit and data window.

### `__init__.py`
Empty file that simply allows the directory to be imported as a module if needed.

## Dependencies
The project has no requirements file, but the modules import:

- `tkinter`
- `matplotlib`
- `numpy`, `scipy`
- `serial` (`pyserial`)
- `pymodbus`
- `openpyxl`

Install them with pip:

```bash
pip install matplotlib numpy scipy pyserial pymodbus openpyxl
```
On Linux you may also need `python3-tk` for Tkinter.

## Running the GUI
After installing the dependencies, launch the interface with:

```bash
python System2_GUI.py
```

The window provides buttons to connect to pumps and PLC devices. You can assign serial ports and Modbus registers using the **Assign Equipment** dialog. Logged data appear on the graphs in real time and can be exported to Excel through the **Export Data** button. Many actions expect actual hardware connected with the addresses defined in the `addresses` dictionary near the top of `System2_GUI.py`.

## Scope of the project
This repository focuses solely on the GUI and supporting code necessary to control laboratory equipment. It does not include firmware or low-level hardware setup. To use the software effectively you need physical pumps, temperature sensors, pressure transducers and balances matching the expected serial/Modbus addresses. Without hardware the GUI will still open but most functions will fail or show errors.

