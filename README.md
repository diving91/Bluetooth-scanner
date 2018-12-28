# Bluetooth device (BLE or not) scanner for Jeedom home automation Framework

* Class BTdaemon purpose: Scan Bluetooth devices on the network and notify a controller when registered devices are in range<br/>

Can work with Bluetooth LE (BLE) or normal (BT) devices<br/>
Controller is any system having an http API to settle devices ON & OFF<br/>
Primary controller configured with this script is Jeedom - but it can easily be adapted<br/>
Jeedom http API is used to control tag widgets<br/>
This script can run either on the same Raspberry PI as Jeedom or on another Raspberry PI allowing to have the BT adapter placed anywhere in the house<br/>
This script is intended to run in CLI mode as a background daemon (via pcntl_fork())<br/>
$ php BTdaemon.php<br/>

*	Configuration:<br/>
Debug mode is selected when an instance of this class is created $ble = new BLE(debug_mode)<br/>
It is advised to start in debug mode to check everything is fine, then turn debug off<br/>
$ php BTdaemon.php start -> Start daemon<br/>
$ php BTdaemon.php stop -> Stop daemon<br/>
$ php BTdaemon.php conf -> Start configuration of your Bluetooth devices and Jeedom API calls<br/>

*	Tested with:<br/>
Raspberry PI 2 - Raspbian Jessie<br/>
BLE devices: Nut mini (https://goo.gl/l36Gtz)<br/>
BT devices: Samsung Galaxy S5, LG G3, iPhone 6s<br/>
Does NOT work with iTags (https://goo.gl/ENNL71): Since those devices are switching off when not connected, they can't be used for presence detection<br/>
Bluetooth adapter: https://goo.gl/e52VTZ<br/>

* Link with the controller<br/>
Define a virtual with on & off cmd action IDs to control the widget via Jeedom http API<br/>
Also create a binary info field that will represent the state of the virtual (only this one is to be displayed) <br/>
<img src=https://github.com/diving91/Bluetooth-scanner/blob/master/images/jeedom%20virtual.jpg><br/>
In the advance configuration (toothed wheel) of the binary info field, use a binary widget with images for the on & off states (example below or any of your choice that you can also find on the jeedom market)<br/><br/>
When started in configuration mode, the script will ask for the list of Bluetooth devices to monitor (via their BT Mac address)<br/>
For each registered devices, the IDs for on & off Jeedom cmd will be asked and stored into a BLE.ini file<br/>


* Optionally a log file is generated to keep track of devices entering or leaving the adapter scan range<br/>

* More information via Jeedom forum (French Forum)<br/>
https://www.jeedom.com/forum/viewtopic.php?f=31&t=25492<br/>
User: diving91<br/>

<img src=https://github.com/diving91/Bluetooth-scanner/blob/master/images/noITAG.png> <img src=https://github.com/diving91/Bluetooth-scanner/blob/master/images/onNut.png> <img src=https://github.com/diving91/Bluetooth-scanner/blob/master/images/offNut.png> <img src=https://github.com/diving91/Bluetooth-scanner/blob/master/images/onPhone.png> <img src=https://github.com/diving91/Bluetooth-scanner/blob/master/images/offPhone.png>
