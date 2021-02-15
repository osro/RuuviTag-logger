#!/usr/bin/python3

import time
from ruuvitag_sensor.ruuvi import RuuviTagSensor, RunFlag
from ruuvitag_sensor.data_formats import DataFormats
from ruuvitag_sensor.decoder import get_decoder

# this for only support dataformat 5 as others are deprecated while making this
# list all your tags MAC: TAG_NAME
tags = {
    'CC:CA:7E:52:CC:34': '1: Backyard',
    'FB:E1:B7:04:95:EE': '2: Upstairs',
    'E8:E0:C6:0B:B8:C5': '3: Downstairs'
}

dweet = True # Enable or disable dweeting True/False
dweetUrl = 'https://dweet.io/dweet/for/' # dweet.io url
dweetThing = 'myHomeAtTheBeach' # dweet.io thing name

db = True # Enable or disable database saving True/False
dbFile = '/home/pi/ruuvitag/ruuvitag.db' # path to db file

if dweet:
	import requests
'''
Dweet format:
{
	'TAG_NAME1 temperature': VALUE,
	'TAG_NAME1 humidity': VALUE,
	'TAG_NAME1 pressure': VALUE,
	'TAG_NAME2 temperature': VALUE,
	'TAG_NAME2 humidity': VALUE,
	'TAG_NAME2 pressure': VALUE,
	etc...
}
'''

if db:
	import sqlite3
	# open database
	conn = sqlite3.connect(dbFile)

	# check if table exists
	cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sensors'")
	row = cursor.fetchone()
	if row is None:
		print("DB table not found. Creating 'sensors' table ...")
		conn.execute('''CREATE TABLE sensors
			(
				id				            INTEGER		PRIMARY KEY AUTOINCREMENT	NOT NULL,
				timestamp		            DATETIME	DEFAULT CURRENT_TIMESTAMP,				
                mac				            TEXT		NOT NULL,
				name			            TEXT		NULL,
                battery                     NUMERIC     NULL,
                pressure		            NUMERIC		NULL,
                measurement_sequence_number NUMERIC     NULL,
                acceleration_z              NUMERIC     NULL,
                acceleration_y              NUMERIC     NULL,
                acceleration_x              NUMERIC     NULL,
                acceleration                NUMERIC     NULL,
                data_format                 NUMERIC     NULL,
				temperature		            NUMERIC		NULL,
                tx_power                    NUMERIC     NULL,
				humidity		            NUMERIC		NULL,
                movement_counter            NUMERIC     NULL
			);''')
		print("Table created successfully\n")

# Extended RuuviTagSensor with name, and raw data output
class Rtag(RuuviTagSensor):

	def __init__(self, mac, name):
		self._mac = mac
		self._name = name

	@property
	def name(self):
		return self._name

	def getData(self):
		return self.get_data(self._mac)

dweetData = {}
dbData = {}

for mac, name in tags.items():
	tag = Rtag(mac, name)

	print("Looking for {} ({})".format(tag._name, tag._mac))
	
	(data_format, encoded) = tag.getData()
	sensor_data = get_decoder(data_format).decode_data(encoded)

	print ("Data received:", sensor_data)

	dbData[tag._mac] = {'name': tag._name}
	# add each sensor with value to the lists
	for sensor, value in sensor_data.items():
		dweetData[tag._name+' '+sensor] = value
		dbData[tag._mac].update({sensor: value})

	print("\n")

if dweet:
	# send data to dweet.io
	print("Dweeting data for {} ...".format(dweetThing))
	response = requests.post(dweetUrl+dweetThing, json=dweetData)
	print(response)
	#print(response.text)

if db:
	# save data to db
	print("Saving data to database ...")
	for mac, content in dbData.items():
		conn.execute("INSERT INTO sensors (mac,name,temperature,humidity,pressure,battery,measurement_sequence_number,acceleration_z,acceleration_y,acceleration_x,acceleration,data_format,tx_power,movement_counter) \
			VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".\
			format(mac, content['name'], content['temperature'], content['humidity'], content['pressure'], content['battery'], content['measurement_sequence_number'], content['acceleration_z'], content['acceleration_y'], content['acceleration_x'], content['acceleration'], content['data_format'], content['tx_power'], content['movement_counter']))
	conn.commit()
	conn.close()
	print("Done.")
