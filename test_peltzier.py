import Py_TC720

# Connect to the device
my_device = Py_TC720.TC720('COM11')

# # Set to computer control mode
my_device.set_mode(0)
# my_device.set_idle()
# desired_temp = 25
# my_device.set_temp(desired_temp)
# # Now you can use functions like:
temp1 = my_device.get_temp1()
print(f"Temperature 1: {temp1} C") # print(temp1)
#
# control_type = my_device.get_control_type()
# print(f"Control type: {control_type}")
# get_set_temp = my_device.get_set_temp()
# print(f"Set temperature: {get_set_temp}")


# my_device.set_mode(1)

