import tkinter as tk
from tkinter import ttk

import threading
from ast import Index

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from System2_Equipment import Pump, ReadFloatsPLC, OneBitClass, WriteFloatsPLC, Balance, Peltier
from System2_utils import Graph, DataCollector
import serial
import time
import sys


class PumpControl:
    """Encapsulates all UI elements for a pump."""

    def __init__(self, connect_button):
        self.connect_button = connect_button  # Connect button
        self.channel_dict = {}  # dictionary of channel id mapped to a map of on button, off button, flow rate var
        self.isconnected = False

    def add_channel(self, channel_id, on_button, off_button, flow_var):
        self.channel_dict[channel_id] = {"on_btn": on_button, "off_btn": off_button, "flow_var": flow_var}

    def set_serial_obj(self, serial_obj):
        print('Setting pump serial object')
        self.serial_obj = serial_obj


class CrystallizerGUI:
    def __init__(self, GUI, address, name):
        self.fullgui = GUI
        self.address = address
        self.root = GUI.equipment_frame
        self.row = GUI.current_row
        self.name = name
        self.step_count = 2  # Initial number of steps
        self.entries = []
        self.repeat_entry = None
        self.rest_temp_entry = None

    def add_btn(self, btn):
        self.btn = btn

    def _on_close(self):
        # Re-enable the button and restore its appearance
        if hasattr(self, "btn") and self.btn:
            self.btn.config(state="normal", relief="raised", bg="SystemButtonFace")

        # Properly destroy the popup
        if hasattr(self, "popup"):
            self.popup.destroy()

    def render_rows(self):
        for row in range(self.step_count):
            row_entries = []
            for col in range(len(self.headers)):
                if col == 0:
                    lbl = tk.Label(self.frame, text=str(row + 1), font=("Arial", 10))
                    lbl.grid(row=row + 3, column=col)
                    row_entries.append(lbl)
                else:
                    entry = tk.Entry(self.frame)
                    entry.grid(row=row + 3, column=col)
                    row_entries.append(entry)
            self.entries.append(row_entries)

    def add_row(self):
        row = self.step_count
        row_entries = []
        for col in range(len(self.headers)):
            if col == 0:
                lbl = tk.Label(self.frame, text=str(row + 1), font=("Arial", 10))
                lbl.grid(row=row + 3, column=col)
                row_entries.append(lbl)
            else:
                entry = tk.Entry(self.frame)
                entry.grid(row=row + 3, column=col)
                row_entries.append(entry)
        self.entries.append(row_entries)
        self.step_count += 1
        self.render_functionalities()

    def remove_row(self):
        if self.step_count <= 2:
            return  # Do not allow fewer than 2 steps

        # Remove last entry widgets from GUI
        last_row_entries = self.entries.pop()
        for widget in last_row_entries:
            widget.destroy()

        self.step_count -= 1
        self.render_functionalities()  # Update UI

    def open_popup(self):
        self.create_crystallizer_ui()
        self.btn.config(state="disabled", relief="sunken", bg="#a9a9a9")

    def render_functionalities(self):

        self.button_frame.grid(row=self.step_count + 3, column=len(self.headers) - 2, columnspan=2, sticky="e",
                               pady=(5, 5))
        self.add_button.pack(side="left", padx=(0, 2))
        self.remove_button.pack(side="left")

        # Enable remove button only if more than 2 steps
        if self.step_count > 2:
            self.remove_button.config(state="normal", relief="raised", bg="#f0f0f0")
        else:
            self.remove_button.config(state="disabled", relief="sunken", bg="#dcdcdc")

        self.repeat_label.grid(row=self.step_count + 4, column=0, sticky="w", pady=(10, 0))
        self.repeat_entry.grid(row=self.step_count + 4, column=1, sticky="w", pady=(10, 0))
        self.rest_label.grid(row=self.step_count + 5, column=0, sticky="w", pady=(10, 0))
        self.rest_temp_entry.grid(row=self.step_count + 5, column=1, sticky="w", pady=(10, 0))
        self.run_button.grid(row=self.step_count + 6, column=0, columnspan=len(self.headers), pady=10)

    def create_crystallizer_ui(self):
        row = self.row
        name = self.name

        if self.fullgui.different_tabs:
            self.frame = tk.Frame(self.fullgui.notebook)
            self.frame.pack(anchor="nw", padx=15, pady=15)
            self.fullgui.notebook.add(self.frame, text=f"Crystallizer {self.name}")
        else:
            popup = tk.Toplevel(self.root)
            popup.title(f"Crystallizer {self.name}")
            self.frame = tk.Frame(popup)
            self.frame.pack(anchor="nw", padx=15, pady=15)
            # Store the popup as an instance attribute so it can be accessed later
            self.popup = popup
            # Handle window close event
            self.popup.protocol("WM_DELETE_WINDOW", self._on_close)

        tk.Label(self.frame, text=f"Crystallizer {name}", font=("Arial", 18, "underline")).grid(sticky="w", row=0,
                                                                                                column=0)
        self.init_label = tk.Label(self.frame, text="Initial Temperature", font=("Arial", 10, "bold"))
        self.init_temp_entry = tk.Entry(self.frame)
        self.init_label.grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.init_temp_entry.grid(row=1, column=1, sticky="w", pady=(10, 0))

        self.headers = [
            "Step",
            "Temperature\n(°C)",
            "Cooling/\nHeating Rate\n(°C/min)",
            "Soak Time\n(hh:mm:ss)",
            "Flow Rate 1\n(mL/min)",
            "Flow Rate 2\n(mL/min)",
            "Flow Rate 3\n(mL/min)",
            "Flow Rate 4\n(mL/min)"
        ]

        for col, text in enumerate(self.headers):
            tk.Label(self.frame, text=text, font=("Arial", 10, "bold"), justify="center").grid(row=2, column=col)

        self.render_rows()
        # Add button
        # Place + and - buttons side by side
        # Frame to hold + and - buttons
        self.button_frame = tk.Frame(self.frame)
        self.add_button = tk.Button(self.button_frame, text="+", command=self.add_row,
                                    font=("Arial", 14, "bold"), width=4)

        self.remove_button = tk.Button(self.button_frame, text="-", command=self.remove_row,
                                       font=("Arial", 14, "bold"), width=4,
                                       disabledforeground="gray", bg="#f0f0f0")

        # Repeat steps section
        self.repeat_label = tk.Label(self.frame, text="Repeat steps", font=("Arial", 10))
        self.repeat_entry = tk.Entry(self.frame, width=10)
        # Rest temperature row
        self.rest_label = tk.Label(self.frame, text="Rest Temperature", font=("Arial", 10, "bold"))
        self.rest_temp_entry = tk.Entry(self.frame)
        # Run button
        self.run_button = tk.Button(self.frame, text="Run", command=self.run_sequence, font=("Arial", 14, "bold"))
        self.render_functionalities()

    def run_sequence(self):
        steps = []

        for row_entries in self.entries:
            step_data = {}
            try:
                step_data["temperature"] = float(row_entries[1].get())
                step_data["rate"] = float(row_entries[2].get())
                step_data["soak_time"] = str(row_entries[3].get())  # Keep as string, parse later
                for i, key in enumerate(["flow1", "flow2", "flow3", "flow4"], start=4):
                    val = row_entries[i].get()
                    step_data[key] = float(val) if val.strip() != "" else None
            except ValueError as e:
                print(f"Invalid input in row {row_entries[0].cget('text')} — skipping")
                print(e)
                continue
            steps.append(step_data)
        try:
            init_temp = float(self.init_temp_entry.get())
        except (ValueError, AttributeError):
            init_temp = 25
        try:
            rest_temp = float(self.rest_temp_entry.get())
        except (ValueError, AttributeError):
            rest_temp = 25
        try:
            repeat_count = int(self.repeat_entry.get())
        except (ValueError, AttributeError):
            repeat_count = 1  # Default to 1 if not specified or invalid

        try:
            self.fullgui.crystallizer_run(self.address, steps, init_temp, rest_temp, repeat_count)
        except AttributeError as e:
            print(
                f"Error: GUI class does not implement crystallizer_run(name, steps, init_temp, rest_temp, repeat_count): {e}")


