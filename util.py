#!/usr/bin/python
''' Check python-bluez is installed on this system
 Copyright (c) 2017 Diving-91 (User:diving91 https://www.jeedom.fr/forum/)
 MIT License
 URL: https://github.com/diving91/Bluetooth-scanner
 Version : 1.0
 '''
import sys

try:
	import bluetooth._bluetooth
	print "ok"
except:
	print "ko"
	sys.exit(4)

sys.exit(0)