import time
from scipy.stats import linregress
from datetime import datetime
import collections
from openpyxl import Workbook
import matplotlib.pyplot as plt

class pid_control:
    def __init__(self, balance_ser, pump_ser, pump_type, pump_name, graph_obj):
        self.balance_ser = balance_ser
        self.pump_ser = pump_ser
        self.pump_controller = None
        self.pump_type = pump_type
        self.pump_name = pump_name
        self.max_data_points = 10
        self.graph_obj = graph_obj

        self.pid_var = True
        self.excel_obj = None
        self.mass = None
        self.flow_rate = None
        self.pid_output = None

        self.stop = False

    def set_stop(self, boolean):
        self.stop = boolean

        self.mass = None
        self.flow_rate = None
        self.pid_output = None

    def set_excel_obj(self, excel_obj):
        self.excel_obj = excel_obj

    def pid_onoff(self, boolean):
        self.pid_var = boolean

    def set_controller_and_matrix(self, controller, matrix_len):
        p = controller
        self.pump_controller = self.pid(p['set_point'], p['kp'], p['ki'], p['kd'], p['integral_error_limit'])
        self.max_data_points = matrix_len

    class pid:
        def __init__(self, set_point, kp, ki, kd, integral_error_limit):
            """
            set_point = set point: the desired value to output // constant, based on GUI
            pv = process variable: the current measured output // changes every recall, based on phsyical system
            kp = proportional gain // constant
            ki = integral gain // constant
            t = time // changes
            last_error // changes every recall, initially at 0
            reset // changes every recall, intially at 0
            """
            if set_point:
                self._set_point = float(set_point)
            self._kp = float(kp)
            self._ki = float(ki)
            self._kd = float(kd)
            self._integral_error_limit = float(integral_error_limit)

            self._last_error = 0.0
            self._integral_error = 0.0
            self._last_time = time.time()

        def __call__(self, process_variable):
            """
            inputs: process_variable, which is the flow rate that is currently being measured
            call this "function" to output a flow rate that should be closer to the set point
            """
            end_time = time.time()
            t = end_time - self._last_time

            if process_variable == 0:
                self._error = 0
            else:
                self._error = self._set_point - process_variable

            #proportional
            p = self._kp * self._error

            #integral
            self._integral_error += self._error * t

            if self._integral_error_limit and abs(self._integral_error) > self._integral_error_limit:
                self._integral_error = self._integral_error_limit

            i = self._ki * self._integral_error

            #derivative
            d = self._kd * (self._error - self._last_error) / t if t > 0 else 0
            self._last_error = self._error
            self._last_time = time.time()

            output = self._set_point + p + i + d
            return output

        def get_flow_rate(self):
            return self._set_point

    class Balance():
        def __init__(self, max_data_points):
            self.max_data_points = max_data_points
            self._times = collections.deque(maxlen=self.max_data_points)
            self._masses = collections.deque(maxlen=self.max_data_points)
            self._mass = None
            self._mass_flow_rate = 0.0
            self._counter = 0

        @property
        def mass(self):
            return self._mass

        @mass.setter
        def mass(self, value):
            """
            inputs: value - masses that are read from the balance using serial
            sets self._mass as the value, appends the current time to self._times, appends value to masses
            every 20 inputs, calculate dt and if dt>120, calculate flow rate and reset self._times and self._masses
            """
            self._counter += 1

            t = time.time()
            value = float(value)
            self._mass = value
            self._times.append(t)
            self._masses.append(value)

            if self._counter == self.max_data_points:
                try:
                    self.estimate_flow_rate()
                except Exception as e:
                    print(f'Exception occured while estimating mass flow rate for balance {self}: {e}')
                self._counter = 0

        def estimate_flow_rate(self):
            try:
                result = linregress(self._times, self._masses)
                self._mass_flow_rate = result.slope * 60
            except Exception:
                self._mass_flow_rate = 0.0
                raise

        @property
        def flow_rate(self):
            """
            outputs flow rate which is the process variable in PID
            """
            try:
                return self._mass_flow_rate
            except:
                return 0.0

    def start(self):
        balance_ser = self.balance_ser
        pump_ser = self.pump_ser
        b = self.Balance(self.max_data_points)

        last_flow_rate = 0.0
        while True:
            while not self.stop:
                # try:
                    balance_data = balance_ser.read(1000)
                    value = balance_data.split()[1].decode('ascii').strip()

                    if value.startswith('+') or value.startswith('-'):
                        print('skip')
                        continue
                    else:
                        mass_in_float = float(value.split('g')[0])
                        b.mass = mass_in_float
                        flow_rate = -(b.flow_rate)

                        output = None
                        if flow_rate != last_flow_rate and self.pid_var: #puts into pid control
                            output = float(self.pump_controller(flow_rate))
                            print('current flow rate:', flow_rate)
                            print('updated flow rate:', output)
                            output_str = f'{output:06.3f}' #assumes output is less than 100 and nonnegative

                            if self.pump_type == 'ELDEX':
                                #put flow rate into eldex pump command
                                command_str = f'SF{output_str}\r\n'
                                pump_ser.write(command_str.encode('ascii'))

                            elif self.pump_type == 'UI-22':
                                output_str = output_str.replace('.', '')
                                command_str = f';01,S3,{output_str}\r\n'
                                pump_ser.write(command_str.encode('ascii'))

                        last_flow_rate = flow_rate

                    self.mass = mass_in_float
                    self.flow_rate = flow_rate
                    self.pid_output = output
                    if self.excel_obj:
                        self.excel_obj.change_data(self.pump_name, self.get_last())

                    self.graph_obj.update_dict("Balance", self.pump_name, self.mass)
                    self.graph_obj.update_dict("Flow_Rate", self.pump_name, self.flow_rate)

                    time.sleep(.1)

                # except Exception as e:
                #     print('Error:', e)

            self.graph_obj.update_dict("Balance", self.pump_name, None)
            self.graph_obj.update_dict("Flow_Rate", self.pump_name, None)

            if self.excel_obj:
                self.excel_obj.change_data(self.pump_name, self.get_last()) #when exciting out loop as well

            time.sleep(.5)

    def get_last(self):
        if self.mass and self.flow_rate:
            return [self.mass, self.flow_rate, self.pid_output]
        else:
            return ['','','']

