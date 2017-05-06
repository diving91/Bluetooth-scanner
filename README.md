# Bluetooth-scanner
BT (LE or not) scanner for Jeedom home automation Framework

* Class BLE purpose: Scan Bluetooth devices on the network and notify a controller when registered devices are in range<br/>

Can work with Bluetooth LE OR non LE devices (but not both at same time)<br/>
Controller is any system having an http API to settle devices ON & OFF<br/>
Primary controller configured with this script is Jeedom - but it can easily be adapted<br/>
Jeedom http API is used to control tag widgets<br/>
This script can run either on the same Raspberry PI as Jeedom or on another Raspberry PI allowing to have the BT adapter placed anywhere in the house<br/>
This script is intended to run in CLI mode as a background daemon (via pcntl_fork())<br/>
$ php BLEDaemon.php<br/>

*	Configuration:<br/>
Debug mode is selected when an instance of this class is created $ble = new BLE(debug_mode)<br/>
It is advised to start in debug mode to check everything is fine, then turn debug off<br/>
BT LE or normal BT is defined with 'scan' or 'lescan' in $_scanType private variable<br/>

*	Tested with:<br/>
Raspberry PI 2 - Raspbian Jessie<br/>
BT LE tags: https://goo.gl/KoQUb3 (Work in Progress)<br/>
BT devices: Samsung Galaxy S5, LG G3, iPhone 6s<br/>
Bluetooth adapter: https://goo.gl/e52VTZ<br/>

* Link with the controller<br/>
Define a widget with on & off cmd IDs to control the widget via Jeedom http API<br/>
When started in configuration mode, the script will ask for the list of BT devices to monitor (via their BT Mac address)<br/>
For each registered BT devices, the IDs for on & off Jeedom cmd will be asked and stored into a BLE.ini file<br/>

* Optionally a log file is generated to keep track of devices entering or leaving the adapter scan range<br/>

* More information via Jeedom forum (French Forum)<br/>
https://www.jeedom.com/forum/viewtopic.php?f=31&t=25492<br/>
User: diving91<br/>

<img src=https://github.com/diving91/Bluetooth-scanner/blob/master/images/noITAG.png> <img src=https://github.com/diving91/Bluetooth-scanner/blob/master/images/onNut.png> <img src=https://github.com/diving91/Bluetooth-scanner/blob/master/images/offNut.png> <img src=https://github.com/diving91/Bluetooth-scanner/blob/master/images/onPhone.png> <img src=https://github.com/diving91/Bluetooth-scanner/blob/master/images/offPhone.png>
