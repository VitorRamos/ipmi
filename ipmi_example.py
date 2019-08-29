import ipmi
import time
import os

ipmi_sensor = ipmi.IPMI("http://service3-bmc", "admin", "admin")

while 1:
	data = ipmi_sensor.get_data()
	print(data, "\n")
	time.sleep(1)