addresses = {
    # 'Pumps': [9,10],
    # 'Balances': {
    #     'Pump 1': [12, 6, 7, 8],
    # },
    'Crystallizers': {'Crystallizer 1': (0, 0), 'Crystallizer 2': (1, 1)},
    # First element is the Pump Index, second is the Peltier Index (which of the pumps and peltiers are the ones used here, starts from 0)
    'Pumps': [9],
    'Peltiers': [11],
    # 'Balances':[12,5,6,7],
    'Balances': [12, 13],
    'Temperatures': [28710, 28712, 28714],
    'Pressure Transmitters': [28750, 28752, 28754],
    'Pressure Regulators': [28770, 28772],
    'Pressure In/Outs': [8352, 8353, 8354, 8355, 8356, 8357],
    'Valves': [8358],
    'Stirrers': [28790, 28792, 28794],
    'Continuous Operation - Pressure Driven': [16387]
}


class System2:
    def __init__(self):
        # style = ttk.Style()
        # style.theme_use("clam")
        self.root = tk.Tk()
        self.root.title("System Two Control Panel")
        self.root.state('zoomed')  # Maximize window
        self.current_row = 0
        self.different_tabs = False
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        # Split the interface into equipment control and graph
        left_panel = tk.Frame(main_frame)
        left_panel.pack(side="left", fill="y", padx=10, pady=10)

        right_panel = tk.Frame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        tk.Label(left_panel, text="System Two Control", font=("Arial", 18, "bold")).pack(pady=10)

        # Create a canvas with scrollbars for equipment control
        vscrollbar = tk.Scrollbar(left_panel, orient="vertical")
        vscrollbar.pack(fill="y", side="right", expand=False)

        hscrollbar = tk.Scrollbar(left_panel, orient="horizontal")
        hscrollbar.pack(fill="x", side="bottom", expand=False)

        canvas = tk.Canvas(
            left_panel,
            bd=0,
            highlightthickness=0,
            yscrollcommand=vscrollbar.set,
            xscrollcommand=hscrollbar.set,
            width=500,  # Fixed width for equipment panel
        )
        canvas.pack(side="left", fill="both", expand=True)
        vscrollbar.config(command=canvas.yview)
        hscrollbar.config(command=canvas.xview)

        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        self.interior = tk.Frame(canvas)
        canvas.create_window(0, 0, window=self.interior, anchor="nw")

        def configure_interior(event):
            # Update the scrollbars to match the size of the inner frame.
            size = (self.interior.winfo_reqwidth(), self.interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if self.interior.winfo_reqwidth() != canvas.winfo_width():
                # Update the canvas's width to fit the inner frame.
                canvas.config(width=self.interior.winfo_reqwidth())
            if self.interior.winfo_reqheight() != canvas.winfo_height():
                # Update the canvas's width to fit the inner frame.
                canvas.config(height=self.interior.winfo_reqheight())

        self.interior.bind("<Configure>", configure_interior)

        ### BUTTONS ###
        self.buttons = {}
        ### ---EQUIPMENT--- ###

        if self.different_tabs:
            self.notebook = ttk.Notebook(self.interior)
            self.notebook.pack(fill="both", expand=True)
            self.gui_frame = tk.Frame(self.notebook)
            self.gui_frame.pack()

            # Create original equipment tab
            self.equipment_frame = tk.Frame(self.gui_frame)
            self.equipment_frame.pack()
        else:
            self.gui_frame = tk.Frame(self.interior)
            self.equipment_frame = tk.Frame(self.gui_frame)
        enter_button = tk.Button(self.equipment_frame, text="Assign and Read Data", command=self.open_assign)
        enter_button.pack(anchor="nw", padx=15, pady=15)

        ### --- PUMPS --- ###
        self.pumps_list = [f"Pump {i + 1}" for i in range(len(addresses['Pumps']))]
        self.pump_connect_vars = [False] * len(self.pumps_list)
        self.pump_port_vars = [None] * len(self.pumps_list)
        self.pump_objects = {}
        self.pump_controls = {}
        self.pump_plot_on = False
        self.create_pump_ui()

        self.pump_polling_threads = {}
        self.stop_polling_flags = {}
        self.current_row += 1
        ### --- Crystallize Control --- ###
        self.crystallizer_list = [f"Crystallizer {i + 1}" for i in range(len(addresses['Crystallizers']))]
        # Create a single section for all crystallizer buttons
        crystallizer_section = tk.LabelFrame(self.equipment_frame, text="Crystallizers",
                                             font=("Arial", 16, "underline"))
        crystallizer_section.pack(anchor="w", padx=10, pady=10)

        for i, crystallizer in enumerate(addresses['Crystallizers'].keys()):
            address_list = list(addresses['Crystallizers'][crystallizer])
            Crystallizer = CrystallizerGUI(self, address_list, i + 1)

            if self.different_tabs:
                Crystallizer.create_crystallizer_ui()
            else:
                btn = tk.Button(crystallizer_section, text=f"Open Crystallizer {i + 1}",
                                command=Crystallizer.open_popup, width=20)
                btn.pack(anchor="w", padx=10, pady=2)
                Crystallizer.add_btn(btn)

        # Maps equipment type to a dictionary that maps a specific equipment to either the current_label
        # for temp and pressure transmitters, or the current value variable for pressure regulator and stirrer
        self.equipment_data = {}

        # Maps "buttons" or "vars" to a dicitonary that equipment name to variable,
        # variable tracks if that equipment is connected (1) or not (0)
        self.connect_dictionary = {"buttons": {}, "vars": {}}

        # Maps equipment type to a dictionary that maps specific equipment number to a register value
        self.register_dictionary = {}

        self.create_temperatures_section()
        self.create_peltiers_section()
        self.create_pressure_transmitter_section()
        self.create_balance_section()
        self.create_pressure_regulator_section()
        self.create_pressure_inout_section()
        self.create_valves_section()
        self.create_stirrer_section()
        self.create_drum_section()

        if self.different_tabs:
            self.notebook.add(self.gui_frame, text="Equipment Control")
        else:
            self.equipment_frame.grid(row=0, column=0, sticky="nw")

        # Initiate Classes
        plc_host_num = "169.254.83.200"
        self.temperature_plc = ReadFloatsPLC(plc_host_num, 502)
        self.pressure_transmitter_plc = ReadFloatsPLC(plc_host_num, 502)
        self.balance_com = Balance()
        self.peltier_com = Peltier()
        self.pressure_inout_plc = OneBitClass(plc_host_num)
        self.valve_plc = OneBitClass(plc_host_num)
        self.drum_plc = OneBitClass(plc_host_num)

        self.stirrer_plc = WriteFloatsPLC(plc_host_num)
        self.pressure_regulator_plc = WriteFloatsPLC(plc_host_num)
        if not self.different_tabs:
            self.gui_frame.pack()

        # Setup for graphs
        self.setup_graphs(right_panel)

        tk.Button(self.root, text="TEST", command=self.test).place(x=10, y=10)
        self.root.bind("<KeyPress>", self.exit_shortcut)  # press escape button on keyboard to close the GUI
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def setup_graphs(self, parent_frame):
        """Create the graph UI and initialize graph objects"""
        # Create frame for graph controls
        graph_control_frame = tk.Frame(parent_frame)
        graph_control_frame.pack(fill="x", pady=10)

        # Labels
        tk.Label(graph_control_frame, text="Data Visualization", font=("Arial", 16, "bold")).pack(anchor="w")

        # Create buttons for graph control
        control_buttons_frame = tk.Frame(graph_control_frame)
        control_buttons_frame.pack(fill="x", pady=5)

        # Time window control
        tk.Label(control_buttons_frame, text="Time Window:").grid(row=0, column=0, padx=5)
        self.time_window_var = tk.StringVar(value="3000")
        time_window_entry = tk.Entry(control_buttons_frame, textvariable=self.time_window_var, width=6)
        time_window_entry.grid(row=0, column=1, padx=5)
        tk.Label(control_buttons_frame, text="seconds").grid(row=0, column=2, padx=5)
        tk.Button(control_buttons_frame, text="Set", command=self.set_time_window).grid(row=0, column=3, padx=5)

        # Export data button
        tk.Button(control_buttons_frame, text="Export Data", command=self.export_graph_data).grid(row=0, column=4,
                                                                                                  padx=20)

        # Clear data button
        tk.Button(control_buttons_frame, text="Clear All Data", command=self.clear_graph_data).grid(row=0, column=5,
                                                                                                    padx=5)

        # Start/Stop graphing
        self.graph_running = True
        self.graph_button = tk.Button(control_buttons_frame, text="Stop Graphing", bg="light coral",
                                      command=self.toggle_graphing)
        self.graph_button.grid(row=0, column=6, padx=20)

        # Create a frame for the graphs
        graph_frame = tk.Frame(parent_frame)
        graph_frame.pack(fill="both", expand=True, pady=5)

        # Configure matplotlib
        fig, self.plot_axes = plt.subplots(2, 2, figsize=(10, 8))
        self.plot_axes = self.plot_axes.flatten()

        # Convert to a tkinter widget
        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas = canvas

        # Initialize dictionaries for graph data
        self.init_graph_data()

        # Create data series selector frame
        data_selector_frame = tk.Frame(parent_frame)
        data_selector_frame.pack(fill="x", pady=5)

        # Create tabs for different types of data
        self.create_data_selector_tabs(data_selector_frame)

        # Start the graph
        self.start_graph()

        # Setup synchronized data collection
        self.setup_synchronized_data_collection()

    def init_graph_data(self):
        """Initialize dictionaries for the graph data with channel-specific entries"""
        # For each data type, create a dictionary to store the series
        # Format: {series_name: [global_switch(bool), active_status(bool), data_points(list)]}

        # Temperature data
        self.temperatures_dict = {}
        for name in self.temperatures_list:
            self.temperatures_dict[name] = [True, True, []]

        # Pressure data
        self.pressures_dict = {}
        for name in self.pressure_transmitters_list:
            self.pressures_dict[name] = [True, True, []]

        # Balance data
        self.balances_dict = {}
        for name in self.balances_list:
            self.balances_dict[name] = [True, True, []]
        # Add entries for each pump channel
        for pump_name in self.pumps_list:
            for channel in range(1, 5):  # 4 channels per pump
                channel_name = f"{pump_name}_Ch{channel}"
                self.balances_dict[channel_name] = [True, True, []]

        # Flow rate data - per channel
        self.flow_rates_dict = {}
        for pump_name in self.pumps_list:
            for channel in range(1, 5):  # 4 channels per pump
                channel_name = f"{pump_name}_Ch{channel}"
                self.flow_rates_dict[channel_name] = [True, True, []]

        # Create the graph object
        self.graph = Graph(
            self.temperatures_dict,
            self.pressures_dict,
            self.balances_dict,
            self.flow_rates_dict,
            max_points=6000,  # Store up to 1000 data points per series
            update_interval=0.5  # Update every 0.5 seconds
        )

    def create_data_selector_tabs(self, parent_frame):
        """Create tabs for selecting which data series to display"""
        # Create notebook for tabs
        notebook = tk.Frame(parent_frame)
        notebook.pack(fill="x")

        # Create tab buttons
        tab_frame = tk.Frame(notebook)
        tab_frame.pack(fill="x")

        self.tab_buttons = []
        self.tab_frames = []

        tab_names = ["Temperatures", "Pressures", "Balances", "Flow_Rates"]

        for i, name in enumerate(tab_names):
            button = tk.Button(tab_frame, text=name,
                               command=lambda idx=i: self.switch_tab(idx))
            button.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            self.tab_buttons.append(button)

        # Create content frames for each tab
        self.tab_content_frame = tk.Frame(notebook)
        self.tab_content_frame.pack(fill="x", expand=True)

        # Create content for temperature tab
        temp_frame = tk.Frame(self.tab_content_frame)
        self.create_series_selectors(temp_frame, "Temperatures", self.temperatures_list)
        self.tab_frames.append(temp_frame)

        # Create content for pressure tab
        pressure_frame = tk.Frame(self.tab_content_frame)
        self.create_series_selectors(pressure_frame, "Pressures", self.pressure_transmitters_list)
        self.tab_frames.append(pressure_frame)

        # Create content for balance tab - using pump names as balance identifiers
        balance_frame = tk.Frame(self.tab_content_frame)
        self.create_series_selectors(balance_frame, "Balances", self.balances_list)
        self.tab_frames.append(balance_frame)

        # Create content for flow rate tab
        flow_frame = tk.Frame(self.tab_content_frame)
        self.create_series_selectors(flow_frame, "Flow_Rates", self.pumps_list)
        self.tab_frames.append(flow_frame)

        # Show first tab by default
        self.switch_tab(0)

    def switch_tab(self, tab_index):
        """Switch between data selector tabs"""
        for i, button in enumerate(self.tab_buttons):
            if i == tab_index:
                button.config(relief="sunken", bg="light blue")
            else:
                button.config(relief="raised", bg="SystemButtonFace")

        for i, frame in enumerate(self.tab_frames):
            if i == tab_index:
                frame.pack(fill="x", expand=True)
            else:
                frame.pack_forget()

    def create_series_selectors(self, parent_frame, data_type, series_list):
        """
        Create checkboxes for each data series that directly control visibility.
        For flow_rates and balances, expand the series list to include all channels
        """
        # Dict to store checkbox variables
        if not hasattr(self, 'checkbox_vars'):
            self.checkbox_vars = {}

        # Add a 'select all' button
        all_button = tk.Button(parent_frame, text=f"Select All {data_type}",
                               command=lambda: self.toggle_all_series(data_type.lower(), True))
        all_button.pack(side="left", padx=5, pady=5)

        # Add a 'deselect all' button
        none_button = tk.Button(parent_frame, text=f"Deselect All {data_type}",
                                command=lambda: self.toggle_all_series(data_type.lower(), False))
        none_button.pack(side="left", padx=5, pady=5)

        # Create a frame for the checkboxes
        checkbox_frame = tk.Frame(parent_frame)
        checkbox_frame.pack(fill="x", padx=5, pady=5)

        expanded_series_list = series_list
        # For flow rates and balances, expand to include all channels
        if data_type.lower() in ["flow_rates"]:
            expanded_series_list = []
            for name in series_list:
                # Create a frame for each pump's channels to keep them on one row
                pump_frame = tk.Frame(checkbox_frame)
                pump_frame.pack(anchor="w", pady=2)

                # Add pump label
                tk.Label(pump_frame, text=f"{name}:", width=8, anchor="w").pack(side="left", padx=(0, 5))

                for channel in range(1, 5):  # 4 channels
                    # Fix: Use consistent naming format with underscores
                    channel_name = f"{name}_Ch{channel}"
                    expanded_series_list.append(channel_name)

                    # Get the dictionary for this data type
                    data_dict = getattr(self.graph, f"{data_type.lower()}_dict")

                    # Initialize checkbox variable based on current series visibility
                    is_visible = data_dict[channel_name][1] if channel_name in data_dict else True

                    # Create variable and store it
                    var = tk.BooleanVar(value=is_visible)
                    self.checkbox_vars[f"{data_type.lower()}_{channel_name}"] = var

                    # Create the checkbox with a command that updates visibility - pack them side by side
                    cb = tk.Checkbutton(
                        pump_frame,
                        text=f"Ch{channel}",
                        variable=var,
                        command=lambda n=channel_name, t=data_type.lower(), v=var: self.update_series_visibility(t, n,
                                                                                                                 v.get())
                    )
                    cb.pack(side="left", padx=5)
        else:
            # For temperatures and pressures - use the original grid layout
            print(f'Setting checkbox for {data_type}')
            for i, name in enumerate(expanded_series_list):
                # Get the dictionary for this data type
                data_dict = getattr(self.graph, f"{data_type.lower()}_dict")

                # Initialize checkbox variable based on current series visibility
                is_visible = data_dict[name][1] if name in data_dict else True

                # Create variable and store it
                var = tk.BooleanVar(value=is_visible)
                self.checkbox_vars[f"{data_type.lower()}_{name}"] = var

                # Create the checkbox with a command that updates visibility
                cb = tk.Checkbutton(
                    checkbox_frame,
                    text=name,
                    variable=var,
                    command=lambda n=name, t=data_type.lower(), v=var: self.update_series_visibility(t, n, v.get())
                )
                cb.grid(row=i // 3, column=i % 3, sticky="w", padx=10, pady=3)

    def update_series_visibility(self, data_type, series_name, is_visible):
        """
        Update the visibility of a data series based on checkbox state.

        Args:
            data_type: Type of data (temperature, pressure, etc.)
            series_name: Name of the data series
            is_visible: Boolean indicating if series should be visible
        """
        # Get the dictionary for this data type
        data_dict = getattr(self.graph, f"{data_type}_dict")

        if series_name in data_dict:
            # If the current visibility state is different from the desired state
            if data_dict[series_name][1] != is_visible:
                # When turning off, add a discontinuity marker
                if not is_visible:
                    data_dict[series_name][2].append((None, None))

                # Update the visibility state
                data_dict[series_name][1] = is_visible

    def toggle_all_series(self, data_type, visible):
        """
        Set all series of a specific type to visible or invisible.

        Args:
            data_type: Type of data (temperature, pressure, etc.)
            visible: Boolean indicating if series should be visible
        """
        # Get the dictionary for this data type
        data_dict = getattr(self.graph, f"{data_type}_dict")

        # Update all series in this dictionary
        for name in data_dict:
            # Update the checkboxes
            checkbox_key = f"{data_type}_{name}"
            if checkbox_key in self.checkbox_vars:
                self.checkbox_vars[checkbox_key].set(visible)

            # Update the data visibility directly
            if data_dict[name][1] != visible and not visible:
                # Add discontinuity marker if hiding
                data_dict[name][2].append((None, None))

            # Set visibility
            data_dict[name][1] = visible

    def start_graph(self):
        """Start the graph plotting thread"""
        self.graph_thread = threading.Thread(
            target=self.graph.plot,
            args=(self.plot_axes, self.canvas, plt.gcf())
        )
        self.graph_thread.daemon = True
        self.graph_thread.start()

    def toggle_graphing(self):
        """Toggle the graph plotting on/off"""
        self.graph_running = not self.graph_running

        if self.graph_running:
            self.graph.stop_plotting(False)
            self.graph_button.config(text="Stop Graphing", bg="light coral")
            # Restart the thread if it's stopped
            if not self.graph_thread.is_alive():
                self.start_graph()
        else:
            self.graph.stop_plotting(True)
            self.graph_button.config(text="Start Graphing", bg="pale green")

    def set_time_window(self):
        """Set the time window for the graph"""
        try:
            time_window = int(self.time_window_var.get())
            if time_window > 0:
                self.graph.set_time_window(time_window)
        except ValueError:
            # Handle invalid input
            self.time_window_var.set("120")  # Reset to default

    def export_graph_data(self):
        """Export graph data to excel"""
        filename = self.graph.export_data()
        tk.messagebox.showinfo("Data Exported", f"Data exported to {filename}")

    def clear_graph_data(self):
        """Clear all graph data"""
        if tk.messagebox.askyesno("Clear Data", "Are you sure you want to clear all graph data?"):
            self.graph.clear_data()

    # crystalizer
    def crystallizer_run(self, index_list, steps, init_temp, rest_temp, repeat_count):
        print('Crystallizer run')
        print(f'Index list: {index_list}')
        print(f'Steps: {steps}')

        def parse_duration(duration_str):
            """Converts hh:mm:ss string into total seconds"""
            h, m, s = map(int, duration_str.split(":"))
            return h * 3600 + m * 60 + s

        def generate_pump_sequence(steps):
            """
            Returns a list of actions like:
            [{'duration':50, 'flow1': 0.5, 'flow2': 0.5, 'flow3': 0.5, 'flow4': 0.5}, {'duration':70, 'flow1': 0.5, 'flow2': 0.5, 'flow3': 0.5, 'flow4': 0.5}]
            """
            print(steps)
            sequence = []
            if not steps:
                return sequence

            current_temp = init_temp
            for i in range(len(steps)):
                prev_temp = current_temp
                current_temp = steps[i]['temperature']

                # GET RAMP TIME
                rate = steps[i]['rate']
                ramp_time = int(round(60 * abs(current_temp - prev_temp) / rate))

                # GET SOAK TIME
                soak_time = steps[i].get('soak_time', None)
                soak_time = parse_duration(soak_time)

                total_duration = soak_time + ramp_time
                sequence.append({'duration': total_duration, 'flow1': steps[i]['flow1'], 'flow2': steps[i]['flow2'],
                                 'flow3': steps[i]['flow3'], 'flow4': steps[i]['flow4']})
            return sequence

        def generate_peltier_sequence(steps):
            """
            Returns a list of actions like:
            [{'mode': 'ramp', 'target': 45.0, 'rate': 0.5}, {'mode': 'soak', 'duration': 7200}]
            """
            print(steps)
            sequence = []
            if not steps:
                return sequence

            current_temp = init_temp
            for i in range(len(steps)):
                prev_temp = current_temp
                current_temp = steps[i]['temperature']

                # GET RAMP TIME
                rate = steps[i]['rate']
                ramp_time = int(round(60 * abs(current_temp - prev_temp) / rate))

                # GET SOAK TIME
                soak_time = steps[i].get('soak_time', None)
                soak_time = parse_duration(soak_time)
                sequence.append({'temp': current_temp, 'ramp_time': ramp_time, 'soak_time': soak_time})
            return sequence

        pump_index = index_list[0]
        peltier_index = index_list[1]

        pump_sequence = generate_pump_sequence(steps)
        peltier_sequence = generate_peltier_sequence(steps)

        peltier_address = addresses['Peltiers'][peltier_index]
        self.peltier_com.send_peltier_sequence(peltier_address, peltier_sequence, init_temp, repeat_count, rest_temp)

        print('setting the following sequence on pump:', pump_sequence)
        self.pump_connect(pump_index)
        self.pump_set_sequence(pump_index, pump_sequence)

    # pumps
    def start_flow_polling(self, channel_name, pump_ser, channel):
        if channel_name in self.pump_polling_threads:
            return

        stop_flag = threading.Event()
        self.stop_polling_flags[channel_name] = stop_flag

        def poll():
            while not stop_flag.is_set():
                try:
                    value = pump_ser.get_speed(channel)
                    self.graph.update_dict("flow_rates", channel_name, value)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Polling error on {channel_name}: {e}")
                    break

        t = threading.Thread(target=poll)
        t.daemon = True
        self.pump_polling_threads[channel_name] = t
        t.start()

    def create_pump_ui(self):
        """Creates UI elements for pumps with the updated PumpControl class structure."""
        frame = tk.Frame(self.equipment_frame)
        tk.Label(frame, text="Pumps", font=("Arial", 16, "underline")).grid(sticky="w", row=0, column=0)

        # Updated headers (removed "On" and "Off")
        headers = ["Connect", "Channel Number", "Flow Rates", "Set Flow Rates"]
        for col, text in enumerate(headers, start=1):
            tk.Label(frame, text=text, font=("Arial", 12, "bold")).grid(row=1, column=col)

        row_index = 2

        for i, pump_name in enumerate(self.pumps_list):
            # Add pump label for whole pump
            tk.Label(frame, text=pump_name, font=("Arial", 11, "bold")).grid(
                row=row_index, column=0, sticky="w", rowspan=4)

            # Create a connect button for the whole pump
            connect_btn = tk.Button(
                frame, text="Connect", width=12,
                command=lambda i=i: self.pump_connect(i))
            connect_btn.grid(row=row_index, column=1, padx=10, rowspan=4)
            self.buttons[('pumps', i)] = connect_btn
            # Create a PumpControl object for this pump
            pump_control = PumpControl(connect_btn)
            self.pump_objects[i] = pump_control

            # Create controls for each channel
            for j in range(4):
                channel_num = j + 1
                channel_id = f"{i}_{j}"  # Unique ID for each channel

                # Channel label
                channel_label = tk.Label(frame, text=f"{channel_num}")
                channel_label.grid(row=row_index + j, column=2, padx=10)

                # Flow rate entry and set button
                flow_var = tk.StringVar()
                flow_entry = tk.Entry(frame, textvariable=flow_var, width=15)
                flow_entry.grid(row=row_index + j, column=3, padx=10)

                set_flow_btn = tk.Button(
                    frame, text="Set", width=5,
                    command=lambda i=i, ch=channel_num, v=flow_var: self.pump_set_flow_rate(i, ch, v))
                set_flow_btn.grid(row=row_index + j, column=4)

                # Add this channel to the pump control object
                # Pass None for on/off buttons since they are removed
                pump_control.add_channel(channel_id, None, None, flow_var)

            row_index += 4

            # Update separator columnspan (was 7, now 5)
            if i < len(self.pumps_list) - 1:
                separator = tk.Frame(frame, height=2, bd=1, relief=tk.SUNKEN)
                separator.grid(row=row_index, column=0, columnspan=5, sticky="ew", pady=5)
                row_index += 1

        frame.pack(anchor="nw", padx=15, pady=15)

    def pump_connect(self, pump_index):
        """Handles connecting/disconnecting a pump."""
        # if not self.pump_connect_vars[pump_index]:  # If not connected
        connect_btn = self.buttons[('pumps', pump_index)]
        if connect_btn:
            connect_btn.config(state="disabled", relief="sunken", bg="#a9a9a9")
        if not self.pump_port_vars[pump_index]:
            address = addresses["Pumps"][pump_index]
            self.pump_port_vars[pump_index] = tk.IntVar(value=address)
        else:
            return None

        try:
            # Get the port number from the pump port variable
            com_number = str(self.pump_port_vars[pump_index].get())

            # Create pump serial object
            pump_ser = Pump(com_number)
            pump_ser.set_independent_channel_control()
            print(f'Connecting pump {pump_index} on COM{com_number}')

            # Update connection state
            self.pump_connect_vars[pump_index] = True

            # Get the PumpControl object
            pump_control = self.pump_objects[pump_index]

            # Set the serial object
            pump_control.set_serial_obj(pump_ser)

        except Exception as e:
            print(f"Error connecting pump: {e}")
            tk.messagebox.showerror("Connection Error", f"Failed to connect pump: {e}")

        # else:  # If already connected
        #     try:
        #         # Update connection state
        #         self.pump_connect_vars[pump_index] = False
        #
        #         # Get the PumpControl object
        #         pump_control = self.pump_objects[pump_index]
        #
        #         # Clean up serial connection
        #         if hasattr(pump_control, 'serial_obj'):
        #             delattr(pump_control, 'serial_obj')
        #
        #     except Exception as e:
        #         print(f"Error disconnecting pump: {e}")

    def pump_on(self, pump_index, channel):
        if not self.pump_connect_vars[pump_index]:
            return

        try:
            pump_control = self.pump_objects[pump_index]
            channel_id = f"{pump_index}_{channel - 1}"
            channel_controls = pump_control.channel_dict.get(channel_id)

            if not channel_controls:
                print(f"Channel controls not found for channel {channel}")
                return

            pump_control.serial_obj.start_channel(channel)

            # Start flow polling
            channel_name = f"{self.pumps_list[pump_index]}_Ch{channel}"
            self.start_flow_polling(channel_name, pump_control.serial_obj, channel)

        except Exception as e:
            print(f"Error turning on pump channel: {e}")

    def pump_off(self, pump_index, channel):
        """Turns off the specified pump channel if connected."""
        if not self.pump_connect_vars[pump_index]:
            return  # Ignore if pump is not connected

        try:
            # Get the PumpControl object
            pump_control = self.pump_objects[pump_index]

            # Find the channel controls
            channel_id = f"{pump_index}_{channel - 1}"  # Convert 1-based channel to 0-based index
            channel_controls = pump_control.channel_dict.get(channel_id)

            if not channel_controls:
                print(f"Channel controls not found for channel {channel}")
                return

            # Turn off the channel
            pump_control.serial_obj.stop_channel(channel)

            self.pump_plot_on = False

        except Exception as e:
            print(f"Error turning off pump channel: {e}")

    def pump_set_flow_rate(self, pump_index, channel, flow_var=None, flow_rate=None):
        if not self.pump_connect_vars[pump_index]:
            return
        # pump_control = self.pump_objects[pump_index]
        # flow_rate = float(flow_var.get())
        # pump_control.serial_obj.set_speed(channel, flow_rate)
        #
        # channel_name = f"{self.pumps_list[pump_index]}_Ch{channel}"
        #
        # # Start polling pump output
        # self.start_flow_polling(channel_name, pump_control.serial_obj, channel)

        try:
            pump_control = self.pump_objects[pump_index]
            if flow_rate is None:
                flow_rate = float(flow_var.get())
            pump_control.serial_obj.set_speed(channel, flow_rate)

            channel_name = f"{self.pumps_list[pump_index]}_Ch{channel}"

            # Start polling pump output
            self.start_flow_polling(channel_name, pump_control.serial_obj, channel)


        except ValueError:
            tk.messagebox.showerror("Error", "Please enter a valid flow rate")
        except Exception as e:
            print(f"Error setting flow rate: {e}")

    def pump_set_sequence(self, pump_index, sequence):
        def run_sequence():
            if not self.pump_connect_vars[pump_index]:
                print("Pump is not connected")
                return

            pump_control = self.pump_objects[pump_index]

            for step in sequence:
                try:
                    for ch in range(1, 5):  # channels 1–4
                        flow_key = f"flow{ch}"
                        flow_rate = step.get(flow_key, 0.0)
                        self.pump_set_flow_rate(pump_index, ch, flow_rate=flow_rate)

                    print(f"Set flow for pump {pump_index}, waiting {step['duration']}s")
                    time.sleep(step['duration'])

                except Exception as e:
                    print(f"Error in sequence step: {e}, 'step': {step},'sequence': {sequence}")
                    break

        threading.Thread(target=run_sequence, daemon=True).start()

    def update_flow_rate_graph(self, channel_name, flow_rate):
        while self.pump_plot_on:
            # Update the flow rate in the graph
            self.graph.update_dict("flow_rates", channel_name, flow_rate)
            time.sleep(0.5)

    # other
    def create_equipment_section(self, title, items, connect_command, display_current=False, entry=False,
                                 onoff_buttons=False, peltier=False):
        start = self.current_row
        frame = tk.Frame(self.equipment_frame)
        tk.Label(self.equipment_frame, text=title, font=("Arial", 16, "underline")).pack(anchor="nw", padx=15,
                                                                                         pady=(10, 0))
        if display_current or entry:
            self.equipment_data[title] = {}
            if peltier:
                self.equipment_data['Peltiers Temperature'] = {}

        self.register_dictionary[title] = {}
        if peltier:
            self.register_dictionary['Peltiers Temperature'] = {}

        for i, name in enumerate(items):

            tk.Label(frame, text=name).grid(row=i + start, column=0, sticky="w", pady=5)
            if display_current:  # Temperatures and pressure trasmitters // read float class
                current_label = tk.Label(frame, text='', bg="white", borderwidth=1, relief="raised", width=10)
                current_label.grid(row=i + start, column=1, padx=15)

                if title == 'Temperatures' and peltier and i >= len(addresses['Temperatures']):
                    self.equipment_data['Peltiers Temperature'][name] = current_label
                    address = addresses['Peltiers'][i - len(addresses['Temperatures'])]
                    self.register_dictionary['Peltiers Temperature'][name] = tk.IntVar(value=address)
                else:
                    self.equipment_data[title][name] = current_label
                    address = addresses[title][i]
                    self.register_dictionary[title][name] = tk.IntVar(value=address)

                # connnect button for these two equipments
                connect_button = tk.Button(frame, text="Connect", font=("Arial", 12, "bold"), width=12,
                                           command=connect_command)
                connect_button.grid(row=0, column=0)
                self.connect_dictionary["buttons"][title] = connect_button

            if entry:  # Pressure regulators and stirrers
                var = tk.StringVar(value="0")
                entry_field = tk.Entry(frame, textvariable=var)
                entry_field.grid(row=i + start, column=1, padx=15, pady=5)
                self.equipment_data[title][name] = var
                (tk.Button(frame, text="Enter",
                           command=lambda t=title, n=name, v=var: self.write_float_values(t, n, float(v.get()))
                           ).grid(row=i + start, column=2)
                 )
                address = addresses[title][i]
                self.register_dictionary[title][name] = tk.IntVar(value=address)

            if onoff_buttons:  # Pressure in/outs and valves
                on_btn = tk.Button(frame, text="On", width=10)
                off_btn = tk.Button(frame, text="Off", width=10)
                on_btn.config(relief=tk.RAISED, state=tk.NORMAL)
                off_btn.config(relief=tk.RAISED, state=tk.NORMAL)
                # Define command after both buttons exist
                on_btn.config(
                    command=lambda t=title, n=name, on_btn=on_btn, off_btn=off_btn: self.toggle_onoff(t, n, True,
                                                                                                      on_btn, off_btn))
                off_btn.config(
                    command=lambda t=title, n=name, on_btn=on_btn, off_btn=off_btn: self.toggle_onoff(t, n, False,
                                                                                                      on_btn, off_btn))

                on_btn.grid(row=i + start, column=1, padx=15)
                off_btn.grid(row=i + start, column=2, padx=15)
                address = addresses[title][i]
                self.register_dictionary[title][name] = tk.IntVar(value=address)

        frame.pack(anchor="nw", padx=15)

    def create_peltiers_section(self):
        self.peltiers_list = [f"Peltier {i + 1}" for i in range(len(addresses['Peltiers']))]
        self.create_equipment_section("Peltiers", self.peltiers_list, self.peltier_connect, entry=True)

    def create_temperatures_section(self):
        self.temperatures_list = [f"Reactant Temperature {i + 1}" for i in range(len(addresses['Temperatures']))] + [
            f'Peltier Temperature {i + 1}' for i in range(len(addresses['Peltiers']))]
        self.create_equipment_section("Temperatures", self.temperatures_list, self.temperature_connect,
                                      display_current=True, peltier=True)

    def create_pressure_transmitter_section(self):
        self.pressure_transmitters_list = ["Pressure Transmitter 1", "Pressure Transmitter 2", "Pressure Transmitter 3"]
        self.create_equipment_section("Pressure Transmitters", self.pressure_transmitters_list,
                                      self.pressure_transmitter_connect, display_current=True)

    def create_balance_section(self):
        self.balances_list = [f"Balance {i + 1}" for i in range(len(addresses['Balances']))]
        self.create_equipment_section("Balances", self.balances_list,
                                      self.balance_connect, display_current=True)

    def create_pressure_regulator_section(self):
        self.pressure_regulators_list = ["Pressure Regulator 1", "Pressure Regulator 2"]
        self.create_equipment_section("Pressure Regulators", self.pressure_regulators_list,
                                      self.pressure_regulator_connect, entry=True)

    def create_pressure_inout_section(self):
        self.pressure_inouts_list = ["Pressure 1 In", "Pressure 1 Out", "Pressure 2 In", "Pressure 2 Out",
                                     "Pressure 3 In", "Pressure 3 Out"]
        self.create_equipment_section("Pressure In/Outs", self.pressure_inouts_list, self.pressure_inout_connect,
                                      onoff_buttons=True)

    def create_valves_section(self):
        self.valves_list = ["Valve 1"]
        self.create_equipment_section("Valves", self.valves_list, self.valve_connect, onoff_buttons=True)

    def create_stirrer_section(self):
        self.stirrers_list = ["10mL Stirrer", "5mL Stirrer", "40mL Stirrer"]
        self.create_equipment_section("Stirrers", self.stirrers_list, self.stirrer_connect, entry=True)

    def create_drum_section(self):
        self.drums_list = ["Pressure Driven 1"]
        self.create_equipment_section("Continuous Operation - Pressure Driven", self.drums_list, self.drum_connect,
                                      onoff_buttons=True)

    def toggle_connection(self, device_name, plc, read_float=False, plc_object=None, data_type=None,
                          peltier_object=None):
        """
        Generic method to handle connection toggling for various devices.
        :param device_name: String name of the device for debugging purposes.
        :param connect_var: Tkinter IntVar tracking connection state.
        :param connect_button: Tkinter Button to update UI.
        :param plc: The PLC object handling the device connection.
        :param read_float: Boolean indicating whether to read float values.
        :param read_type: String type of data to read if read_float is True.
        """
        connect_button = self.connect_dictionary["buttons"][device_name]
        connect_button.config(state="disabled", relief="sunken", bg="#a9a9a9")
        peltier = False
        if peltier_object:
            peltier = True
            for address in addresses['Peltiers']:
                peltier_object.reading_onoff(address)
                self.read_peltier_float_values(peltier_object, 'Peltiers Temperature', address)

        plc.connect()
        if read_float:
            plc.reading_onoff(True)
            self.read_float_values(plc_object, data_type, peltier=peltier)

    def toggle_balance_connection(self, device_name, balance, read_float=False, data_type=None):
        """
        Method to handle connection to balance.
        Needs to be different from other methods since it requires a COM connection instead of plc
        """
        connect_button = self.connect_dictionary["buttons"][device_name]
        connect_button.config(state="disabled", relief="sunken", bg="#a9a9a9")

        balance.connect()
        if read_float:
            balance.reading_onoff(True)
            self.read_balance_float_values(balance, data_type)

    def toggle_peltier_connection(self, device_name, peltier):
        """
        Method to handle connection to balance.
        Needs to be different from other methods since it requires a COM connection instead of plc
        """
        connect_peltier = self.connect_dictionary["peltiers"][device_name]
        connect_peltier.config(state="disabled", relief="sunken", bg="#a9a9a9")
        peltier.connect()

    def temperature_connect(self):
        self.toggle_connection("Temperatures", self.temperature_plc, read_float=True,
                               plc_object=self.temperature_plc, data_type="Temperatures",
                               peltier_object=self.peltier_com)

    def peltier_connect(self):
        self.toggle_peltier_connection("Peltiers", self.peltier_com)

    def pressure_transmitter_connect(self):
        self.toggle_connection("Pressure Transmitters", self.pressure_transmitter_plc,
                               read_float=True, plc_object=self.pressure_transmitter_plc,
                               data_type="Pressure Transmitters")

    def balance_connect(self):
        print('HERE IS WHAT THE BUTTON FOR BALANCE STARTS: Trying to connect to balance')
        self.toggle_balance_connection("Balances", self.balance_com,
                                       read_float=True,
                                       data_type="Balances")

    def valve_connect(self):
        self.toggle_connection("Valves", self.valve_plc)

    def pressure_inout_connect(self):
        self.toggle_connection("Pressure In/Outs", self.pressure_inout_plc)

    def pressure_regulator_connect(self):
        self.toggle_connection("Pressure Regulators", self.pressure_regulator_plc)

    def stirrer_connect(self):
        self.toggle_connection("Stirrers", self.stirrer_plc)

    def drum_connect(self):
        self.toggle_connection("Continuous Operation - Pressure Driven", self.drum_plc)

    def create_assignment_section(self, title, headers, items):
        frame = tk.Frame(self.scrollable_frame)
        tk.Label(frame, text=title, font=("Arial", 12, "bold")).pack(pady=5)

        table_frame = tk.Frame(frame)
        for col, header in enumerate(headers):
            tk.Label(table_frame, text=header, font=("TkDefaultFont", 9, "underline")).grid(row=0, column=col, padx=5)

        for i, item in enumerate(items):
            tk.Label(table_frame, text=item).grid(row=i + 1, column=0, padx=5)

            # for j, var in enumerate(self.register_dictionary[title]):
            entry = tk.Entry(table_frame, textvariable=self.register_dictionary[title][item])
            entry.grid(row=i + 1, column=1, padx=5)

        table_frame.pack()
        frame.pack(pady=10)

    def open_assign(self):
        self.assign_page = tk.Toplevel(self.root)
        self.assign_page.title("Assign Equipment")

        # Create a canvas with scrollbars
        canvas = tk.Canvas(self.assign_page)
        scrollbar_y = tk.Scrollbar(self.assign_page, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set)

        tk.Label(self.scrollable_frame, text="Assign Equipment", font=("Arial", 14, "bold")).pack(pady=10)

        # --- Pump and Balance Section ---
        tk.Label(self.scrollable_frame, text="Assign Pump Types and Balance Ports", font=("Arial", 12, "bold")).pack(
            pady=5)
        pump_balance_frame = tk.Frame(self.scrollable_frame)

        # Column headers
        tk.Label(pump_balance_frame, text="Pump Name", font=("TkDefaultFont", 9, "underline")).grid(row=0, column=0)
        tk.Label(pump_balance_frame, text="Pump Port", font=("TkDefaultFont", 9, "underline")).grid(row=0, column=1)
        tk.Label(pump_balance_frame, text="Ch1 Balance", font=("TkDefaultFont", 9, "underline")).grid(row=0, column=2)
        tk.Label(pump_balance_frame, text="Ch2 Balance", font=("TkDefaultFont", 9, "underline")).grid(row=0, column=3)
        tk.Label(pump_balance_frame, text="Ch3 Balance", font=("TkDefaultFont", 9, "underline")).grid(row=0, column=4)
        tk.Label(pump_balance_frame, text="Ch4 Balance", font=("TkDefaultFont", 9, "underline")).grid(row=0, column=5)

        # Initialize balance port variables for each pump channel
        self.balance_port_vars = {}
        for pump_name in self.pumps_list:
            self.balance_port_vars[pump_name] = {}
            for channel in range(1, 5):
                # Get default port from addresses if available
                default_port = 5  # Default fallback
                if pump_name in addresses["Balances"]:
                    default_port = addresses["Balances"][pump_name][channel - 1]

                self.balance_port_vars[pump_name][channel] = tk.StringVar(value=str(default_port))

        # Row for each pump
        for i, pump_name in enumerate(self.pumps_list):
            # Pump name
            tk.Label(pump_balance_frame, text=pump_name).grid(row=i + 1, column=0, padx=5)

            # Pump port entry
            address = addresses["Pumps"][i]
            self.pump_port_var = tk.IntVar(value=address)
            if self.pump_port_vars[i]:
                self.pump_port_var.set(self.pump_port_vars[i].get())
            pump_port_entry = tk.Entry(pump_balance_frame, textvariable=self.pump_port_var)
            pump_port_entry.grid(row=i + 1, column=1, padx=5)
            self.pump_port_vars[i] = self.pump_port_var

            # Initialize balance port dictionary for this pump if not exists
            if pump_name not in self.balance_port_vars:
                self.balance_port_vars[pump_name] = {}

            # Balance port entries for each channel
            for channel in range(1, 5):  # Channels 1-4
                channel_name = f"{pump_name}_Ch{channel}"

                # Get default value from addresses
                default_port = addresses["Balances"][pump_name][channel - 1] if pump_name in addresses[
                    "Balances"] else 5

                if channel not in self.balance_port_vars[pump_name]:
                    self.balance_port_vars[pump_name][channel] = tk.StringVar(value=str(default_port))

                balance_port_entry = tk.Entry(pump_balance_frame,
                                              textvariable=self.balance_port_vars[pump_name][channel],
                                              width=8)
                balance_port_entry.grid(row=i + 1, column=channel + 1, padx=5)

        pump_balance_frame.pack(pady=10)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")

        self.create_assignment_section(
            title="Temperatures",
            headers=["Name", "Register 1"],
            items=self.temperatures_list
        )

        self.create_assignment_section(
            title="Pressure Transmitters",
            headers=["Name", "Register 1"],
            items=self.pressure_transmitters_list
        )

        self.create_assignment_section(
            title="Balances",
            headers=["Name", "Register 1"],
            items=self.balances_list
        )

        self.create_assignment_section(
            title="Pressure Regulators",
            headers=["Name", "Register 1"],
            items=self.pressure_regulators_list
        )

        self.create_assignment_section(
            title="Pressure In/Outs",
            headers=["Name", "Address"],
            items=self.pressure_inouts_list
        )

        self.create_assignment_section(
            title="Valves",
            headers=["Name", "Address"],
            items=self.valves_list
        )

        self.create_assignment_section(
            title="Stirrers",
            headers=["Name", "Register 1"],
            items=self.stirrers_list
        )

        self.create_assignment_section(
            title="Continuous Operation - Pressure Driven",
            headers=["Name", "Register 1"],
            items=self.drums_list
        )

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")

    def setup_synchronized_data_collection(self):
        """Create and start the synchronized data collector"""
        self.data_collector = DataCollector(self.graph)
        self.data_collector.start_collection()

    def read_float_values(self, plc_object, data_type, peltier=False):
        """
        For PLC equipment that reads float values with synchronized data collection
        data_type is the type of equipment (i.e. Temperatures or Pressure Transmitters)
        """
        print(f"[read_float_values] Starting for type: {data_type}")
        print(f"Connecting on {data_type}, equipment_data = {self.equipment_data}")
        for equipment_name in self.equipment_data[data_type]:
            if peltier:
                if 'peltier' in equipment_name:
                    continue
            label = self.equipment_data[data_type][equipment_name]
            reg1 = self.register_dictionary[data_type][equipment_name].get()
            print(f"[read_float_values] Reading {equipment_name} at reg {reg1}")

            # Create a custom function to update the buffer and the label
            def update_value_and_buffer(label, equipment_name, data_type):
                def _update(value):
                    # Update the label
                    label.config(text=str(value))

                    # Update the data collector buffer instead of directly updating the graph
                    data_type_lower = data_type.lower()
                    if data_type_lower == "pressure transmitters":
                        data_type_lower = "pressures"  # dictionary name is pressures_dict
                    self.data_collector.buffer_update(data_type_lower, equipment_name, value)
                    # print(f"[callback] {equipment_name}: Value received = {value}")

                return _update

            print(f'Creating Callback for equiptment {equipment_name}')
            callback = update_value_and_buffer(label, equipment_name, data_type)

            # Start the reading thread
            t = threading.Thread(target=lambda: plc_object.read_float(callback, reg1, reg1 + 1))
            t.daemon = True
            t.start()

    def read_balance_float_values(self, balance_object, data_type):
        """
        For PLC equipment that reads float values with synchronized data collection
        data_type is the type of equipment (i.e. Temperatures or Pressure Transmitters)
        """
        print(f"[read_float_balance_values] Starting for type: {data_type}")
        for equipment_name in self.equipment_data[data_type]:  # FOR EACH BALANCE COM
            label = self.equipment_data[data_type][equipment_name]
            COM = self.register_dictionary[data_type][equipment_name].get()
            print(f"[read_float_values] Reading {equipment_name} at reg {COM}")

            # Create a custom function to update the buffer and the label
            def update_value_and_buffer(label, equipment_name, data_type):
                def _update(value):
                    # Update the label
                    label.config(text=str(value))

                    # Update the data collector buffer instead of directly updating the graph
                    data_type_lower = data_type.lower()
                    if data_type_lower == "pressure transmitters":
                        data_type_lower = "pressures"  # dictionary name is pressures_dict
                    self.data_collector.buffer_update(data_type_lower, equipment_name, value)
                    # print(f"[callback] {equipment_name}: Value received = {value}")

                return _update

            print(f'Creating Callback for equiptment {equipment_name}')
            callback = update_value_and_buffer(label, equipment_name, data_type)

            # Start the reading thread
            t = threading.Thread(target=lambda: balance_object.read_float(callback, COM))
            t.daemon = True
            t.start()

    def read_peltier_float_values(self, peltier_object, data_type, address):
        """
                For PLC equipment that reads float values with synchronized data collection
                data_type is the type of equipment (i.e. Temperatures or Pressure Transmitters)
                """
        print(f"[read_float_balance_values] Starting for type: {data_type}")
        for equipment_name in self.equipment_data[data_type]:  # FOR EACH BALANCE COM
            label = self.equipment_data[data_type][equipment_name]
            COM = self.register_dictionary[data_type][equipment_name].get()
            print(f"[read_float_values] Reading {equipment_name} at reg {COM}")

            # Create a custom function to update the buffer and the label
            def update_value_and_buffer(label, equipment_name, data_type):
                def _update(value):
                    # Update the label
                    label.config(text=str(value))

                    # Update the data collector buffer instead of directly updating the graph
                    data_type_lower = data_type.lower()
                    if data_type_lower == "pressure transmitters":
                        data_type_lower = "pressures"  # dictionary name is pressures_dict
                    self.data_collector.buffer_update(data_type_lower, equipment_name, value)
                    # print(f"[callback] {equipment_name}: Value received = {value}")

                return _update

            print(f'Creating Callback for equiptment {equipment_name}')
            callback = update_value_and_buffer(label, equipment_name, data_type)

            # Start the reading thread
            t = threading.Thread(target=lambda: peltier_object.read_float(callback, COM))
            t.daemon = True
            t.start()

    def write_float_values(self, equipment_type, equipment_name, value):
        """
        Function to write float values to PLC.
        equipment type will be "Pressure Regulators" or "Stirrers"
        """
        if equipment_type == "Pressure Regulators":
            object = self.pressure_regulator_plc
        elif equipment_type == "Stirrers":
            object = self.stirrer_plc
        elif equipment_type == "Peltiers":
            object = self.peltier_com

        reg1 = self.register_dictionary[equipment_type][equipment_name].get()
        print('reg1', reg1)
        object.write_float(reg1, value)

    def toggle_onoff(self, equipment_type, equipment_name, boolean, on_btn, off_btn):
        """
        Turn equipment on or off
        equipment type is "Pressure In/Outs" or "Valves"
        """
        if boolean:
            on_btn.config(state=tk.DISABLED, relief=tk.SUNKEN)
            off_btn.config(state=tk.NORMAL, relief=tk.RAISED)
        else:
            off_btn.config(state=tk.DISABLED, relief=tk.SUNKEN)
            on_btn.config(state=tk.NORMAL, relief=tk.RAISED)
        if equipment_type == "Pressure In/Outs":
            plc_object = self.pressure_inout_plc
        elif equipment_type == "Valves":
            plc_object = self.valve_plc
        elif equipment_type == "Continuous Operation - Pressure Driven":
            plc_object = self.drum_plc
        else:
            print(f"Equipment type {equipment_type} not found")
        address = self.register_dictionary[equipment_type][equipment_name].get()
        plc_object.write_onoff(address, boolean)

    def exit_shortcut(self, event):
        """Exit the GUI when the escape key is pressed."""
        if event.keysym == "Escape":
            self.root.quit()

    def on_closing(self):
        """Handle window close event with data collector cleanup."""
        if hasattr(self, 'data_collector'):
            self.data_collector.stop_collection()

        if hasattr(self, 'graph'):
            self.graph.stop_plotting(True)
        for pump_index in range(len(self.pump_objects)):
            if self.pump_connect_vars[pump_index]:
                try:
                    pump_control = self.pump_objects[pump_index]
                    if hasattr(pump_control, "serial_obj") and pump_control.serial_obj:
                        pump_control.serial_obj.close()
                        print(f"Closed pump {pump_index}")
                except Exception as e:
                    print(f"Error closing pump {pump_index}: {e}")

        time.sleep(0.2)

        self.root.destroy()
        sys.exit(0)

    def test(self):
        print('Test balance connection')
        p = f'COM{5}'
        ser = serial.Serial(port=p, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                            bytesize=serial.EIGHTBITS, timeout=0.2)
        print("connected to: " + ser.portstr)
        from time import sleep
        for i in range(5):
            balance_data = ser.read(1000)
            value = balance_data.split()[1].decode('ascii').strip()
            value = float(value.split('g')[0])
            print('Read value:', value)
            sleep(.5)

        ser.close()
        print(f'Closed {ser.portstr}')


gui = System2()