class excel_file:
    def __init__(self, pump_list, pump_controllers, matrix_lengths):
        self.pumps_data = {pump: ['','',''] for pump in pump_list}

        human_time = datetime.now()
        self.filename = str(human_time).replace(':', '_') + '.xlsx'
        self.workbook = Workbook()

        #For the descriptions/constants
        self.sheet1 = self.workbook.active
        self.sheet1.title = 'Descriptions'
        heading1 = [f'Pump{x+1}' for x in range(len(pump_list))]
        self.sheet1.append(heading1)
        pump_controllers = [str(controller_dict) for controller_dict in pump_controllers]
        self.sheet1.append(pump_controllers)
        self.sheet1.append(matrix_lengths)

        self.sheet2 = self.workbook.create_sheet(title='Data')
        heading2 = ['Time']
        for pump in self.pumps_data:
            heading2.append(pump + ': Mass (g)')
            heading2.append(pump + ': Flow Rate (g/min)')
            heading2.append(pump + ': PID Value (mL/min)')
        self.sheet2.append(heading2)

        self.stopped = False

    def change_data(self, pump, data):
        #data should be an array of [mass, flow rate, pid value]
        self.pumps_data[pump] = data

    def start_file(self):
        while not self.stopped:
            human_time = datetime.now()
            data_line = [human_time]
            for p in self.pumps_data:
                mass = self.pumps_data[p][0]
                flow_rate = self.pumps_data[p][1]
                pid_value = self.pumps_data[p][2]
                data_line.append(mass)
                data_line.append(flow_rate)
                data_line.append(pid_value)
            self.sheet2.append(data_line)
            time.sleep(.2)

    def stop_file(self):
        self.stopped = True
        self.workbook.save(self.filename)
        self.workbook.close()


class graph:
    def __init__(self, temperature_dict, pressure_dict, balance_dict, flow_rate_dict):
        self.temperature_dict = temperature_dict
        self.pressure_dict = pressure_dict
        self.balance_dict = balance_dict
        self.flow_rate_dict = flow_rate_dict
        self.data_dicts = [('Temperature', self.temperature_dict),('Pressure', self.pressure_dict),
                        ('Balance', self.balance_dict),('Flow Rate', self.flow_rate_dict)]
        self.color_map = {}

        self.gui_plot_stopped = False

    def big_checkmark(self, dict_type):
        #remove all little checkmarks within
        d = self.get_dict_type(dict_type)

        if d:
            for name in d:
                d[name][0] = not d[name][0]

    def plot(self, plots, canvas):
        while not self.gui_plot_stopped:
            for p in plots:
                p.clear()
                
            plots[0].set_title('Temperature Over Time')
            plots[0].set_xlabel('Time (s)')
            plots[0].set_ylabel('Temperature (°C)')

            plots[1].set_title('Pressure Over Time')
            plots[1].set_xlabel('Time (s)')
            plots[1].set_ylabel('Pressure (psi)')

            plots[2].set_title('Balance Over Time')
            plots[2].set_xlabel('Time (s)')
            plots[2].set_ylabel('Balance (g)')

            plots[3].set_title('Flow Rate Over Time')
            plots[3].set_xlabel('Time (s)')
            plots[3].set_ylabel('Flow Rate (mL/min)')

            for label, data_dict in self.data_dicts:
                plotted = False
                p_idx = {'Temperature': 0, 'Pressure': 1, 'Balance': 2, 'Flow Rate': 3}[label]
                p = plots[p_idx]
                for name, var_value in data_dict.items():
                    if var_value[0] and var_value[1]:
                        times = [t for t, v in var_value[2]]
                        values = [v for t, v in var_value[2]]

                        if name not in self.color_map:
                            self.color_map[name] = plt.get_cmap("tab10")(len(self.color_map) % 10)

                        p.plot(times, values, label=f'{label}: {name}', color=self.color_map[name])
                        plotted = True

                if plotted:
                    p.legend()  # Add legend for each specific plot
            canvas.draw()
            time.sleep(.5)

    def update_dict(self, dict_type, name, value):
        d = self.get_dict_type(dict_type)
        if d and d[name][0] and d[name][1]:
            d[name][2].append((time.perf_counter(),value))

    def checkmark(self, dict_type, name):
        d = self.get_dict_type(dict_type)

        if d and d[name][0]:
            if d[name][1]:  # If currently checked, uncheck and insert None to create a gap
                d[name][2].append((None, None))
            d[name][1] = not d[name][1]

    def get_dict_type(self, dict_type):
        return getattr(self, f"{dict_type.lower()}_dict", None)

    def gui_plot_stop(self, boolean):
        self.gui_plot_stopped = boolean

    def test(self):
        pass