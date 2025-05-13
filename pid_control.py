import time
import threading
import collections
from scipy.stats import linregress
import numpy as np
import serial

class PIDControl:
    """
    PID control class for regulating pump flow rate based on real-time balance readings.
    This controller continuously calculates error between the target flow rate (set point)
    and actual measured flow rate, then adjusts the pump speed to minimize this error.
    """
    def __init__(self, balance_ser, pump_ser, pump_type, pump_name, graph_obj):
        """
        Initialize PID controller with required components.
        
        Args:
            balance_ser: Serial connection to balance
            pump_ser: Serial connection to pump
            pump_type: Type of pump ('ELDEX', 'UI-22', or 'REGLO')
            pump_name: Name for identifying this controller
            graph_obj: Graph object for visualization
        """
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
        self.pid_thread = None
        self._exit_thread = False

    def set_stop(self, boolean):
        """
        Stop or start the PID control loop.
        
        Args:
            boolean: True to stop, False to allow running
        """
        self.stop = boolean

        if boolean:
            self.mass = None
            self.flow_rate = None
            self.pid_output = None

    def set_excel_obj(self, excel_obj):
        """
        Set Excel object for data export.
        
        Args:
            excel_obj: Excel export object
        """
        self.excel_obj = excel_obj

    def pid_onoff(self, boolean):
        """
        Enable or disable PID control.
        
        Args:
            boolean: True to enable PID, False to disable
        """
        self.pid_var = boolean

    def set_controller_and_matrix(self, controller, matrix_len):
        """
        Configure the PID controller with parameters and data buffer length.
        
        Args:
            controller: Dictionary with PID parameters (set_point, kp, ki, kd, integral_error_limit)
            matrix_len: Length of data matrix for flow rate calculation
        """
        p = controller
        self.pump_controller = self.PID(p['set_point'], p['kp'], p['ki'], p['kd'], p['integral_error_limit'])
        self.max_data_points = matrix_len

    class PID:
        """
        PID controller implementation.
        
        The controller calculates an output value based on:
        - Proportional term: responds to current error
        - Integral term: responds to accumulated error over time
        - Derivative term: responds to rate of change of error
        """
        def __init__(self, set_point, kp, ki, kd, integral_error_limit):
            """
            Initialize PID controller with tuning parameters.
            
            Args:
                set_point: Desired target value (flow rate)
                kp: Proportional gain
                ki: Integral gain
                kd: Derivative gain
                integral_error_limit: Maximum allowed integral error to prevent windup
            """
            if set_point is not None:
                self._set_point = float(set_point)
            else:
                self._set_point = 0.0
                
            self._kp = float(kp)
            self._ki = float(ki)
            self._kd = float(kd)
            self._integral_error_limit = float(integral_error_limit)

            self._last_error = 0.0
            self._integral_error = 0.0
            self._last_time = time.time()

        def __call__(self, process_variable):
            """
            Calculate PID output based on current process variable.
            
            Args:
                process_variable: Current measured value (flow rate)
                
            Returns:
                Flow rate output value for pump
            """
            end_time = time.time()
            t = end_time - self._last_time

            if process_variable == 0:
                self._error = 0
            else:
                self._error = self._set_point - process_variable

            # Proportional term
            p = self._kp * self._error

            # Integral term
            self._integral_error += self._error * t

            if self._integral_error_limit and abs(self._integral_error) > self._integral_error_limit:
                sign = 1 if self._integral_error > 0 else -1
                self._integral_error = sign * self._integral_error_limit

            i = self._ki * self._integral_error

            # Derivative term
            d = self._kd * (self._error - self._last_error) / t if t > 0 else 0
            self._last_error = self._error
            self._last_time = time.time()

            output = self._set_point + p + i + d
            # Ensure output is non-negative
            return max(0.0, output)

        def get_flow_rate(self):
            """Get the current set point flow rate."""
            return self._set_point

    class Balance:
        """Balance data processing for flow rate calculation."""
        def __init__(self, max_data_points):
            """
            Initialize balance data processor.
            
            Args:
                max_data_points: Maximum number of data points to store
            """
            self.max_data_points = max_data_points
            self._times = collections.deque(maxlen=self.max_data_points)
            self._masses = collections.deque(maxlen=self.max_data_points)
            self._mass = None
            self._mass_flow_rate = 0.0
            self._counter = 0

        @property
        def mass(self):
            """Get current mass reading."""
            return self._mass

        @mass.setter
        def mass(self, value):
            """
            Set current mass reading and update flow rate calculation.
            
            Args:
                value: Current mass reading
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
                    print(f'Exception occurred while estimating mass flow rate: {e}')
                self._counter = 0

        def estimate_flow_rate(self):
            """
            Estimate flow rate based on linear regression of mass vs time.
            The slope of the regression line gives mass per time.
            """
            try:
                # Convert deques to lists for linregress
                times_list = list(self._times)
                masses_list = list(self._masses)
                result = linregress(times_list, masses_list)
                # Convert to mL/min (assuming density of 1 g/mL)
                self._mass_flow_rate = result.slope * 60
            except Exception as e:
                print(f"Flow rate estimation error: {e}")
                self._mass_flow_rate = None
                raise

        @property
        def flow_rate(self):
            """Get current flow rate estimate."""
            return self._mass_flow_rate
                
    def start(self):
        """Start the PID control loop in a separate thread."""
        if self.pid_thread is None or not self.pid_thread.is_alive():
            self.stop = False
            self._exit_thread = False
            self.pid_thread = threading.Thread(target=self._pid_loop)
            self.pid_thread.daemon = True
            self.pid_thread.start()
            return True
        return False

    def _pid_loop(self):
        """Main PID control loop."""
        balance_ser = self.balance_ser
        pump_ser = self.pump_ser
        b = self.Balance(self.max_data_points)

        last_flow_rate = 0.0

        print(f"Starting PID control loop for {self.pump_name}")

        while not self._exit_thread:
            while not self.stop and not self._exit_thread:
                try:
                    # Read balance data
                    balance_data = balance_ser.readline().strip()

                    # Parse mass value from balance data
                    if isinstance(balance_data, bytes):
                        balance_data = balance_data.decode('ascii', errors='ignore')

                    # Different balance models may output data in different formats
                    try:
                        parts = balance_data.split()
                        if len(parts) >= 2:
                            value = parts[1].strip()
                        else:
                            value = balance_data.strip()

                        # Handle different balance output formats
                        if value.startswith('+') or value.startswith('-'):
                            print('skip')  # Skipping unstable readings
                            continue

                        # Extract numeric part (assuming format like "123.45g")
                        if 'g' in value:
                            mass_in_float = float(value.split('g')[0])
                        else:
                            mass_in_float = float(value)

                        # Update balance with new mass
                        b.mass = mass_in_float

                        # Use the flow rate calculated from balance mass readings
                        # Negative sign because decreasing mass = positive flow out
                        if b.flow_rate is not None:
                            flow_rate = -b.flow_rate
                        else:
                            flow_rate = last_flow_rate

                        # Store the current values for UI and logging
                        self.mass = mass_in_float
                        self.flow_rate = flow_rate

                        # Update the graph with current values
                        self.graph_obj.update_dict("balances", self.pump_name, self.mass)
                        self.graph_obj.update_dict("flow_rates", self.pump_name, self.flow_rate)

                        # Apply PID control if enabled and flow rate has been calculated
                        if self.pid_var and b.flow_rate is not None:
                            output = float(self.pump_controller(flow_rate))
                            print(
                                f'{self.pump_name} - Mass: {mass_in_float:.2f}g, Flow rate: {flow_rate:.2f} mL/min, PID output: {output:.2f}')

                            # Send command based on pump type
                            if self.pump_type == 'REGLO':
                                # Extract channel from pump name
                                try:
                                    channel = int(self.pump_name.split('_Ch')[1])
                                    pump_ser.set_speed(channel, output)
                                except (ValueError, IndexError):
                                    # If we can't parse channel from name, try to get it from the last character
                                    try:
                                        channel = int(self.pump_name[-1])
                                        pump_ser.set_speed(channel, output)
                                    except (ValueError, IndexError):
                                        # If all else fails, default to channel 1
                                        pump_ser.set_speed(1, output)
                                        print(
                                            f"Warning: Could not parse channel from {self.pump_name}, using channel 1")
                            elif self.pump_type == 'ELDEX':
                                command_str = f'SF{output:06.3f}\r\n'
                                pump_ser.write(command_str.encode('ascii'))
                            elif self.pump_type == 'UI-22':
                                output_str = f'{output:06.3f}'.replace('.', '')
                                command_str = f';01,S3,{output_str}\r\n'
                                pump_ser.write(command_str.encode('ascii'))

                            # Store the output value
                            self.pid_output = output

                        last_flow_rate = flow_rate

                        # Update Excel if available
                        if self.excel_obj:
                            self.excel_obj.change_data(self.pump_name, self.get_last())

                    except (ValueError, IndexError) as e:
                        print(f"Error parsing balance data: {e}")

                    time.sleep(0.5)

                except Exception as e:
                    print(f'Error in PID loop: {e}')
                    time.sleep(1)  # Prevent tight error loop

            # Clear data when stopped
            self.graph_obj.update_dict("balances", self.pump_name, None)
            self.graph_obj.update_dict("flow_rates", self.pump_name, None)

            if self.excel_obj:
                self.excel_obj.change_data(self.pump_name, self.get_last())

            # Check if we should exit the thread
            if self._exit_thread:
                break

            time.sleep(0.5)

    def get_last(self):
        """Get the last recorded data point."""
        if self.mass is not None and self.flow_rate is not None:
            return [self.mass, self.flow_rate, self.pid_output]
        else:
            return ['', '', '']
            
    def stop_thread(self):
        """Stop the PID control thread completely."""
        self.stop = True
        self._exit_thread = True