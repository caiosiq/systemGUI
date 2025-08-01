import Py_TC720

# Connect to the device
my_device = Py_TC720.TC720('COM11',
                           mode = 1,
                           )
#
# #
# my_device.set_single_sequence(1, temp=30, ramp_time=10,
#                                        soak_time=10,go_to=2,repeats=3)
#
# my_device.set_single_sequence(2, temp=40, ramp_time=10,
#                                        soak_time=10,go_to=3,repeats=3)
#
# my_device.set_single_sequence(3, temp=20, ramp_time=10,
#                                        soak_time=10,go_to=1,repeats=3)
# my_device.set_single_sequence(4, temp=20, ramp_time=10,
#                                        soak_time=30000, go_to = 4, repeats = 5)
# print(my_device.get_sequence(location='all'))
# my_device.start_soak()
# my_device.idle_soak()

# # Set to computer control mode
# my_device.set_mode(0)
# my_device.set_idle()
# desired_temp = 25
# my_device.set_temp(desired_temp)
# # Now you can use functions like:
temp1 = my_device.get_temp1()
print(f"Temperature 1: {temp1} C") # print(temp1)
temp2 = my_device.get_temp2()
print(f"Temperature 2: {temp2} C") # print(temp1)
#
# control_type = my_device.get_control_type()
# print(f"Control type: {control_type}")
# get_set_temp = my_device.get_set_temp()
# print(f"Set temperature: {get_set_temp}")



# my_device.set_mode(1)

