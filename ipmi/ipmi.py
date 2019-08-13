import time
import struct
import datetime
import requests
import pickle
import xml.etree.ElementTree as ET

import math

def ToSigned(Num, signedbitB):
	if signedbitB > 0:
		# positive 
		if (Num%(0x01<<signedbitB)/(0x01<<(signedbitB-1)))<1:
			return Num%(0x01<<signedbitB-1)
		# negative
		else:
			temp = (Num%(0x01<<signedbitB-1)) ^ ((0x01<<signedbitB-1)-1)
			return (-1-temp)
	else:
		return Num

class IPMI:
	def __init__(self, server, user, password, proxies=None):
		self.server = server
		self.formPower = {'POWER_CONSUMPTION.XML':'(0,0)', 'time_stamp':'', '_':''}
		self.formSource = {'Get_PSInfoReadings.XML':'(0,0)', 'time_stamp':'', '_':''}
		self.formSensors = {'SENSOR_INFO.XML':'(1,ff)', 'time_stamp':'', '_':''}
		self.subpages = ['servh_psinfo', 'monitor_pw_comsumption']
		self.cookies = {'langSetFlag':'0', 'language':'English', 'SID':'', 'mainpage':'health', 'subpage':self.subpages[1]}
		self.user = user
		self.password = password
		self.proxies = proxies
		
		self.data = []
		self.conn = False

		self.login()

	def login(self):
		try:
			login = requests.post(self.server+"/cgi/login.cgi", data={'name':self.user, 'pwd':self.password})
			if 'SID' in login.cookies.get_dict().keys():
				self.cookies['SID'] = login.cookies.get_dict()['SID']
				self.conn = True
			else:
				print("Cant login")
		except requests.exceptions.RequestException as e:
			print("Connection error", e)

	def get_data(self):
		if not self.conn:
			print("Not connected")
			return
		now = datetime.datetime.now()
		tstamp = time.mktime(now.timetuple())
		self.formPower['time_stamp'] = self.formSource['time_stamp'] # fix
		self.formSource['time_stamp'] = self.formSource['time_stamp']
		self.formSensors['time_stamp'] = self.formSensors['time_stamp']
		try:
			rPower = requests.post(self.server+"/cgi/ipmi.cgi", data=self.formPower, cookies=self.cookies)
			rSource = requests.post(self.server+"/cgi/ipmi.cgi", data=self.formSource, cookies=self.cookies)
			rSensors = requests.post(self.server+"/cgi/ipmi.cgi", data=self.formSensors, cookies=self.cookies)
			return self.processXML(rPower, rSource, rSensors)
		except requests.exceptions.RequestException as e:
			print("Connection error", e)

	def processXML(self, rPower, rSource, rSensors):
		data_now = {'font_n':0,'acInVoltage':0, 'acInCurrent':0, 'acInPower':0, 'dc12OutVoltage':0, 'dc12OutCurrent':0, 'dcOutPower':0, 'temp1':0, 'temp2':0}
		sensor_now = {'Vcpu1':0, 'Vcpu2':0}
		sources= []
		pwd = []
		ipmiS = ET.fromstring(rSource.content)
		ipmiP = ET.fromstring(rPower.content)
		ipmiI = ET.fromstring(rSensors.content)
		cont = 1

		for child in ipmiS:
			for item in child:
				ps = item.attrib

				data_now['font_n'] = cont
				data_now['acInVoltage'] = int(ps['acInVoltage'], 16)
				data_now['acInCurrent'] = int(ps['acInCurrent'], 16)/1000.0
				data_now['acInPower'] = int(ps['acInPower'], 16)
				data_now['dc12OutVoltage'] = int(ps['dc12OutVoltage'], 16)/10.0
				data_now['dc12OutCurrent'] = int(ps['dc12OutCurrent'], 16)/1000.0
				data_now['dcOutPower'] = int(ps['dcOutPower'], 16)
				data_now['temp1'] = int(ps['temp1'], 16)
				data_now['temp2'] = int(ps['temp2'], 16)
				
				sources.append(data_now.copy())

				cont += 1

		for child in ipmiI:
			for item in child:
				ps = item.attrib
				if 'Vcpu1' in ps['NAME'] or 'Vcpu2' in ps['NAME']:
#					print ps['NAME']
					
					UnitType1 = int(ps['UNIT1'], 16)
					AnalogDataFormat = UnitType1 >> 6
					if AnalogDataFormat == 0x02:
						raw_data = hex(ToSigned(int(ps['READING'][:2], 16), 8))
					else:
						raw_data = ps['READING'][:2]

					m = ps['M']
					b = ps['B']
					rb = ps['RB']

					# change sequense of lsb and msb into 10b char
					M_raw = ((int(m,16)&0xC0) << 2)+(int(m,16)>>8)
					B_raw = ((int(b,16)&0xC0) << 2)+(int(b,16)>>8)

					Km_raw = int(rb,16)>>4
					Kb_raw = (int(rb,16)&0x0F)
	
					M_data = ToSigned(M_raw, 10)
					B_data = ToSigned(B_raw, 10)
					Km_data = ToSigned(Km_raw, 4)
					Kb_data = ToSigned(Kb_raw, 4)
		
					sensor_data = (M_data*int(raw_data, 16)+B_data*math.pow(10, Kb_data))*math.pow(10,Km_data)
					sensor_now[ps['NAME']] = sensor_data
#					print sensor_data
#					print '\n'
	
		for child in ipmiP:
			if child.tag == 'NOW':
				now = child.attrib
				pwd.append(dict((k, int(v)) for k, v in now.iteritems()))

		mix = {'sources':sources, 'power':pwd, 'sensor': sensor_now}
		self.data.append(mix.copy())
		return mix.copy()	

	def clear_data(self):
		self.data = []
	
	def save_data(self, name):
		with open('data/'+name+'.pkl', 'wb') as f:
			pickle.dump(self.data, f, pickle.HIGHEST_PROTOCOL)
		
	def load_data(self, name):
		with open('data/'+name+'.pkl', 'rb') as f:
			self.data = pickle.load(f)

	def print_data(self):
		if len(self.data) == 0:
			print("Sem dados")
			return
		data = self.data[-1]
		cont = 1
		for font in data['sources']:
			print("Source ", cont)
			print("AC input")
			print(str(font['acInVoltage'])+" V "+str(font['acInCurrent'])+" A "+str(font['acInPower'])+" W ") 

			print("DC output") 
			print(str(font['dc12OutVoltage'])+" V "+str(font['dc12OutCurrent'])+" A "+str(font['dcOutPower'])+" W ")

			print("Temperature 1 : "+str(font['temp1'])+" C ")
			print("Temperature 2 : "+str(font['temp2'])+" C ")

			print("\n")
			cont += 1
		print("Voltage cpu1 ", data['sensor']['Vcpu1'])
		print("Voltage cpu2 ", data['sensor']['Vcpu2'])
		print("\n")
		print("Power")
		for pw in data['power']:
			print("Min "+str(pw['MIN'])+" W Media "+str(pw['AVR'])+" W Max "+str(pw['MAX'])+" W")

