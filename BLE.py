#!/usr/bin/python
''' Bluetooth scanner inspired by and modified to run with php script for non BLE devices
   Author: jmleglise
   Date: 25-May-2016
   Description : Test yours beacon 
   URL : https://github.com/jmleglise/mylittle-domoticz/edit/master/Presence%20detection%20%28beacon%29/test_beacon.py
   Version : 1.0

 Copyright (c) 2017-05 Diving-91 (User:diving91 https://www.jeedom.fr/forum/)
 URL: https://github.com/diving91/Bluetooth-scanner

 MIT License
 Copyright (c) 2017 

 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in
 all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.'''

''' DESCRIPTION
 This script will send data to the main php script each time a BLE device is advertising
        data is a json of [[bdaddr , timestamp last seen],[...]]
 Works well with Nut mini BLE devices: (https://goo.gl/l36Gtz)
 
 USAGE
 $ python BLE.py hciAdapterID processUSer phpCallback debug jsonTagsBDaddr
        Example: sudo python ble.py 0 pi BTdaemon.php [\"EF:A2:C5:EB:A3:2F\",\"FF:FE:8A:40:FA:97\"]
 $ python BLE.py kill
        This will kill the previously launched BLE.py processes
'''
import os
import sys
import pwd
import struct
import logging
import json
import bluetooth._bluetooth as bluez
import time

LE_META_EVENT = 0x3e
OGF_LE_CTL=0x08
OCF_LE_SET_SCAN_ENABLE=0x000C
EVT_LE_CONN_COMPLETE=0x01
EVT_LE_ADVERTISING_REPORT=0x02

TAG_DATA = [] # Example [["EF:A2:C5:EB:A3:2F",0],["FF:FE:8A:40:FA:97",0]] - [bdaddr , timestamp last seen] - imported from argv[3]

me = os.path.basename(__file__)

# Check 5 args are supplied or 1 arg 'kill'
if not(len(sys.argv) == 6) and not(len(sys.argv) == 2 and sys.argv[1] =='kill'):
	print "ERROR: Please use arguments"
	print "$ python "+me+" adapterNb processUser phpcallback debug jsonTagsBdaddr"
	print "$ python "+me+" kill"
	sys.exit(1)
elif len(sys.argv) == 6: # ARG4: define logging level
	FORMAT = '%(asctime)s - %(message)s'
	if sys.argv[4] == "1":
		logLevel=logging.DEBUG
		logging.basicConfig(format=FORMAT,level=logLevel)
	elif sys.argv[4] == "0":
		logLevel=logging.CRITICAL	
		logging.basicConfig(format=FORMAT,level=logLevel)
	else:
		print "ERROR: Wrong logging level supplied - Use 0 or 1"
		sys.exit(1)

def packed_bdaddr_to_string(bdaddr_packed):
	return ':'.join('%02x'%i for i in struct.unpack("<BBBBBB", bdaddr_packed[::-1]))

def hci_toggle_le_scan(sock, enable):
	cmd_pkt = struct.pack("<BB", enable, 0x00)
	bluez.hci_send_cmd(sock, OGF_LE_CTL, OCF_LE_SET_SCAN_ENABLE, cmd_pkt)

def le_handle_connection_complete(pkt):
	status, handle, role, peer_bdaddr_type = struct.unpack("<BHBB", pkt[0:5])
	device_address = packed_bdaddr_to_string(pkt[5:11])
	interval, latency, supervision_timeout, master_clock_accuracy = struct.unpack("<HHHB", pkt[11:])
	#print "le_handle_connection output"
	#print "status: 0x%02x\nhandle: 0x%04x" % (status, handle)
	#print "role: 0x%02x" % role
	#print "device address: ", device_address

# ARG1: Kill BLE scanner or check hci adapter
if sys.argv[1] == "kill": #Kill mode
	x = os.popen("ps aux | grep " + me + " | grep -v grep| grep -v sudo | awk '{print $2}'").read().splitlines() # all processes
	x = list(set(x).difference([str(os.getpid())])) # all processes but current one
	if x:
		x = int(x[0]) # convert to pid
		print 'Kill %s process %i'%(me,x)
		os.system("sudo kill %i" % (x))
		sys.exit(0)
	else:
		print 'There is no %s process to kill'%(me)
		sys.exit(0)
else: # define hci adapter
	try:
		hciId = int(sys.argv[1]) # 0 for hci0
		logging.debug('Will Use hci adapter hci%s'%(sys.argv[1]))
	except:
		logging.critical('ERROR - Wrong HCI adapter number supplied: %s'%(sys.argv[1]))
		sys.exit(1)

# ARG2: Check processUSer
try:
	pwd.getpwnam(sys.argv[2])
	processUser = sys.argv[2]
	logging.debug('Will use %s as process User',processUser)	
except:
	logging.critical('ERROR - Wrong processUser supplied')
	sys.exit(1)
	
# ARG3: Check php script callback
callback=os.path.dirname(os.path.abspath(__file__))+"/"+str(sys.argv[3])
if os.path.exists(callback):
	callback = sys.argv[3]
	logging.debug('Will use %s as php script callback',callback)
else:
	logging.critical('ERROR - Wrong php script file name supplied: %s'%(callback))
	sys.exit(1)
	
# ARG5: json BLE TAGs mac address
try:
	tags = json.loads(sys.argv[5])
	for tag in tags:
		TAG_DATA.append([tag.encode('ascii', 'ignore'),0])
	logging.debug('Will scan %s tag(s) with bdaddr %s'%(sys.argv[5].count(":")/5,sys.argv[5]))
except:
	logging.critical('ERROR - Wrong json for TAGS: %s'%sys.argv[5])
	sys.exit(1)

# MAIN part of the script
# Connect to hci adapter
try:
	sock = bluez.hci_open_dev(hciId)
	logging.debug('Connected to bluetooth adapter hci%i',hciId)
except:
	logging.critical('Unable to connect to bluetooth device...')
	sys.exit(1)

# Enable LE scan
hci_toggle_le_scan(sock, 0x01)
# Infinite loop to listen socket
while True:
	old_filter = sock.getsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, 14)
	flt = bluez.hci_filter_new()
	bluez.hci_filter_all_events(flt)
	bluez.hci_filter_set_ptype(flt, bluez.HCI_EVENT_PKT)
	sock.setsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, flt )

	pkt = sock.recv(255)
	ptype, event, plen = struct.unpack("BBB", pkt[:3])

	if event == LE_META_EVENT:
		subevent, = struct.unpack("B", pkt[3])
		pkt = pkt[4:]
		if subevent == EVT_LE_CONN_COMPLETE:
			le_handle_connection_complete(pkt)
		elif subevent == EVT_LE_ADVERTISING_REPORT:
			num_reports = struct.unpack("B", pkt[0])[0]
			for i in range(0, num_reports):
				macAdressSeen=packed_bdaddr_to_string(pkt[3:9])
				ts = int(time.time()) # time of event
				for tag in TAG_DATA:
					if macAdressSeen.lower() == tag[0].lower():
						# More than 2 seconds from last seen, so we can call php callback. This prevent overload from high freq advertising devices
						if ts > tag[1]+2:
							tag[1]=ts # update lastseen
							logging.debug('Tag %s seen @ %i',tag[0],tag[1])
							jsonTag = json.dumps(TAG_DATA,separators=(',', ':')) # json encode TAG_DATA list
							os.system("sudo -u " + processUser + " php " + callback + " callback '" + jsonTag + "'") #call php callback
	sock.setsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, old_filter )
