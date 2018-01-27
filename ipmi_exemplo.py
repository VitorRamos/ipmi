import ipmi
import time
import os

ipmi_sensor= ipmi.IPMI("http://localhost:8080", "admin", "admin")

try:
	while 1:
		ipmi_sensor.get_data()
#		os.system('clear')
		ipmi_sensor.print_data()
		time.sleep(1)
except KeyboardInterrupt:
	ipmi_sensor.save_data("data")
	ipmi_sensor.clear_data()
	print "Saving"
	
