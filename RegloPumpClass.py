        # import serial
        # p_in = f'COM{8}'  # put in port number
        # ser_in = serial.Serial(port=p_in, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
        #                     bytesize=serial.EIGHTBITS, timeout=1)
        # print("connected to: " + ser_in.portstr)
        # p_out = f'COM{5}'  # put in port number
        # ser_out = serial.Serial(port=p_out, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
        #                     bytesize=serial.EIGHTBITS, timeout=1)
        # print("connected to: " + ser_out.portstr)

        # set flow rate
        # ser_in.write('1M1300-3[CR]\r\n'.encode('ascii'))
        # response = ser_out.readline().decode('ascii')
        # print(f'{ser_out.portstr}: {response}')

        # # turn on
        # ser_in.write('1H[CR]\r\n'.encode('ascii'))
        # response = ser_out.readline().decode('ascii')
        # print(f'{ser_out.portstr}: {response}')
        #
        # # #turn off
        # ser.write('1I[CR]\r\n'.encode('ascii'))
        # response = ser.readline().decode('ascii')
        # print(f'{ser.portstr}: {response}')

        # p = f'COM{8}'  # put in port number
        # ser = serial.Serial(port=p, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
        #                     bytesize=serial.EIGHTBITS, timeout=1)
        # print("connected to: " + ser.portstr)
        #
        # # turn on
        # ser.write('1H[CR]\r\n'.encode('ascii'))
        # response = ser.readline().decode('ascii')
        # print(f'{ser.portstr}: {response}')
        #
        # ser.close()

        # set flow rate
        # ser.write('1f1300-3[CR]\r\n'.encode('ascii'))
        # response = ser.readline().decode('ascii')
        # print(f'{ser.portstr}: {response}')

        #turn off
        # ser.write('1I[CR]\r\n'.encode('ascii'))
        # response = ser.readline().decode('ascii')
        # print(f'{ser.portstr}: {response}')




        #
        #
        # '''
        # ------------------------------------------
        # Reglo ICC Peristaltic Pump Control Library
        # ------------------------------------------
        # '''
        #
        # import serial
        # import time
        #
        # # ---------------------------------------------------------------------------------#
        # # LIBRARY MANAGING THE COMMUNICATION WITH A REGLO ICC WITH 3 INDEPENDENT CHANNELS #
        # # ---------------------------------------------------------------------------------#
        #
        # class RegloICC:
        #     # Initialize the pump
        #     def __init__(self, COM):
        #         self.COM = COM
        #         # Open the serial port with the data format corresponding to the RegloICC pump
        #         self.sp = serial.Serial(self.COM, 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
        #                                 bytesize=serial.EIGHTBITS)
        #         self.direction = [0, 0, 0]  # 0 = clockwise, 1 = counter-clockwise
        #         self.mode = [0, 0,
        #                      0]  # 0 = RPM, 1 = Flow Rate, 2 = Volume (over time), one can add here all other modes
        #         self.speed = [0, 0, 0]  # rotation speed for each channel in RPM mode
        #         # Change the size of 'direction', 'mode' and 'speed' according to the total number of channels to control.
        #         # In the case herein, 3 channels are being independently controlled
        #
        #     # Delete the pump
        #     def __del__(self):
        #         self.sp.close()
        #
        #     # Start the corresponding channel
        #     def start_channel(self, channel):
        #         command = f'{channel}H\r'.encode()  # 'H' to start the channel
        #         # \r for the carriage return [CR] required to tell the pump that the command is finished
        #         self.sp.write(command)  # write the command to the pump
        #         time.sleep(
        #             0.1)  # give the pump time to process the command after sending it before reading the response
        #         return self.sp.read(self.sp.in_waiting).decode()  # read the pump response
        #
        #     # Stop the corresponding channel
        #     def stop_channel(self, channel):
        #         command = f'{channel}I\r'.encode()  # 'I' to stop the channel
        #         self.sp.write(command)
        #         time.sleep(0.1)
        #         return self.sp.read(self.sp.in_waiting).decode()
        #
        #     # Set the rotation direction for a single channel
        #     def set_direction(self, channel, direction):
        #         if direction == 1:
        #             command = f'{channel}K\r'.encode()  # counter-clockwise
        #         else:
        #             command = f'{channel}J\r'.encode()  # clockwise
        #         self.sp.write(command)
        #         self.direction[channel - 1] = direction  # pyhton count starts from 0
        #         time.sleep(0.1)
        #         return self.sp.read(self.sp.in_waiting).decode()
        #
        #     # Get the rotation direction of a single channel
        #     def get_direction(self, channel):
        #         command = f'{channel}xD\r'.encode()  # 'xD' to get the rotation direction
        #         self.sp.write(command)
        #         time.sleep(0.1)
        #         # read the rotation direction from the corresponding channel
        #         return self.sp.read(self.sp.in_waiting).decode()
        #
        #     # Set the speed for a single channel in RPM when in RPM mode
        #     def set_speed(self, channel, speed):  # in RPM, with speed  Result: '123'                       #
        #         # pass
        #         #
        #         # Convert the decimal part to a string with two digits :                        #
        #         decimal_part = f'{int((speed - int(speed)) * 100)}'; ## --&gt; Result: '45'       #
        #                                                                                        #
        #         # Concatenate the two parts :                                                   #
        #         speed_string = f'{int(speed):03d}{int((speed - int(speed)) * 100)}';           #
        #         # --&gt; Result: '12345' representing 123.45 in fixed-point notation               #
        #                                                                                        #
        #         # When the two strings are concatenated, the result is a string that represents #
        #         # the original speed value in a fixed-point notation with three digits before   #
        #         # the decimal point and two digits after, without the decimal separator.        #
        #         #--------------------------------------------------------------------------------
        #         ## Change the setting speed to 24 RPM
        #         self.sp.write((str(channel) + f'f{speed_string}' + chr(13)).encode())
        #         # Setting speed has a resolution of 0.01 RPM so 24 RPM is assigned as 2400
        #         # Discrete type 3 data has a width of 6 characters with unused digits to the left being zeros --&gt; 002400
        #         read_data = self.sp.read(self.sp.in_waiting).decode()
        #         return read_data
        #         # The pump returns '*' after a successful execution of the command
        #
        #         # Read out speed of a single channel in RPM when in RPM mode
        #     def get_speed(self, channel):
        #         command = f'{channel}S\r'.encode()  # 'S' to get the setting speed in RPM
        #         self.sp.write(command)
        #         time.sleep(0.1)
        #         return self.sp.read(self.sp.in_waiting).decode()
        #
        #     # Set the operational mode for a single channel (you can add all other modes)
        #     def set_mode(self, channel, mode):
        #         if mode == 0:
        #             command = f'{channel}L\r'.encode()  # RPM mode
        #         elif mode == 1:
        #             command = f'{channel}M\r'.encode()  # Flow rate mode
        #         else:
        #             command = f'{channel}G\r'.encode()  # Volume (over time) mode
        #         self.sp.write(command)
        #         self.mode[channel - 1] = mode
        #         time.sleep(0.1)
        #         return self.sp.read(self.sp.in_waiting).decode()
        #
        #     # Get the operational mode of a single channel
        #     def get_mode(self, channel):
        #         command = f'{channel}xM\r'.encode()  # 'xM' to get the operational mode
        #         self.sp.write(command)
        #         time.sleep(0.1)
        #         return self.sp.read(self.sp.in_waiting).decode()
        # #
        # # # ----------------------------------------------------------------------------#
        # # #   EXAMPLES ON HOW TO USE THE DEFINED CLASS TO CONTROL THE Reglo ICC PUMP   #
        # # # ----------------------------------------------------------------------------#
        # #
        # # ### Initialize the pump with the specified COM port
        # pump = RegloICC('COM8')  # Replace 'COM8' with your actual COM port
        # # # ### Set the operational mode of channel 1 to flow rate
        # # #
        # # # ### Get the current speed setting of channel 1
        # pump.start_channel(1)
        # pump.set_mode(1, 1)
        # print('initial speed:',pump.get_speed(1))
        # # #
        # # # ### Set the setting speed of channel 1 to 24 RPM
        # print('set speed:',pump.set_speed(1, 1234))
        # ### Start channel 1
        # print('final speed:', pump.get_speed(1))
        #
        # ### Get the rotation direction of channel 1
        # # print(pump.get_direction(1))
        # #
        # # ### Set the rotation direction of channel 1 to clockwise
        # # pump.set_direction(1, 0)
        # #
        # # ### Get the current operational mode of channel 1
        # # print(pump.get_mode(1))
        # #
        # #
        ### Stop channel 1
        # time.sleep(3)
        # pump.stop_channel(1)

        ## Delete the pump object
        # del pump

        # from pymodbus.client import ModbusTcpClient
        # import time
        # def write_onoff(address_num, boolean):
        #     client = ModbusTcpClient(host="169.254.83.200")
        #     client.write_coil(address=address_num, value=boolean)

        # write_onoff(8353, True)
        # time.sleep(1)
        # write_onoff(8353, False)
