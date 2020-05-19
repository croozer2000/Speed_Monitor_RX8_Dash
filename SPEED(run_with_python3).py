#!/usr/bin/python3
#
## cluster_rpm.py
# 
# This python3 program sends out CAN data from the PiCAN2 board to a Mazda RX8 instrument cluster.
# For use with PiCAN boards on the Raspberry Pi
# http://skpang.co.uk/catalog/pican2-canbus-board-for-raspberry-pi-2-p-1475.html
#
# Make sure Python-CAN is installed first http://skpang.co.uk/blog/archives/1220
#
#
#

import can
import time
import os
import subprocess
from threading import Thread
import multiprocessing
import re


RPM_PID		=  0x201
#oil temp 0x420

print('Bring up CAN0....')
os.system("sudo /sbin/ip link set can0 up type can bitrate 500000")
time.sleep(0.1)	
print('Ready')
try:
	bus = can.interface.Bus(channel='can0', bustype='socketcan_native')
except OSError:
	print('Cannot find PiCAN board.')
	GPIO.output(led,False)
	exit()

seconds = .1
run = True
speed_in = 40
rpm_in = 0
data = [rpm_in,0x00,0,0,speed_in,0,0,0]
# def rpm_go():
# 	while run:
# 		# for rpm in range(50,130):
# 		# GPIO.output(led,True)
# 		msg = can.Message(arbitration_id=RPM_PID,data=[0,0x00,0,0,speed_in,0,0,0],extended_id=False)
# 		bus.send(msg)
# 		# print(' {0:d}'.format(rpm))
# 		time.sleep(seconds)
# 		# GPIO.output(led,False)
# 		# time.sleep(0.04)
def speed_test(list_in):
	'''gets the internet speed'''
	while True:
		response = subprocess.Popen('/usr/local/bin/speedtest-cli --simple', shell=True, stdout=subprocess.PIPE).stdout.read().decode('utf-8')
		ping = re.findall('Ping:\s(.*?)\s', response, re.MULTILINE)
		download = re.findall('Download:\s(.*?)\s', response, re.MULTILINE)
		upload = re.findall('Upload:\s(.*?)\s', response, re.MULTILINE)

		ping = ping[0].replace(',', '.')
		download = download[0].replace(',', '.')
		upload = upload[0].replace(',', '.')

		print(download,upload)
		
		list_in['ping'] = ping
		list_in['download'] = download
		list_in['upload'] = upload
		time.sleep(300)

def tac():
	while run:
		for rpm in range(0,150):
			# GPIO.output(led,True)
			data[0] = rpm
			# print(' {0:d}'.format(rpm))
			time.sleep(0.4)
			# time.sleep(0.04)

def send_msg():
	# run speed test
	manager = multiprocessing.Manager()
	list_val = manager.dict({'download': 0.0,'upload':0.0,'ping':0.0})
	p1 = multiprocessing.Process(target=speed_test,args=[list_val])
	p1.start()

	while run:
		download = list_val['download']
		upload = list_val['upload']

		temp = float(download)/1.6 + 39
		data[4] = int(round(temp))

		temp = float(upload)/10 * 15
		data[0] = int(round(temp))


		# data_in = [rpm_in,0x00,0,0,speed_in,0,0,0]

		msg = can.Message(arbitration_id=RPM_PID,data=data,extended_id=False)
		bus.send(msg)
		time.sleep(0.1)
# Main loop
try:
	t1 = Thread(target=send_msg)
	t1.start()
	t2 = Thread(target=tac)
	# t2.start()



	while run:
		Myinput = input("(r)pm/(s)peed/delay: ")
		if Myinput == "exit":
			run = False
		elif Myinput[0] == 'r':
			speed_in = int(Myinput[1:])
		elif Myinput[0] == 's':
			temp = float(Myinput[1:])/1.6 + 39
			speed_in = int(round(temp))
		else:
			seconds = float(Myinput)
			print('second is', seconds)
		data[4] = speed_in

	t1.join()
	# t2.join()
except KeyboardInterrupt:
	#Catch keyboard interrupt
	GPIO.output(led,False)
	run = False
	os.system("sudo /sbin/ip link set can0 down")
	print('\n\rKeyboard interrtupt')