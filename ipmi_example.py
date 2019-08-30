import ipmi
import time

ipmi_sensor = ipmi.IPMI(server="http://localhost:8080", user="admin", password="admin", proxy={"http":"socks5h://admin:1080"})

while 1:
	data = ipmi_sensor.get_data()
	print(data, "\n")
	time.sleep(1)
