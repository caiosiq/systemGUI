import tkinter as tk
import threading
from System2_Serial import Pump, ReadFloatsPLC, OneBitClass, WriteFloatsPLC

class PumpControl:
    """Encapsulates all UI elements for a pump."""
    def __init__(self, connect, on_button, off_button, channel_var, flow_var):
        self.connect = connect  # Connect button
        self.on_button = on_button  # On button
        self.off_button = off_button  # Off button
        self.channel_var = channel_var  # Channel number input variable
        self.flow_var = flow_var  # Flow rate input variable

    def set_serial_obj(self, serial_obj):
        print('Setting serial object')
        self.serial_obj = serial_obj

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
        self.equipment_frame = tk.Frame(gui_frame)

        ### --- PUMPS --- ###
        self.pumps_list = ["Pump 1"]
        self.pump_connect_vars = [False] * len(self.pumps_list)
        self.pump_port_vars = [None] * len(self.pumps_list)
        self.pump_controls = {}  # Dictionary to store UI elements
        self.create_pump_ui()

        # Maps equipment type to a dictionary that maps a specific equipment to either the current_label
        # for temp and pressure transmitters, or the current value variable for pressure regulator and stirrer
        self.equipment_data = {}

        # Maps "buttons" or "vars" to a dicitonary that equipment name to variable, 
        # variable tracks if that equipment is connected (1) or not (0)
        self.connect_dictionary = {"buttons": {}, "vars": {}}

        # Maps equipment type to a dictionary that maps specific equipment number to a register value
        self.register_dictionary = {}

        self.create_temperatures_section()
        self.create_pressure_transmitter_section()
        self.create_pressure_regulator_section()
        self.create_pressure_inout_section()
        self.create_valves_section()
        self.create_stirrer_section()
        self.create_drum_section()

        # Create the assign button
        enter_button = tk.Button(self.root, text="Assign and Read Data", command=self.open_assign)
        enter_button.place(x=50, y=10)

        self.equipment_frame.grid(row=0, column=0, sticky="nw")

        # Initiate Classes
        plc_host_num = "169.254.83.200"
        self.temperature_plc = ReadFloatsPLC(plc_host_num, 502)
        self.pressure_transmitter_plc = ReadFloatsPLC(plc_host_num, 502)

        self.pressure_inout_plc = OneBitClass(plc_host_num)
        self.valve_plc = OneBitClass(plc_host_num)
        self.drum_plc = OneBitClass(plc_host_num)

        self.stirrer_plc = WriteFloatsPLC(plc_host_num)
        self.pressure_regulator_plc = WriteFloatsPLC(plc_host_num)

        gui_frame.pack()

        tk.Button(self.root, text="TEST", command=self.test).place(x=10, y=10)
        self.root.bind(
            "<KeyPress>", self.exit_shortcut
        )  # press escape button on keyboard to close the GUI
        self.root.mainloop()

    # pumps
    def create_pump_ui(self):
        """Creates UI elements for pumps."""
        frame = tk.Frame(self.equipment_frame)
        tk.Label(frame, text="Pumps", font=("Arial", 16, "underline")).grid(sticky="w", row=0, column=0)

        # Column headers
        headers = ["Connect", "On", "Off", "Channel Number", "Flow Rate", "Set Flow Rate"]
        for col, text in enumerate(headers, start=1):
            tk.Label(frame, text=text, font=("Arial", 12, "bold")).grid(row=1, column=col)

        for i, pump_name in enumerate(self.pumps_list):
            tk.Label(frame, text=pump_name).grid(row=i + 2, column=0, sticky="w")

            # Create buttons and entry fields
            connect_btn = tk.Button(frame, text="Disconnected", width=12, command=lambda i=i: self.pump_connect(i))
            on_btn = tk.Button(frame, text="On", width=7, command=lambda i=i: self.pump_on(i))
            off_btn = tk.Button(frame, text="Off", width=7, command=lambda i=i: self.pump_off(i))
            channel_var = tk.StringVar()
            channel_entry = tk.Entry(frame, textvariable=channel_var, width=5)
            flow_var = tk.StringVar()
            flow_entry = tk.Entry(frame, textvariable=flow_var, width=15)
            set_flow_btn = tk.Button(frame, text="Set", width=5, command=lambda i=i: self.pump_set_flow_rate(i))

            # Store elements in the dictionary
            self.pump_controls[i] = PumpControl(connect_btn, on_btn, off_btn, channel_var, flow_var)

            # Place elements in the grid
            connect_btn.grid(row=i + 2, column=1, padx=10)
            on_btn.grid(row=i + 2, column=2, padx=10)
            off_btn.grid(row=i + 2, column=3, padx=10)
            channel_entry.grid(row=i + 2, column=4, padx=10)
            flow_entry.grid(row=i + 2, column=5, padx=10)
            set_flow_btn.grid(row=i + 2, column=6)

        frame.pack(anchor="nw", padx=15, pady=15)

    def update_button_colors(self, pump_index, state):
        """Updates UI button colors for a given pump."""
        pump = self.pump_controls[pump_index]

        if state == "on":
            pump.on_button.config(bg="pale green")
            pump.off_button.config(bg="SystemButtonFace")
        elif state == "off":
            pump.off_button.config(bg="IndianRed1")
            pump.on_button.config(bg="SystemButtonFace")
        elif state == "connected":
            pump.connect.config(bg="LightSkyBlue1", text="Connected")
        elif state == "disconnected":
            pump.connect.config(bg="SystemButtonFace", text="Disconnected")

    def pump_connect(self, pump_index):
        """Handles connecting/disconnecting a pump."""
        pump = self.pump_controls[pump_index]

        if not self.pump_connect_vars[pump_index]:  # If not connected
            if not self.pump_port_vars[pump_index]:
                print("Please enter a port number.")
                return
            
            self.pump_connect_vars[pump_index] = True
            self.update_button_colors(pump_index, "connected")

            com_number = str(self.pump_port_vars[pump_index].get())
            pump_ser = Pump(com_number)
            pump.set_serial_obj(pump_ser)

        else:  # If already connected
            self.pump_connect_vars[pump_index] = False
            self.update_button_colors(pump_index, "disconnected")

            pump_ser = pump.serial_obj
            del pump_ser # equivalent to pump_ser.close()

    def pump_on(self, pump_index):
        """Turns on the pump if connected."""
        if not self.pump_connect_vars[pump_index]:
            return  # Ignore if pump is not connected

        self.update_button_colors(pump_index, "on")
        pump = self.pump_controls[pump_index]
        pump_ser = pump.serial_obj
        channel_number = int(pump.channel_var.get())

        pump_ser.start_channel(channel_number)

    def pump_off(self, pump_index):
        """Turns off the pump if connected."""
        if not self.pump_connect_vars[pump_index]:
            return  # Ignore if pump is not connected

        self.update_button_colors(pump_index, "off")
        pump = self.pump_controls[pump_index]
        pump_ser = pump.serial_obj
        channel_number = int(pump.channel_var.get())

        pump_ser.stop_channel(channel_number)

    def pump_set_flow_rate(self, pump_index):
        """Sets the flow rate for the pump."""
        if not self.pump_connect_vars[pump_index]:
            return  # Ignore if not connected

        pump = self.pump_controls[pump_index]
        pump_ser = pump.serial_obj
        channel_num = int(pump.channel_var.get())
        flow_rate = float(pump.flow_var.get())

        pump_ser.set_mode(channel_num, 1)  # Set to flow rate mode
        pump_ser.set_speed(channel_num, flow_rate)

    # other
    def create_equipment_section(self, title, items, connect_command, display_current=False, entry=False, onoff_buttons=False):
        frame = tk.Frame(self.equipment_frame)
        tk.Label(self.equipment_frame, text=title, font=("Arial", 16, "underline")).pack(anchor="nw", padx=15, pady=(10, 0))
        if display_current or entry:
            self.equipment_data[title] = {}
        self.register_dictionary[title] = {}
        
        for i, name in enumerate(items):
            tk.Label(frame, text=name).grid(row=i + 1, column=0, sticky="w", pady=5)
            if display_current: # Temperatures and pressure trasmitters // read float class
                current_label = tk.Label(frame, text=None, bg="white", borderwidth=1, relief="raised", width=10)
                current_label.grid(row=i + 1, column=1, padx=15)
                self.equipment_data[title][name] = current_label
                self.register_dictionary[title][name] = tk.IntVar()

                # connnect button for these two equipments
                connect_button = tk.Button(frame, text="Connect", font=("Arial", 12, "bold"), width=12, command=connect_command)
                connect_button.grid(row=0, column=0)
                self.connect_dictionary["buttons"][title] = connect_button
                self.connect_dictionary["vars"][title] = 0

            if entry: # Pressure regulators and stirrers
                var = tk.StringVar(value="0")
                entry_field = tk.Entry(frame, textvariable=var)
                entry_field.grid(row=i + 1, column=1, padx=15, pady=5)
                self.equipment_data[title][name] = var
                tk.Button(frame, text="Enter", command=lambda t=title, n=name, v = float(self.equipment_data[title][name].get()):
                           self.write_float_values(t, n, v)).grid(row=i + 1, column=2)
                self.register_dictionary[title][name] = tk.IntVar()
                
            if onoff_buttons: # Pressure in/outs and valves
                tk.Button(frame, text="On", width=10, command=lambda t=title, n=name: self.toggle_onoff(t, n, True)).grid(row=i + 1, column=1, padx=15)
                tk.Button(frame, text="Off", width=10, command=lambda t=title, n=name: self.toggle_onoff(t, n, False)).grid(row=i + 1, column=2, padx=15)
                self.register_dictionary[title][name] = tk.IntVar()
        
        frame.pack(anchor="nw", padx=15)

    def create_temperatures_section(self):
        self.temperatures_list = ["Temperature 1", "Temperature 2", "Temperature 3"]
        self.create_equipment_section("Temperatures", self.temperatures_list, self.temperature_connect, display_current=True)
        
    def create_pressure_transmitter_section(self):
        self.pressure_transmitters_list = ["Pressure Transmitter 1", "Pressure Transmitter 2", "Pressure Transmitter 3"]
        self.create_equipment_section("Pressure Transmitters", self.pressure_transmitters_list, self.pressure_transmitter_connect, display_current=True)

    def create_pressure_regulator_section(self):
        self.pressure_regulators_list = ["Pressure Regulator 1", "Pressure Regulator 2"]
        self.create_equipment_section("Pressure Regulators", self.pressure_regulators_list, self.pressure_regulator_connect, entry=True)

    def create_pressure_inout_section(self):
        self.pressure_inouts_list = ["Pressure 1 In", "Pressure 1 Out", "Pressure 2 In", "Pressure 2 Out", "Pressure 3 In", "Pressure 3 Out"]
        self.create_equipment_section("Pressure In/Outs", self.pressure_inouts_list, self.pressure_inout_connect, onoff_buttons=True)
    
    def create_valves_section(self):
        self.valves_list = ["Valve 1"]
        self.create_equipment_section("Valves", self.valves_list, self.valve_connect, onoff_buttons=True)

    def create_stirrer_section(self):
        self.stirrers_list = ["10mL Stirrer", "5mL Stirrer", "40mL Stirrer"]
        self.create_equipment_section("Stirrers", self.stirrers_list, self.stirrer_connect, entry=True)
    
    def create_drum_section(self):
        self.drums_list = ["Drum 1"]
        self.create_equipment_section("Drums", self.drums_list, self.drum_connect, onoff_buttons=True)

    def toggle_connection(self, device_name, plc, read_float=False, plc_object=None, data_type = None):
        """
        Generic method to handle connection toggling for various devices.
        :param device_name: String name of the device for debugging purposes.
        :param connect_var: Tkinter IntVar tracking connection state.
        :param connect_button: Tkinter Button to update UI.
        :param plc: The PLC object handling the device connection.
        :param read_float: Boolean indicating whether to read float values.
        :param read_type: String type of data to read if read_float is True.
        """
        connect_button =  self.connect_dictionary["buttons"][device_name]
        connect_var = self.connect_dictionary["vars"][device_name]

        if connect_var == 0:  # If not connected, connect
            connect_button.config(bg="pale green", text="Connected")
            self.connect_dictionary["vars"][device_name] = 1
            plc.connect()
            if read_float:
                plc.reading_onoff(True)
                self.read_float_values(plc_object, data_type)
        else:  # If connected, disconnect
            self.connect_dictionary["vars"][device_name] = 0
            connect_button.config(bg="SystemButtonFace", text="Connect")
            if read_float:
                plc.reading_onoff(False)
            plc.disconnect()

    def temperature_connect(self):
        self.toggle_connection("Temperatures", self.temperature_plc, read_float=True, 
                               plc_object=self.temperature_plc, data_type="Temperatures")

    def pressure_transmitter_connect(self):
        self.toggle_connection("Pressure Transmitters", self.pressure_transmitter_plc, 
                               read_float=True, plc_object=self.pressure_transmitter_plc, 
                               data_type="Pressure Transmitters")

    def valve_connect(self):
        self.toggle_connection("Valves", self.valve_plc)

    def pressure_inout_connect(self):
        self.toggle_connection("Pressure In/Outs", self.pressure_inout_plc)

    def pressure_regulator_connect(self):
        self.toggle_connection("Pressure Regulators", self.pressure_regulator_plc)

    def stirrer_connect(self):
        self.toggle_connection("Stirrers", self.stirrer_plc)

    def drum_connect(self):
        self.toggle_connection("Drums", self.drum_plc)

    def read_float_values(self, plc_object, data_type):
        """
        For PLC equipment that reads float values
        data_type is the type of equipment (i.e. Temperatures or Pressure Transmitters)
        """
        for equipment_name in self.equipment_data[data_type]:
            label = self.equipment_data[data_type][equipment_name]
            reg1 = self.register_dictionary[data_type][equipment_name].get()

            t = threading.Thread(target=plc_object.read_float, args=(label, reg1, reg1+1))
            t.daemon = True
            t.start()

    def write_float_values(self, equipment_type, equipment_name, value):
        """
        Function to write float values to PLC.
        equipment type will be "Pressure Regulators" or "Stirrers"
        """
        if equipment_type == "Pressure Regulators":
            plc_object = self.pressure_regulator_plc
        elif equipment_type == "Stirrers":
            plc_object = self.stirrer_plc

        reg1 = self.register_dictionary[equipment_type][equipment_name].get()
        plc_object.write_float(reg1, value)
    
    def toggle_onoff(self, equipment_type, equipment_name, boolean):
        """
        Turn equipment on or off
        equipment type is "Pressure In/Outs" or "Valves"
        """
        if equipment_type == "Pressure In/Outs":
            plc_object = self.pressure_inout_plc
        elif equipment_type == "Valves":
            plc_object = self.valve_plc
        elif equipment_type == "Drums":
            plc_object = self.drum_plc

        address = self.register_dictionary[equipment_type][equipment_name].get()
        plc_object.write_onoff(address, boolean)

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
        
        tk.Label(self.scrollable_frame, text="Assign Pump Types and Ports", font=("Arial", 12, "bold")).pack(pady=5)
        pump_frame = tk.Frame(self.scrollable_frame)

        tk.Label(pump_frame, text="Pump Name", font=("TkDefaultFont", 9, "underline")).grid(row=0, column=0)
        tk.Label(pump_frame, text="Pump Port Number", font=("TkDefaultFont", 9, "underline")).grid(row=0, column=1)

        for i, name in enumerate(self.pumps_list):
            tk.Label(pump_frame, text=name).grid(row=i + 1, column=0, padx=5)

            self.pump_port_var = tk.IntVar()
            if self.pump_port_vars[i]:
                self.pump_port_var.set(self.pump_port_vars[i].get())
            pump_port_entry = tk.Entry(pump_frame, textvariable=self.pump_port_var)
            pump_port_entry.grid(row=i + 1, column=1, padx=5)
            self.pump_port_vars[i] = self.pump_port_var

        pump_frame.pack(pady=10)

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

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")

    # Other functions
    def exit_shortcut(self, event):
        """Shortcut for exiting all pages"""
        if event.keysym == "Escape":
            quit()

    def test(self):
        print(self.register_dictionary["Temperatures"]["Temperature 1"].get())

gui = System2()
