import tkinter as tk
import threading
from System2_Serial import Pump, Balance, read_floats_class, one_bit_class, write_floats_class
from System2_PID import pid_control, excel_file, graph
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

pump1_controller = {
    "set_point": None,
    "kp": 0.1,
    "ki": 0.0001,
    "kd": 0.01,
    "integral_error_limit": 100,
}
pump2_controller = {
    "set_point": None,
    "kp": 1,
    "ki": 1,
    "kd": 1,
    "integral_error_limit": 100,
}
pump3_controller = {
    "set_point": None,
    "kp": 1,
    "ki": 1,
    "kd": 1,
    "integral_error_limit": 100,
}
pump4_controller = {
    "set_point": None,
    "kp": 1,
    "ki": 1,
    "kd": 1,
    "integral_error_limit": 100,
}

pump_controllers = [
    pump1_controller,
    pump2_controller,
    pump3_controller,
    pump4_controller
]
matrix_lengths = [10] * len(pump_controllers)

class System2:
    def __init__(self):
        self.root = tk.Tk()
        tk.Label(self.root, text="System Two", font=("Arial", 18, "bold")).pack(
            pady=10
        )

        vscrollbar = tk.Scrollbar(self.root, orient="vertical")
        vscrollbar.pack(fill="y", side="right", expand=False)
        hscrollbar = tk.Scrollbar(self.root, orient="horizontal")
        hscrollbar.pack(fill="x", side="bottom", expand=False)
        canvas = tk.Canvas(
            self.root,
            bd=0,
            highlightthickness=0,
            yscrollcommand=vscrollbar.set,
            xscrollcommand=hscrollbar.set,
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

        gui_frame = tk.Frame(self.interior)

        ### ---EQUIPMENT--- ###
        equipment_frame = tk.Frame(gui_frame)
        # self.excel_obj = None

        ### --- PUMPS --- ###
        pumps_frame = tk.Frame(equipment_frame)
        tk.Label(equipment_frame, text="Pumps", font=("Arial", 16, "underline")).pack(
            anchor="nw", padx=15
        )
        tk.Label(pumps_frame, text="Connect", font=("Arial", 12, "bold")).grid(
            row=0, column=1
        )
        tk.Label(pumps_frame, text="On", font=("Arial", 12, "bold")).grid(
            row=0, column=2
        )
        tk.Label(pumps_frame, text="Off", font=("Arial", 12, "bold")).grid(
            row=0, column=3
        )
        tk.Label(pumps_frame, text="Flow Rate", font=("Arial", 12, "bold")).grid(
            row=0, column=4
        )
        tk.Label(pumps_frame, text="Set Flow Rate", font=("Arial", 12, "bold")).grid(
            row=0, column=5
        )
        self.pumps_list = [
            "Pump 1",
            "Pump 2",
            "Pump 3",
            "Pump 4",
        ]
        self.pump_connect_vars = [False] * len(self.pumps_list)
        self.pump_connect_buttons = []
        self.pump_sers = [None] * len(self.pumps_list)
        self.balance_sers = [None] * len(self.pumps_list)
        self.pump_on_buttons = []
        self.pump_off_buttons = []
        self.pump_flow_entry_vars = []

        self.pump_pid_classes = [None] * len(self.pumps_list)
        self.pump_pid_threads_started = [False] * len(self.pumps_list)
        self.pid_vars = [tk.BooleanVar(value=True) for _ in self.pumps_list]

        for i, pump_name in enumerate(self.pumps_list):
            # Pump names
            tk.Label(pumps_frame, text=pump_name).grid(
                row=i + 1, column=0, sticky="w"
            )

            # Connect buttons
            pump_connect_button = tk.Button(
                pumps_frame,
                text="Disconnected",
                width=12,
                command=lambda i=i: self.pump_connect(i),
            )
            pump_connect_button.grid(row=i + 1, column=1, padx=10)
            self.pump_connect_buttons.append(pump_connect_button)

            # On/Off buttons
            pump_on_button = tk.Button(
                pumps_frame, text="On", width=7, command=lambda i=i: self.pump_on(i)
            )
            pump_off_button = tk.Button(
                pumps_frame, text="Off", width=7, command=lambda i=i: self.pump_off(i)
            )
            self.pump_on_buttons.append(pump_on_button)
            self.pump_off_buttons.append(pump_off_button)
            pump_on_button.grid(row=i + 1, column=2, padx=10)
            pump_off_button.grid(row=i + 1, column=3, padx=10)

            # Entry for flow rate
            self.pump_flow_entry_var = tk.StringVar()
            pump_flow_entry = tk.Entry(
                pumps_frame, textvariable=self.pump_flow_entry_var, width=15
            )
            pump_flow_entry.grid(row=i + 1, column=4, padx=10)
            self.pump_flow_entry_vars.append(self.pump_flow_entry_var)

            # Set Flow Rate Button
            pump_set_flow_rate_button = tk.Button(
                pumps_frame,
                text="Set",
                width=5,
                command=lambda i=i: self.pump_set_flow_rate(i),
            )
            pump_set_flow_rate_button.grid(row=i + 1, column=5)

            # use pid or no
            data_types_checkbox = tk.Checkbutton(
                pumps_frame,
                text="PID",
                variable=self.pid_vars[i],
                command=lambda i=i: self.change_pid_onoff(i),
            )
            data_types_checkbox.grid(row=i + 1, column=6)

        pumps_frame.pack(anchor="nw", padx=15)

        self.pump_type_vars = [None for _ in self.pumps_list]
        self.pump_port_vars = [None for _ in self.pumps_list]
        self.balance_port_vars = [None for _ in self.pumps_list]

        ### --- TEMPERATURES --- ###
        temps_frame = tk.Frame(equipment_frame)
        tk.Label(
            equipment_frame,
            text="Temperatures (°C)",
            font=("Arial", 16, "underline"),
        ).pack(anchor="nw", padx=15, pady=(10, 0))
        self.temps_list = [
            "Temperature 1",
            "Temperature 2"
        ]
        self.temp_connect_var = tk.IntVar()
        self.temp_connect_var.set(0)  # Initial state: off
        self.temp_reg1_vars = [None for _ in self.temps_list]
        self.temp_reg2_vars = [None for _ in self.temps_list]

        self.temp_connect_button = tk.Button(
            temps_frame,
            text="Connect",
            font=("Arial", 12, "bold"),
            width=12,
            command=self.temp_connect,
        )
        self.temp_connect_button.grid(row=0, column=0)

        tk.Label(temps_frame, text="Current", font=("Arial", 12, "bold")).grid(
            row=0, column=1, sticky="nsew"
        )
        self.current_temp_labels = []

        for i, temp_name in enumerate(self.temps_list):
            # Temp names
            tk.Label(temps_frame, text=temp_name).grid(
                row=i + 1, column=0, sticky="w", pady=5
            )

            current_temp_label = tk.Label(temps_frame, text=None, bg="white", width=10)
            current_temp_label.grid(row=i + 1, column=1, padx=15)
            self.current_temp_labels.append(current_temp_label)

        temps_frame.pack(anchor="nw", padx=15)

        ### --- PRESSURE TRANSMITTER --- ###
        pressure_transmitters_frame = tk.Frame(equipment_frame)
        tk.Label(
            equipment_frame,
            text="Pressure Transmitters",
            font=("Arial", 16, "underline"),
        ).pack(anchor="nw", padx=15, pady=(10, 0))
        self.pressure_transmitters_list = [
            "Pressure Transmitter 1",
            "Pressure Transmitter 2",
            "Pressure Transmitter 3"
        ]
        self.pressure_transmitter_connect_var = tk.IntVar()
        self.pressure_transmitter_connect_var.set(0)  # Initial state: off
        self.pressure_transmitter_reg1_vars = [None for _ in self.pressure_transmitters_list]
        self.pressure_transmitter_reg2_vars = [None for _ in self.pressure_transmitters_list]

        self.pressure_transmitter_connect_button = tk.Button(
            pressure_transmitters_frame,
            text="Connect",
            font=("Arial", 12, "bold"),
            width=12,
            command=self.pressure_transmitter_connect,
        )
        self.pressure_transmitter_connect_button.grid(row=0, column=0)

        tk.Label(pressure_transmitters_frame, text="Current", font=("Arial", 12, "bold")).grid(
            row=0, column=1, sticky="nsew"
        )
        self.current_pressure_transmitter_labels = []

        for i, pressure_transmitter_name in enumerate(self.pressure_transmitters_list):
            # pressure_transmitter names
            tk.Label(pressure_transmitters_frame, text=pressure_transmitter_name).grid(
                row=i + 1, column=0, sticky="w", pady=5
            )
            current_pressure_transmitter_label = tk.Label(pressure_transmitters_frame, text=None, bg="white", width=10)
            current_pressure_transmitter_label.grid(row=i + 1, column=1, padx=15)
            self.current_pressure_transmitter_labels.append(current_pressure_transmitter_label)

        pressure_transmitters_frame.pack(anchor="nw", padx=15)

        ### --- PRESSURE REGULATOR --- ###
        pressure_regulator_frame = tk.Frame(equipment_frame)
        tk.Label(
            equipment_frame, text="Pressure Regulator", font=("Arial", 16, "underline")
        ).pack(anchor="nw", padx=15, pady=(10, 0))

        self.pressure_regulator_list = ["Pressure Regulator 1", "Pressure Regulator 2"]
        self.pressure_regulator_vars = []
        self.pressure_regulator_entries = []

        self.pressure_regulator_connect_button = tk.Button(
            pressure_regulator_frame,
            text="Connect",
            font=("Arial", 12, "bold"),
            width=12,
            command=self.pressure_regulator_connect,
        )
        self.pressure_regulator_connect_button.grid(row=0, column=0)

        for i, name in enumerate(self.pressure_regulator_list):
            tk.Label(pressure_regulator_frame, text=name).grid(row=i+1, column=0)

            self.pressure_regulator_var = tk.StringVar()
            self.pressure_regulator_var.set("0")
            self.pressure_regulator_vars.append(self.pressure_regulator_var)
            pressure_regulator_entry = tk.Entry(pressure_regulator_frame, textvariable=self.pressure_regulator_var)
            pressure_regulator_entry.grid(row=i+1, column=1, padx=15, pady=10)
            self.pressure_regulator_entries.append(pressure_regulator_entry)
            tk.Button(pressure_regulator_frame, text="Enter", command=lambda i=i: self.write_float_values(i, "pressure regulator")).grid(row=i+1, column=2)

        pressure_regulator_frame.pack(anchor="nw", padx=15)

        self.pressure_regulator_connect_var = tk.IntVar()
        self.pressure_regulator_connect_var.set(0)  # Initial state: off
        self.pressure_regulator_reg1_vars = [None for _ in self.pressure_regulator_list]
        self.pressure_regulator_reg2_vars = [None for _ in self.pressure_regulator_list]

        ### --- Pressure In Out --- ###
        pressure_inouts_frame = tk.Frame(equipment_frame)
        tk.Label(
            equipment_frame, text="Pressure In Out", font=("Arial", 16, "underline")
        ).pack(anchor="nw", padx=15, pady=(10, 0))
        self.pressure_inouts_list = ["Pressure 1 In", "Pressure 1 Out", "Pressure 2 In", "Pressure 2 Out", "Pressure 3 In", "Pressure 3 Out"]

        self.pressure_inout_on_buttons = []
        self.pressure_inout_off_buttons = []

        self.pressure_inout_connect_var = tk.IntVar()
        self.pressure_inout_connect_var.set(0)  # Initial state: off

        self.pressure_inout_connect_button = tk.Button(
            pressure_inouts_frame,
            text="Connect",
            font=("Arial", 12, "bold"),
            width=12,
            command=self.pressure_inout_connect,
        )
        self.pressure_inout_connect_button.grid(row=0, column=0)

        for i, pressure_inout_name in enumerate(self.pressure_inouts_list):
            # pressure_inout names
            tk.Label(pressure_inouts_frame, text=pressure_inout_name).grid(row=i+1, column=0, sticky="w")

            # On/Off buttons
            pressure_inout_on_button = tk.Button(
                pressure_inouts_frame, text="On", width=10, command=lambda i=i: self.pressure_inout_onoff(i, True)
            )
            self.pressure_inout_on_buttons.append(pressure_inout_on_button)
            pressure_inout_off_button = tk.Button(
                pressure_inouts_frame, text="Off", width=10, command=lambda i=i: self.pressure_inout_onoff(i, False)
            )
            self.pressure_inout_off_buttons.append(pressure_inout_off_button)
            pressure_inout_on_button.grid(row=i+1, column=1, padx=15)
            pressure_inout_off_button.grid(row=i+1, column=2, padx=15)

        self.pressure_inout_address_vars = [None for _ in self.pressure_inouts_list]
        pressure_inouts_frame.pack(anchor="nw", padx=15)

        ### --- VALVES --- ###
        valves_frame = tk.Frame(equipment_frame)
        tk.Label(
            equipment_frame, text="Valves", font=("Arial", 16, "underline")
        ).pack(anchor="nw", padx=15, pady=(10, 0))
        self.valves_list = ["Valve 1"]

        self.valve_on_buttons = []
        self.valve_off_buttons = []

        self.valve_connect_var = tk.IntVar()
        self.valve_connect_var.set(0)  # Initial state: off

        self.valve_connect_button = tk.Button(
            valves_frame,
            text="Connect",
            font=("Arial", 12, "bold"),
            width=12,
            command=self.valve_connect,
        )
        self.valve_connect_button.grid(row=0, column=0)
        for i, valve_name in enumerate(self.valves_list):
            # Valve names
            tk.Label(valves_frame, text=valve_name).grid(row=i+1, column=0, sticky="w")

            # On/Off buttons
            valve_on_button = tk.Button(
                valves_frame, text="On", width=10, command=lambda i=i: self.valve_onoff(i, True)
            )
            self.valve_on_buttons.append(valve_on_button)
            valve_off_button = tk.Button(
                valves_frame, text="Off", width=10, command=lambda i=i: self.valve_onoff(i, False)
            )
            self.valve_off_buttons.append(valve_off_button)
            valve_on_button.grid(row=i+1, column=1, padx=15)
            valve_off_button.grid(row=i+1, column=2, padx=15)

        self.valve_address_vars = [None for _ in self.valves_list]
        valves_frame.pack(anchor="nw", padx=15)

        ### --- STIRRER --- ###
        stirrer_frame = tk.Frame(equipment_frame)
        tk.Label(
            equipment_frame, text="Stirrer (rpm)", font=("Arial", 16, "underline")
        ).pack(anchor="nw", padx=15, pady=(10, 0))

        self.stirrer_list = ["10mL Stirrer",
                             "5mL Stirrer",
                             "40mL Stirrer"]
        self.stirrer_vars = []
        self.stirrer_entries = []

        self.stirrer_connect_button = tk.Button(
            stirrer_frame,
            text="Connect",
            font=("Arial", 12, "bold"),
            width=12,
            command=self.stirrer_connect,
        )
        self.stirrer_connect_button.grid(row=0, column=0)

        for i, name in enumerate(self.stirrer_list):
            tk.Label(stirrer_frame, text=name).grid(row=i+1, column=0)

            self.stirrer_var = tk.StringVar()
            self.stirrer_var.set("0")
            self.stirrer_vars.append(self.stirrer_var)
            stirrer_entry = tk.Entry(stirrer_frame, textvariable=self.stirrer_var)
            stirrer_entry.grid(row=i+1, column=1, padx=15, pady=10)
            self.stirrer_entries.append(stirrer_entry)
            tk.Button(stirrer_frame, text="Enter", command=lambda i=i: self.write_float_values(i, "stirrer")).grid(row=i+1, column=2)

        stirrer_frame.pack(anchor="nw", padx=15)

        self.stirrer_connect_var = tk.IntVar()
        self.stirrer_connect_var.set(0)  # Initial state: off
        self.stirrer_reg1_vars = [None for _ in self.stirrer_list]
        self.stirrer_reg2_vars = [None for _ in self.stirrer_list]

        # Create the assign button
        enter_button = tk.Button(
            self.root, text="Assign and Read Data", command=self.open_assign
        )
        enter_button.place(x=50, y=10)

        equipment_frame.grid(row=0, column=0, sticky="nw")

        ### --- DATA --- ###
        data_frame = tk.Frame(gui_frame)
        tk.Label(data_frame, text="Graph Data", font=("Arial", 16, "underline")).grid(
            row=0, column=0, pady=10, sticky="nw"
        )

        self.plot_temperatures = {temp_name: [False, False, []] for temp_name in self.temps_list}
        self.plot_pressures = {pressure_name: [False, False, []] for pressure_name in self.pressure_transmitters_list}
        self.plot_balances = {balance_name: [False, False, []] for balance_name in self.pumps_list}
        self.plot_flow_rates = {flow_rate_name: [False, False, []] for flow_rate_name in self.pumps_list}

        self.data_type_dict_objects = [
            self.plot_temperatures,
            self.plot_pressures,
            self.plot_balances,
            self.plot_flow_rates,
        ]

        self.g = graph(
            self.plot_temperatures,
            self.plot_pressures,
            self.plot_balances,
            self.plot_flow_rates,
        )

        # Initiate Classes
        print('remember to change line self.temp_plc = temp(....)')
        self.temp_plc = read_floats_class(NotImplementedError, NotImplementedError)  # put the host_num directly in __init__
        self.temp_plc.set_graph_obj(self.g)
        self.pressure_transmitter_plc = read_floats_class(NotImplementedError, NotImplementedError)
        self.pressure_transmitter_plc.set_graph_obj(self.g)
        self.pressure_inout_plc = one_bit_class(NotImplementedError)
        self.valve_plc = one_bit_class(NotImplementedError)
        self.stirrer_plc = write_floats_class(NotImplementedError)
        self.pressure_regulator_plc = write_floats_class(NotImplementedError)
    
        # Checkboxes for different data
        data_types_frame = tk.Frame(data_frame)
        self.data_types = ["Temperature", "Pressure", "Balance", "Flow_Rate"]
        self.data_types_vars = [tk.BooleanVar() for _ in self.data_types]
        for index, value in enumerate(self.data_types):
            data_types_checkbox = tk.Checkbutton(
                data_types_frame,
                text=value,
                variable=self.data_types_vars[index],
                command=lambda v=value: self.g.big_checkmark(v),
            )
            data_types_checkbox.grid(row=0, column=index)
            self.data_types_vars[index].trace_add("write", self.update_plot_checkboxes)
        data_types_frame.grid(row=1, column=0, sticky="w")

        # graph and graph buttons
        graph_frame = tk.Frame(data_frame)
        graph_frame.columnconfigure(0, weight=4)
        graph_frame.columnconfigure(1, weight=1)

        # graph_display
        self.graph_display_frame = tk.Frame(
            graph_frame, width=800, height=500, bg="white"
        )
        self.figure = Figure(figsize=(10, 7), dpi=100)
        plot1 = self.figure.add_subplot(221)
        plot2 = self.figure.add_subplot(222)
        plot3 = self.figure.add_subplot(223)
        plot4 = self.figure.add_subplot(224)

        plot1.set_title("Temperature Over Time")
        plot1.set_xlabel("Time (s)")
        plot1.set_ylabel("Temperature (°C)")

        plot2.set_title("Pressure Over Time")
        plot2.set_xlabel("Time (s)")
        plot2.set_ylabel("Pressure (psi)")

        plot3.set_title("Balance Over Time")
        plot3.set_xlabel("Time (s)")
        plot3.set_ylabel("Balance (g)")

        plot4.set_title("Flow Rate Over Time")
        plot4.set_xlabel("Time (s)")
        plot4.set_ylabel("Flow Rate (mL/min)")

        self.plots = [plot1, plot2, plot3, plot4]
        self.figure.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.graph_display_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()

        # graph_buttons_table
        graph_buttons_table_frame = tk.Frame(graph_frame)

        # buttons
        self.start_button = tk.Button(
            graph_buttons_table_frame,
            text="Start",
            width=20,
            command=self.change_start_button,
        )
        self.start_button.grid(row=0, column=0)
        self.stop_button = tk.Button(
            graph_buttons_table_frame,
            text="Stop",
            width=20,
            activebackground="IndianRed1",
            command=self.change_stop_button,
        )
        self.stop_button.grid(row=1, column=0)
        self.start_excel_button = tk.Button(
            graph_buttons_table_frame,
            text="Start Reading Data",
            width=20,
            command=self.start_excel,
        )
        self.start_excel_button.grid(row=2, column=0)
        self.stop_excel_button = tk.Button(
            graph_buttons_table_frame,
            text="End Reading Data",
            width=20,
            activebackground="IndianRed1",
            command=self.stop_excel,
        )
        self.stop_excel_button.grid(row=3, column=0)

        # # table
        # tk.Text(graph_buttons_table_frame, width=30, height=23, bg="gray").grid(
        #     row=4, column=0, pady=(25, 0)
        # )

        self.graph_display_frame.grid(row=0, column=0, sticky="N")
        graph_buttons_table_frame.grid(row=0, column=1, sticky="n", padx=20)
        graph_frame.grid(row=2, column=0, sticky="w")

        # Checkboxes for what to plot
        tk.Label(data_frame, text="Plot:", font=("Arial", 16, "underline")).grid(
            row=3, column=0, pady=10, sticky="nw"
        )
        self.plot_frame = tk.Frame(data_frame)

        # Temperature checkboxes
        self.plot_temperature_name = tk.Label(self.plot_frame, text="Temperature:")
        self.plot_temperature_name.grid(row=0, column=0, sticky="nw")
        self.plot_temperature_name.grid_remove()

        self.plot_temperatures_vars = [tk.BooleanVar() for _ in self.plot_temperatures]
        self.plot_temperatures_checkboxes = []
        self.plot_temperatures_frame = tk.Frame(self.plot_frame)

        for index, value in enumerate(self.plot_temperatures):
            plot_temperatures_checkbox = tk.Checkbutton(
                self.plot_temperatures_frame,
                text=value,
                variable=self.plot_temperatures_vars[index],
                command=lambda v=value: self.g.checkmark("Temperature", v),
            )
            self.plot_temperatures_checkboxes.append(plot_temperatures_checkbox)
            plot_temperatures_checkbox.grid(row=0, column=index, sticky="w")
            plot_temperatures_checkbox.grid_remove()

        self.plot_temperatures_frame.grid(row=0, column=1, sticky="w")

        # Pressure checkboxes
        self.plot_pressure_name = tk.Label(self.plot_frame, text="Pressure:")
        self.plot_pressure_name.grid(row=1, column=0, sticky="nw")
        self.plot_pressure_name.grid_remove()

        self.plot_pressures_vars = [tk.BooleanVar() for _ in self.plot_pressures]
        self.plot_pressures_checkboxes = []
        self.plot_pressures_frame = tk.Frame(self.plot_frame)

        for index, value in enumerate(self.plot_pressures):
            plot_pressures_checkbox = tk.Checkbutton(
                self.plot_pressures_frame,
                text=value,
                variable=self.plot_pressures_vars[index],
                command=lambda v=value: self.g.checkmark("Pressure", v),
            )
            self.plot_pressures_checkboxes.append(plot_pressures_checkbox)
            plot_pressures_checkbox.grid(row=0, column=index, sticky="w")
            plot_pressures_checkbox.grid_remove()

        self.plot_pressures_frame.grid(row=1, column=1, sticky="w")

        # Balance checkboxes
        self.plot_balance_name = tk.Label(self.plot_frame, text="Balance:")
        self.plot_balance_name.grid(row=2, column=0, sticky="nw")
        self.plot_balance_name.grid_remove()

        self.plot_balances_vars = [tk.BooleanVar() for _ in self.plot_balances]
        self.plot_balances_checkboxes = []
        self.plot_balances_frame = tk.Frame(self.plot_frame)

        for index, value in enumerate(self.plot_balances):
            plot_balances_checkbox = tk.Checkbutton(
                self.plot_balances_frame,
                text=value,
                variable=self.plot_balances_vars[index],
                command=lambda v=value: self.g.checkmark("Balance", v),
            )
            self.plot_balances_checkboxes.append(plot_balances_checkbox)
            plot_balances_checkbox.grid(row=0, column=index, sticky="w")
            plot_balances_checkbox.grid_remove()

        self.plot_balances_frame.grid(row=2, column=1, sticky="w")

        # Flow rate checkboxes
        self.plot_flowrate_name = tk.Label(self.plot_frame, text="Flow Rate:")
        self.plot_flowrate_name.grid(row=3, column=0, sticky="nw")
        self.plot_flowrate_name.grid_remove()

        self.plot_flow_rates_vars = [tk.BooleanVar() for _ in self.plot_flow_rates]
        self.plot_flow_rates_checkboxes = []
        self.plot_flow_rates_frame = tk.Frame(self.plot_frame)

        for index, value in enumerate(self.plot_flow_rates):
            plot_flow_rates_checkbox = tk.Checkbutton(
                self.plot_flow_rates_frame,
                text=value,
                variable=self.plot_flow_rates_vars[index],
                command=lambda v=value: self.g.checkmark("Flow_Rate", v),
            )
            self.plot_flow_rates_checkboxes.append(plot_flow_rates_checkbox)
            plot_flow_rates_checkbox.grid(row=0, column=index, sticky="w")
            plot_flow_rates_checkbox.grid_remove()

        self.plot_flow_rates_frame.grid(row=3, column=1, sticky="w")

        self.plot_frame.grid(row=4, column=0, sticky="w")
        data_frame.grid(row=0, column=1, sticky="nw")

        gui_frame.pack()

        tk.Button(self.root, text="TEST", command=self.test).place(x=10, y=10)
        self.root.bind(
            "<KeyPress>", self.exit_shortcut
        )  # press escape button on keyboard to close the GUI
        self.root.mainloop()


    # equipment functions
    # pumps
    def pump_connect(self, pump_index):
        if not self.pump_connect_vars[pump_index]:  # If not connected
            self.pump_connect_vars[pump_index] = True
            self.pump_connect_buttons[pump_index].config(
                bg="LightSkyBlue1", text="Connected"
            )  # Change to blue color

            p_ser = Pump.pump_connect(self, self.pump_port_vars[pump_index].get())
            self.pump_sers[pump_index] = p_ser

            b_ser = Balance.balance_connect(
                self, self.balance_port_vars[pump_index].get()
            )
            self.balance_sers[pump_index] = b_ser

            c = pid_control(
                b_ser,
                p_ser,
                self.pump_type_vars[pump_index].get().upper(),
                self.pumps_list[pump_index],
                self.g,
            )
            self.pump_pid_classes[pump_index] = c
            c.set_excel_obj(self.excel_obj)

        else:  # If already connected
            self.pump_connect_vars[pump_index] = False
            self.pump_connect_buttons[pump_index].config(
                bg="SystemButtonFace", text="Disconnected"
            )  # Change back to default color

            p_ser = self.pump_sers[pump_index]
            Pump.pump_disconnect(self, p_ser)

            b_ser = self.balance_sers[pump_index]
            Balance.balance_disconnect(self, b_ser)

    def pump_on(self, pump_index):
        self.pump_on_buttons[pump_index].config(bg="pale green")
        self.pump_off_buttons[pump_index].config(bg="SystemButtonFace")

        if self.pump_connect_vars[pump_index]:  # if connected
            pump_type = self.pump_type_vars[pump_index].get().upper()
            ser = self.pump_sers[pump_index]

            if pump_type == "ELDEX":
                Pump.eldex_pump_command(self, ser, command="RU")
            elif pump_type == "UI-22":
                Pump.UI22_pump_command(self, ser, command="G1", value="1")

            c = self.pump_pid_classes[pump_index]
            if c:
                c.set_stop(False)

    def pump_off(
            self, pump_index
    ):  # turning off requires set flow rate to be set again
        self.pump_off_buttons[pump_index].config(bg="IndianRed1")
        self.pump_on_buttons[pump_index].config(bg="SystemButtonFace")

        if self.pump_connect_vars[pump_index]:  # if connected
            pump_type = self.pump_type_vars[pump_index].get().upper()

            c = self.pump_pid_classes[pump_index]
            if c:
                c.set_stop(True)

            ser = self.pump_sers[pump_index]
            if pump_type == "ELDEX":
                Pump.eldex_pump_command(self, ser, command="ST")
            elif pump_type == "UI-22":
                Pump.UI22_pump_command(self, ser, command="G1", value="0")

    def pump_set_flow_rate(self, index):
        if self.pump_connect_vars[index]:  # if connected, assumes pump is on
            flow_rate = float(self.pump_flow_entry_vars[index].get())
            flow_rate = f"{flow_rate:06.3f}"
            pump_type = self.pump_type_vars[index].get().upper()
            p_ser = self.pump_sers[index]
            pump_controller = pump_controllers[index]
            pump_controller["set_point"] = float(flow_rate)

            # figure out excel writing
            if pump_type == "ELDEX":
                Pump.eldex_pump_command(self, p_ser, command="SF", value=flow_rate)
            elif pump_type == "UI-22":
                flow_rate = flow_rate.replace(".", "")
                Pump.UI22_pump_command(self, p_ser, command="S3", value=flow_rate)

            c = self.pump_pid_classes[index]
            c.set_controller_and_matrix(pump_controller, matrix_lengths[index])
            c.set_stop(False)

            if not self.pump_pid_threads_started[index]:
                t_pid = threading.Thread(target=c.start)
                t_pid.daemon = True
                t_pid.start()

                self.pump_pid_threads_started[index] = True

    def change_pid_onoff(self, i):
        c = self.pump_pid_classes[i]
        if c:
            c.pid_onoff(self.pid_vars[i].get())
            if not self.pid_vars[i].get():
                print("PID control off")

    def pressure_inout_onoff(self, i, boolean):
        if boolean:
            self.pressure_inout_on_buttons[i].config(bg="LightSkyBlue1")
            self.pressure_inout_off_buttons[i].config(bg="SystemButtonFace")
            self.pressure_inout_plc.write_onoff(address_num=self.pressure_inout_address_vars[i], boolean=True)

        else:
            self.pressure_inout_off_buttons[i].config(bg="LightSkyBlue1")
            self.pressure_inout_on_buttons[i].config(bg="SystemButtonFace")
            self.pressure_inout_plc.write_onoff(address_num=self.pressure_inout_address_vars[i], boolean=False)

    def valve_onoff(self, i, boolean):
        if boolean:
            self.valve_on_buttons[i].config(bg="LightSkyBlue1")
            self.valve_off_buttons[i].config(bg="SystemButtonFace")
            self.valve_plc.write_onoff(address_num=self.valve_address_vars[i], boolean=True)

        else:
            self.valve_off_buttons[i].config(bg="LightSkyBlue1")
            self.valve_on_buttons[i].config(bg="SystemButtonFace")
            self.valve_plc.write_onoff(address_num=self.valve_address_vars[i], boolean=False)
    
    def valve_connect(self):
        if self.valve_connect_var.get() == 0:  # if not connected, connect
            self.valve_connect_button.config(bg="pale green", text="Connected")
            self.valve_connect_var.set(1)
            self.valve_plc.connect()
        else:
            self.valve_connect_var.set(0)
            self.valve_connect_button.config(bg="SystemButtonFace", text="Connect")
            self.valve_plc.disconnect()

    def pressure_inout_connect(self):
        if self.pressure_inout_connect_var.get() == 0:  # if not connected, connect
            self.pressure_inout_connect_button.config(bg="pale green", text="Connected")
            self.pressure_inout_connect_var.set(1)
            self.pressure_inout_plc.connect()
        else:
            self.pressure_inout_connect_var.set(0)
            self.pressure_inout_connect_button.config(bg="SystemButtonFace", text="Connect")
            self.pressure_inout_plc.disconnect()

    def temp_connect(self):
        if self.temp_connect_var.get() == 0:  # if not connected, connect
            self.temp_connect_button.config(bg="pale green", text="Connected")
            self.temp_connect_var.set(1)
            self.temp_plc.connect()
            self.temp_plc.reading_onoff(True)
            self.read_float_values('Temperature')
        else:
            self.temp_connect_var.set(0)
            self.temp_connect_button.config(bg="SystemButtonFace", text="Connect")
            self.temp_plc.reading_onoff(False)
            self.temp_plc.disconnect()

    def pressure_transmitter_connect(self):
        if self.pressure_transmitter_connect_var.get() == 0:  # if not connected, connect
            self.pressure_transmitter_connect_button.config(bg="pale green", text="Connected")
            self.pressure_transmitter_connect_var.set(1)
            self.pressure_transmitter_plc.connect()
            self.pressure_transmitter_plc.reading_onoff(True)
            self.read_float_values("Pressure")
        else:
            self.pressure_transmitter_connect_var.set(0)
            self.pressure_transmitter_connect_button.config(bg="SystemButtonFace", text="Connect")
            self.pressure_transmitter_plc.reading_onoff(False)
            self.pressure_transmitter_plc.disconnect()

    def read_float_values(self, data_type):
        for index, label in enumerate(self.current_temp_labels):
            reg1 = self.temp_reg1_vars[index]
            reg2 = self.temp_reg2_vars[index]
            if reg1:
                t = None
                reg1 = reg1.get()
                reg2 = reg2.get()
                if reg1 != 0 and reg2 != 0:
                    t = threading.Thread(
                        target=self.temp_plc.read_temp,
                        args=(self.temps_list[index], label, reg1, data_type, reg2),
                    )
                elif reg1 != 0:
                    t = threading.Thread(
                        target=self.temp_plc.read_temp,
                        args=(self.temps_list[index], label, reg1, data_type),
                    )
                if t:
                    t.daemon = True
                    t.start()
    
    def stirrer_connect(self):
        if self.stirrer_connect_var.get() == 0:  # if not connected, connect
            self.stirrer_connect_button.config(bg="pale green", text="Connected")
            self.stirrer_connect_var.set(1)
            self.stirrer_plc.connect()
        else:
            self.stirrer_connect_var.set(0)
            self.stirrer_connect_button.config(bg="SystemButtonFace", text="Connect")
            self.stirrer_plc.disconnect()

    def pressure_regulator_connect(self):
        if self.pressure_regulator_connect_var.get() == 0:  # if not connected, connect
            self.pressure_regulator_connect_button.config(bg="pale green", text="Connected")
            self.pressure_regulator_connect_var.set(1)
            self.pressure_regulator_plc.connect()
        else:
            self.pressure_regulator_connect_var.set(0)
            self.pressure_regulator_connect_button.config(bg="SystemButtonFace", text="Connect")
            self.pressure_regulator_plc.disconnect()
        
    def write_float_values(self, index, equipment_type):
        """
        Function to write float values to PLC. Equipment type will be:
        "stirrer" or "pressure regulator"
        """
        if equipment_type == "stirrer":
            data = list(self.stirrer_entries[index])
            reg1 = self.stirrer_reg1_vars[index]
            reg2 = self.stirrer_reg2_vars[index]
            self.stirrer_plc.write_float(data, reg1, reg2)

        if equipment_type == "pressure regulator":
            data = list(self.pressure_regulator_entries[index])
            reg1 = self.pressure_regulator_reg1_vars[index]
            reg2 = self.pressure_regulator_reg2_vars[index]
            self.pressure_regulator_plc.write_float(data, reg1, reg2)

    def open_assign(self):
        """
        Assigns a pump type and port number to each pump, and has commands to read data
        Outputs a list for pump type, pump port numbers, and balance port numbers, in the order that corresponds with self.pumps_list
        """

        self.assign_page = tk.Toplevel(self.root)
        # pumps and balance
        tk.Label(
            self.assign_page, text="Assign Pump Types and Ports", font=("Arial", 14)
        ).pack(pady=10)
        pump_frame = tk.Frame(self.assign_page)

        tk.Label(
            pump_frame, text="Pump Name", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=0)
        tk.Label(
            pump_frame, text="Pump Type", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=1)
        tk.Label(
            pump_frame, text="Pump Port Number", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=2)
        tk.Label(
            pump_frame,
            text="Balance Port Number",
            font=("TkDefaultFont", 9, "underline"),
        ).grid(row=0, column=3)

        for i, name in enumerate(self.pumps_list):
            tk.Label(pump_frame, text=name).grid(row=i + 1, column=0, padx=5)

            self.pump_type_var = tk.StringVar()
            if self.pump_type_vars[
                i
            ]:  # populate assign page with previously assigned 
                self.pump_type_var.set(self.pump_type_vars[i].get())
            pump_type_entry = tk.Entry(pump_frame, textvariable=self.pump_type_var)
            pump_type_entry.grid(row=i + 1, column=1, padx=5)
            self.pump_type_vars[i] = self.pump_type_var

            self.pump_port_var = tk.IntVar()
            if self.pump_port_vars[i]:
                self.pump_port_var.set(self.pump_port_vars[i].get())
            pump_port_entry = tk.Entry(pump_frame, textvariable=self.pump_port_var)
            pump_port_entry.grid(row=i + 1, column=2, padx=5)
            self.pump_port_vars[i] = self.pump_port_var

            # balances
            self.balance_port_var = tk.IntVar()
            if self.balance_port_vars[i]:
                self.balance_port_var.set(self.balance_port_vars[i].get())
            balance_port_entry = tk.Entry(
                pump_frame, textvariable=self.balance_port_var
            )
            balance_port_entry.grid(row=i + 1, column=3, padx=5)
            self.balance_port_vars[i] = self.balance_port_var

        pump_frame.pack(pady=10)

        # Pressure_in_out registers
        pressure_inout_frame = tk.Frame(self.assign_page)
        tk.Label(
            pressure_inout_frame, text="pressure_inout Name", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=0)
        tk.Label(
            pressure_inout_frame, text="Address", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=1)

        for i, pressure_inout_name in enumerate(self.pressure_inouts_list):
            tk.Label(pressure_inout_frame, text=pressure_inout_name).grid(row=i + 1, column=0, padx=5)

            pressure_inout_address_var = tk.IntVar()
            if self.pressure_inout_address_vars[i]:
                pressure_inout_address_var.set(self.pressure_inout_address_vars[i].get())
            pressure_inout_var_reg_entry = tk.Entry(pressure_inout_frame, textvariable=pressure_inout_address_var)
            pressure_inout_var_reg_entry.grid(row=i + 1, column=1, padx=5)
            self.pressure_inout_address_vars[i] = pressure_inout_address_var

        pressure_inout_frame.pack(pady=10)

        # Valve registers
        valve_frame = tk.Frame(self.assign_page)
        tk.Label(
            valve_frame, text="Valve Name", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=0)
        tk.Label(
            valve_frame, text="Address", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=1)

        for i, valve_name in enumerate(self.valves_list):
            tk.Label(valve_frame, text=valve_name).grid(row=i + 1, column=0, padx=5)

            valve_address_var = tk.IntVar()
            if self.valve_address_vars[i]:
                valve_address_var.set(self.valve_address_vars[i].get())
            valve_var_reg_entry = tk.Entry(valve_frame, textvariable=valve_address_var)
            valve_var_reg_entry.grid(row=i + 1, column=1, padx=5)
            self.valve_address_vars[i] = valve_address_var

        valve_frame.pack(pady=10)

        # temperature registers
        temp_frame = tk.Frame(self.assign_page)
        tk.Label(
            temp_frame, text="Temperature Name", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=0)
        tk.Label(
            temp_frame, text="Register 1", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=1)
        tk.Label(
            temp_frame, text="Register 2", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=2)

        for i, temp_name in enumerate(self.temps_list):
            tk.Label(temp_frame, text=temp_name).grid(row=i + 1, column=0, padx=5)

            temp_reg1_var = tk.IntVar()
            temp_reg2_var = tk.IntVar()
            if self.temp_reg1_vars[i]:
                temp_reg1_var.set(self.temp_reg1_vars[i].get())
            if self.temp_reg2_vars[i]:
                temp_reg2_var.set(self.temp_reg2_vars[i].get())
            temp_var_reg1_entry = tk.Entry(temp_frame, textvariable=temp_reg1_var)
            temp_var_reg2_entry = tk.Entry(temp_frame, textvariable=temp_reg2_var)
            temp_var_reg1_entry.grid(row=i + 1, column=1, padx=5)
            temp_var_reg2_entry.grid(row=i + 1, column=2, padx=5)
            self.temp_reg1_vars[i] = temp_reg1_var
            self.temp_reg2_vars[i] = temp_reg2_var

        temp_frame.pack(pady=10)

        #Pressure Regulator
        pressure_regulator_frame = tk.Frame(self.assign_page)
        tk.Label(
            pressure_regulator_frame, text="pressure_regulator Name", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=0)
        tk.Label(
            pressure_regulator_frame, text="Register 1", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=1)
        tk.Label(
            pressure_regulator_frame, text="Register 2", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=2)

        for i, pressure_regulator_name in enumerate(self.pressure_regulator_list):
            tk.Label(pressure_regulator_frame, text=pressure_regulator_name).grid(row=i + 1, column=0, padx=5)

            pressure_regulator_reg1_var = tk.IntVar()
            pressure_regulator_reg2_var = tk.IntVar()
            if self.pressure_regulator_reg1_vars[i]:
                pressure_regulator_reg1_var.set(self.pressure_regulator_reg1_vars[i].get())
            if self.pressure_regulator_reg2_vars[i]:
                pressure_regulator_reg2_var.set(self.pressure_regulator_reg2_vars[i].get())
            pressure_regulator_var_reg1_entry = tk.Entry(pressure_regulator_frame, textvariable=pressure_regulator_reg1_var)
            pressure_regulator_var_reg2_entry = tk.Entry(pressure_regulator_frame, textvariable=pressure_regulator_reg2_var)
            pressure_regulator_var_reg1_entry.grid(row=i + 1, column=1, padx=5)
            pressure_regulator_var_reg2_entry.grid(row=i + 1, column=2, padx=5)
            self.pressure_regulator_reg1_vars[i] = pressure_regulator_reg1_var
            self.pressure_regulator_reg2_vars[i] = pressure_regulator_reg2_var

        pressure_regulator_frame.pack(pady=10)

        # pressure_transmitter registers
        pressure_transmitter_frame = tk.Frame(self.assign_page)
        tk.Label(
            pressure_transmitter_frame, text="Pressure Transmitter Name", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=0)
        tk.Label(
            pressure_transmitter_frame, text="Register 1", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=1)
        tk.Label(
            pressure_transmitter_frame, text="Register 2", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=2)

        for i, pressure_transmitter_name in enumerate(self.pressure_transmitters_list):
            tk.Label(pressure_transmitter_frame, text=pressure_transmitter_name).grid(row=i + 1, column=0, padx=5)

            pressure_transmitter_reg1_var = tk.IntVar()
            pressure_transmitter_reg2_var = tk.IntVar()
            if self.pressure_transmitter_reg1_vars[i]:
                pressure_transmitter_reg1_var.set(self.pressure_transmitter_reg1_vars[i].get())
            if self.pressure_transmitter_reg2_vars[i]:
                pressure_transmitter_reg2_var.set(self.pressure_transmitter_reg2_vars[i].get())
            pressure_transmitter_var_reg1_entry = tk.Entry(pressure_transmitter_frame, textvariable=pressure_transmitter_reg1_var)
            pressure_transmitter_var_reg2_entry = tk.Entry(pressure_transmitter_frame, textvariable=pressure_transmitter_reg2_var)
            pressure_transmitter_var_reg1_entry.grid(row=i + 1, column=1, padx=5)
            pressure_transmitter_var_reg2_entry.grid(row=i + 1, column=2, padx=5)
            self.pressure_transmitter_reg1_vars[i] = pressure_transmitter_reg1_var
            self.pressure_transmitter_reg2_vars[i] = pressure_transmitter_reg2_var

        pressure_transmitter_frame.pack(pady=10)

        #Stirrer
        stirrer_frame = tk.Frame(self.assign_page)
        tk.Label(
            stirrer_frame, text="Stirrer Name", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=0)
        tk.Label(
            stirrer_frame, text="Register 1", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=1)
        tk.Label(
            stirrer_frame, text="Register 2", font=("TkDefaultFont", 9, "underline")
        ).grid(row=0, column=2)

        for i, stirrer_name in enumerate(self.stirrer_list):
            tk.Label(stirrer_frame, text=stirrer_name).grid(row=i + 1, column=0, padx=5)

            stirrer_reg1_var = tk.IntVar()
            stirrer_reg2_var = tk.IntVar()
            if self.stirrer_reg1_vars[i]:
                stirrer_reg1_var.set(self.stirrer_reg1_vars[i].get())
            if self.stirrer_reg2_vars[i]:
                stirrer_reg2_var.set(self.stirrer_reg2_vars[i].get())
            stirrer_var_reg1_entry = tk.Entry(stirrer_frame, textvariable=stirrer_reg1_var)
            stirrer_var_reg2_entry = tk.Entry(stirrer_frame, textvariable=stirrer_reg2_var)
            stirrer_var_reg1_entry.grid(row=i + 1, column=1, padx=5)
            stirrer_var_reg2_entry.grid(row=i + 1, column=2, padx=5)
            self.stirrer_reg1_vars[i] = stirrer_reg1_var
            self.stirrer_reg2_vars[i] = stirrer_reg2_var

        stirrer_frame.pack(pady=10)

    # graph data functions
    def change_start_button(self):
        self.start_button.config(background="pale green")
        self.stop_button.config(background="SystemButtonFace")
        self.g.gui_plot_stop(False)
        t = threading.Thread(target=self.g.plot, args=(self.plots, self.canvas))
        t.daemon = True
        t.start()

    def change_stop_button(self):
        self.start_button.config(background="SystemButtonFace")
        self.g.gui_plot_stop(True)

    def start_excel(self):
        self.start_excel_button.config(background="pale green")
        self.stop_excel_button.config(background="SystemButtonFace")

        print("Writing data into excel file...")
        self.excel_obj = excel_file(self.pumps_list, pump_controllers, matrix_lengths)
        for c in self.pump_pid_classes:
            if c:
                c.set_excel_obj(self.excel_obj)
        t_excel = threading.Thread(target=self.excel_obj.start_file)
        t_excel.daemon = True
        t_excel.start()

    def stop_excel(self):
        self.start_excel_button.config(background="SystemButtonFace")

        print("Stopping excel file...")
        self.excel_obj.stop_file()

    def update_plot_checkboxes(self, *args):
        frames = [
            (
                self.plot_temperature_name,
                self.plot_temperatures_checkboxes,
                self.plot_temperatures_frame,
            ),
            (
                self.plot_pressure_name,
                self.plot_pressures_checkboxes,
                self.plot_pressures_frame,
            ),
            (
                self.plot_balance_name,
                self.plot_balances_checkboxes,
                self.plot_balances_frame,
            ),
            (
                self.plot_flowrate_name,
                self.plot_flow_rates_checkboxes,
                self.plot_flow_rates_frame,
            ),
        ]

        row = 0
        for i, var in enumerate(self.data_types_vars):
            name, checkboxes, frame = frames[i]
            if var.get():
                name.grid(row=row, column=0, sticky="nw")
                frame.grid(row=row, column=1, sticky="w")
                for checkbox in checkboxes:
                    checkbox.grid()
                row += 1
            else:
                name.grid_remove()
                frame.grid_remove()
                for checkbox in checkboxes:
                    checkbox.grid_remove()

    # Other functions
    def exit_shortcut(self, event):
        """Shortcut for exiting all pages"""
        if event.keysym == "Escape":
            quit()

    def test(self):
        from pymodbus.client import ModbusTcpClient
        client = ModbusTcpClient(host="169.254.92.250")
        client.write_coil(address=8386, value=False)
        client.write_coil(address=8387, value=False)
        print('testing complete')
        pass

gui = System2()