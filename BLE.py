#!/usr/bin/python
''' Bluetooth scanner inspired by and modified to run with php script for non BLE devices
   Author: jmleglise
   Date: 25-May-2016
   Description : Test yours beacon 
   URL : https://github.com/jmleglise/mylittle-domoticz/edit/master/Presence%20detection%20%28beacon%29/test_beacon.py
   Version : 1.0

 Copyright (c) 2017 Diving-91 (User:diving91 https://www.jeedom.fr/forum/)
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
 python ble.py hciAdapterID phpCallback jsonTagsBDaddr &
	Example: sudo python ble.py 0 BTdaemon.php [\"EF:A2:C5:EB:A3:2F\",\"FF:FE:8A:40:FA:97\"]
 python ble.py kill
	This will kill the previously launched background process
'''

import os
import sys
import struct
import logging
import json
import bluetooth._bluetooth as bluez
import time
import signal

LE_META_EVENT = 0x3e
OGF_LE_CTL=0x08
OCF_LE_SET_SCAN_ENABLE=0x000C
EVT_LE_CONN_COMPLETE=0x01
EVT_LE_ADVERTISING_REPORT=0x02

TAG_DATA = [] # Example [["EF:A2:C5:EB:A3:2F",0],["FF:FE:8A:40:FA:97",0]] - [bdaddr , timestamp last seen] - imported from argv[3]

# IMPORTANT -> choose between DEBUG (log every information) or CRITICAL (only error)
#logLevel=logging.DEBUG
logLevel=logging.CRITICAL
FORMAT = '%(asctime)s - %(message)s'
logging.basicConfig(format=FORMAT,level=logLevel)

def packed_bdaddr_to_string(bdaddr_packed):
	return ':'.join('%02x'%i for i in struct.unpack("<BBBBBB", bdaddr_packed[::-1]))

def hci_toggle_le_scan(sock, enable):
	cmd_pkt = struct.pack("<BB", enable, 0x00)
	bluez.hci_send_cmd(sock, OGF_LE_CTL, OCF_LE_SET_SCAN_ENABLE, cmd_pkt)

me = os.path.basename(__file__)
#logging.debug('Start %s scanner'%(me))
# ARG1: Kill BLE scanner or check hci adapter
if sys.argv[1:]:
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
else: # no argv[1], assume no hci adapter
	logging.critical('ERROR - NO HCI adapter number supplied')
	sys.exit(1)	

# ARG2: Check php script callback
if sys.argv[2:]:
	callback=os.path.dirname(os.path.abspath(__file__))+"/"+str(sys.argv[2])
	if os.path.exists(callback):
		callback = sys.argv[2]
		logging.debug('Will use %s as php script callback',callback)
	else:
		logging.critical('ERROR - Wrong php script file name supplied: %s'%(callback))
		sys.exit(1)
else: # no argv[2], no php callback
	logging.critical('ERROR - No php script file name supplied')
	sys.exit(1)

# ARG3: json BLE TAGs mac address
if sys.argv[3:]:
	tags = json.loads(sys.argv[3])
	for tag in tags:
		TAG_DATA.append([tag.encode('ascii', 'ignore'),0])
	logging.debug('Will scan %s tag(s) with bdaddr %s'%(sys.argv[3].count(":")/5,sys.argv[3]))
else: # no argv[3], no tags bdaddr
	logging.critical('ERROR - No Tags supplied')
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
# Infinite loop to lsiten socket
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
							os.system("php " + callback + " callback '" + jsonTag + "'") #call php callback
	sock.setsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, old_filter )
