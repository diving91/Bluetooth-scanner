# Bluetooth-scanner
BT (LE or not) scanner for Jeedom automation Framework

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
It is adviced to start in debug mode to check evything is fine, then turn debug off<br/>
BT LE or normal BT is defined with 'scan' or 'lescan' in $_scanType private variable<br/>

*	Tested with:<br/>
Raspberry PI 2 - Raspian Jessie<br/>
BT LE tags: https://goo.gl/KoQUb3<br/>
BT non LE device: Samsung Galaxy S5<br/>
Bluetooth adapter: https://goo.gl/e52VTZ<br/>

* Link with the controller<br/>
Define a widget with on & off cmd IDs to control the widget via Jeedom http API<br/>
When started in configuration mode, the script will ask for the list of BT devices to monitor (via their BT Mac address)<br/>
For each registered BT devices, the IDs for on & off jeedom cmd will be asked and stored into a BLE.ini file<br/>

* Optionally a log file is generated to keep track of devices entering or levaing the adapter scan range<br/>

* More information via Jeedom forum<br/>
User: diving91<br/>


