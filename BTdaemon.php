<?php
/*
* Copyright (c) 2017 Diving-91 (User:diving91 https://www.jeedom.fr/forum/)
*
* MIT License
* Copyright (c) 2017 
*
* Permission is hereby granted, free of charge, to any person obtaining a copy
* of this software and associated documentation files (the "Software"), to deal
* in the Software without restriction, including without limitation the rights
* to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
* copies of the Software, and to permit persons to whom the Software is
* furnished to do so, subject to the following conditions:
*
* The above copyright notice and this permission notice shall be included in
* all copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
* IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
* FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
* AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
* LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
* OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
* SOFTWARE.
*
*/

/*
* Class BTScanner purpose: Scan Bluetooth devices on the network and notify a controller when registered devices are in range
*	Controller is any system having an http API to settle devices ON & OFF
*	Primary controller configured with this script is Jeedom - but it can easily be adapted
*	Jeedom http API is used to control BTtag widgets
*	This script can run either on the same Raspberry PI as Jeedom or on another Raspberry PI allowing to have the BT adapter placed anywhere in the house
*	This script is intended to run in CLI mode as a background daemon (via pcntl_fork())
*
*	Configuration:
*	Debug mode is selected when an instance of this class is created $bt = new BTScanner(debug_mode)
*	It is adviced to start in debug mode to check evything is fine, then turn debug off
*
*	Tested with:
*	Raspberry PI 2 - Raspian Jessie / Should be Ok for PI 3 with built-in Bluetooth as well
*	BT devices: Samsung Galaxy S5 & LG G3 & iPhone 6s
*	Bluetooth adapter: https://goo.gl/e52VTZ
*
*/
class BTScanner {
	private $_logfile = 'BT.log';
	private $_loglength = 50;	// Max log size in lines
	private $_cfgfile = 'BT.ini';
	// from cfgfile
	private $_adapter; 		// BT adapter eg: hci0
	private $_jeedomurl;		// Base URL jeedom API 
	private $_log;			// Boolean to log BT ativity in $_logfile
	private $_tags;			// Array of BT tags with the parameter BT MAC,Jeedom CmdON,Jeedom CmdOFF

	private $_hcitool;		// Path to hcitool
	
	private $_loopTime = 2;		// BT scan loop time
	private $_debug;		// For debug purpose - Settled at Class construct time

	public function __construct($debug = false) {
		$this->_debug = $debug;
	}

	public function run() {
		pcntl_signal(SIGCHLD, SIG_IGN);
		$pid = pcntl_fork();
		if($pid == -1) {
			echo "ERROR FORK MAIN\n";
		}
		else if($pid) {
			// This is the main parent process
			// Nothing to do. Will be killed with stop() method
			// Once forked, Every _loopTime, Bluetooth scan is performed
			exit(0);
		}
		else {	// Forked process
			$this->dbg("children - ".getmypid()."\n");
			while (true) {
				foreach ($this->_tags as $key=>$device) {
					$x = exec("sudo $this->_hcitool -i $this->_adapter name $key");
					if (empty($x) and $device['state'] == true) {
						$this->callJedoomUrl($device['off']);
						$this->_tags[$key]['state'] = false;
						$this->dbg("Inactive Tag found: $key\n");
						$this->log("$key inactive\n");
					}
					else if (!empty($x) and $device['state'] == false) {
						$this->callJedoomUrl($device['on']);
						$this->_tags[$key]['state'] = true;
						$this->dbg("Active Tag found: $key\n");
						$this->log("$key ACTIVE\n");
					}
				}
				sleep($this->_loopTime);
			}
		}
	}

	public function stop() {
		$me = ltrim(__FILE__,__DIR__); // name of this file
		exec('ps aux | grep "php $me" | grep -v grep | awk \'{print $2}\'',$pidList); // all Daemon processes
		$mypid = array(getmypid()); // this process
		$pidList = array_diff($pidList,$mypid); // all processes but current one
		foreach ($pidList as $pid) {
			posix_kill($pid, SIGKILL);
			echo "Kill Bluetooth Daemon $pid\n";
		}
	}

	// Check config file exists and loads config parameters
	public function checkAndLoadConfig() {
		$this->dbg("Check config file exists\n");
		$me = ltrim(__FILE__,__DIR__); // name of this file
		if (!file_exists($this->_cfgfile)) {die("ERROR No config file, use: php $me conf\n");}	
		else $this->loadConfig();
	}

	// Generate config file 
	public function config() {
		$handle = fopen($this->_cfgfile, 'w');
		// Select Adapter Number
		do {
			$loop = false;
			echo "Select hci adapter (0,1,2,...): ";
			$r = $this->readline();
			if (!ctype_digit($r)) {
				echo "ERROR: Bad adapter number\n";
				$loop = true;
			}
		} while ($loop);
		$str = "[adapter]\nhci = hci$r\n";
		fwrite($handle,$str);
		// Select Jeedom IP
		do {
			$loop = false;
			echo "Select Jeedom IP (x.y.z.w): ";
			$r = $this->readline();
			if(!filter_var($r, FILTER_VALIDATE_IP,FILTER_FLAG_IPV4)){
				echo "ERROR: Bad IP address\n";
				$loop = true;
			}
		} while ($loop);
		$str = "[Jeedom IP]\nip = $r\n";
		fwrite($handle,$str);
		// Select Jeedom API key
		echo "Select Jeedom API key: ";
		$r = $this->readline();
		$str = "[Jeedom Key]\nkey = $r\n";
		fwrite($handle,$str);
		// Select iTag parameters
		$str = "[TAGS]\n";
		$tag = 1;
		do {
			// Select iTag BT Mac
			do {
				$loop = false;
				echo "Select iTag BT MAC: ";
				$r = $this->readline();
				if(!filter_var($r, FILTER_VALIDATE_MAC)){
					echo "ERROR: Bad iTag BT MAC address\n";
					$loop = true;
				}
			} while ($loop);
			$str .= $tag." = ".strtoupper($r);
			// Select Jeedom cmd id ON
			do {
				$loop = false;
				echo "Select Jeedom cmd id ON (0,1,2,...): ";
				$r = $this->readline();
				if (!ctype_digit($r)) {
					echo "ERROr: Bad Jeedom cmd id ON\n";
					$loop = true;
				}
			} while ($loop);
			$str .= ",".$r;
			// Select Jeedom cmd id OFF
			do {
				$loop = false;
				echo "Select Jeedom cmd id OFF (0,1,2,...): ";
				$r = $this->readline();
				if (!ctype_digit($r)) {
					echo "ERROr: Bad Jeedom cmd id OFF\n";
					$loop = true;
				}
			} while ($loop);
			$str .= ",".$r."\n";
			// More iTags ?
			echo "Enter another iTag ? (yes/no): ";
			$r = $this->readline();
			if(filter_var($r, FILTER_VALIDATE_BOOLEAN)) {
				$loop = true;
			}
			else {
				$loop = false;
			}
			$tag++;
		} while ($loop);
		fwrite($handle,$str);
		// Select logs
		echo "Activate logs ? (yes/no): ";
		$r = $this->readline();
		if(filter_var($r, FILTER_VALIDATE_BOOLEAN)){
			$str = "[logs]\nlog = 1";
		}
		else {
			$str = "[logs]\nlog = 0";
		}
		fwrite($handle,$str);
		fclose($handle);
	}

	// Load parameters from cfgfile 
	private function loadConfig() {
		$this->dbg("Load config file\n");
		$handle = fopen($this->_cfgfile, 'r');
		$config = parse_ini_file($this->_cfgfile,true);
		fclose($handle);

		$this->_adapter = $config['adapter']['hci'];
		// http://192.168.1.xxx/core/api/jeeApi.php?apikey=yourkey&type=cmd&id=77
		$this->_jeedomurl = "http://".$config['Jeedom IP']['ip']."/core/api/jeeApi.php?apikey=".$config['Jeedom Key']['key']."&type=cmd&id=";
		$this->_log =$config['logs']['log']; 
		// For each tag array[mac] = array(ID on, ID Off, State) - State by default set to false
		foreach ($config['TAGS'] as $tag) {
			$tagData = explode(",",$tag);
			$this->_tags[$tagData[0]] = array("on" => $tagData[1], "off" => $tagData[2],"state" => false);
		}
		$nbTags = count($this->_tags);
		$this->dbg("Adapter: $this->_adapter\n");
		$this->dbg("Jeedom base url: $this->_jeedomurl\n");
		$this->dbg("logs: $this->_log\n");
		$this->dbg("Amount of BT tags: $nbTags\n");

		$this->dbg("Check Bluetooth Software & Hardware\n");
		$this->checkHCI($this->_adapter);
	}

	// Call Jeedom specified URL
	private function callJedoomUrl($id) {
		//echo "$this->_jeedomurl"."$id\n";
		$r = file_get_contents("$this->_jeedomurl"."$id");
		if (!empty($r)) { $this->dbg("URL call ERROR: $r\n"); }
		else { $this->dbg("URL call succesfully for ID: $id\n"); }
	}

	// Check Bluetooth Software and Hardware is well installed and configured
	private function checkHCI($adapter) {
		// Check hcitool is installed - sudo apt-get install bluetooth
		$hciconfig = exec('which hciconfig');
		if (empty($hciconfig)) {die("ERROR bluetooth not install, use: sudo apt-get install bluetooth\n");}
		$this->dbg("Found hciconfig: $hciconfig\n");
		$this->_hcitool = exec('which hcitool');
		$this->dbg("Found hcitool: $this->_hcitool\n");
		// Check an adapter/dongle is present 
		exec("sudo $this->_hcitool dev",$r);
		if (empty($r[1])) {die("ERROR, no bluetooth adapter found: You need to install an adapter\n");}
		$this->dbg("Bluetooth adapter found\n");
		//$this->dbg(print_r($r,true));
		// Check specific $adapter adapter is up and running - sudo hciconfig hci0 up
		unset($r);
		exec("$hciconfig -a $adapter",$r);
		//$this->dbg(print_r($r,true));
		if (@trim($r[2]) != "UP RUNNING") {die("ERROR $adapter adapter not running, use: sudo hciconfig $adapter up\n");}
		$this->dbg("Bluetooth adapter UP & RUNNING\n");
	}

	// Read stdin
	private function readline() {
		return rtrim(fgets(STDIN));
	}

	// Log message
	private function log($str) {
		if ($this->_log) {
			$handle = fopen($this->_logfile, 'a');
			fwrite($handle,date('Y-m-d H:i:s')." - ".$str);
			fclose($handle);
			// keep only last _loglength logs lines
			$r = exec("wc -l < $this->_logfile");
			if ($r > $this->_loglength) {
				$this->dbg("Reducing Log Size to $this->_loglength events\n");
				exec("tail -$this->_loglength $this->_logfile > /tmp/myownBT.log");
				exec("mv /tmp/myownBT.log $this->_logfile");
			}
		}
	}

	// Debug message
	private function dbg($str) {
		if ($this->_debug) echo $str;
	}
}

/* 
	Main Bluetooth Daemon script
*/

function usage() {
	$me = ltrim(__FILE__,__DIR__); // name of this file
	echo "Bluetooth Daemon Usage:\n";
	echo "php $me start -> Start Daemon\n";
	echo "php $me stop -> Stop Daemon\n";
	echo "php $me conf -> Config Daemon\n";
}

// START of MAIN
if (php_sapi_name() == 'cli') {
	$bt = new BTScanner(false); //true for debug mode, else false
	if (isset($argv[1])) { $arg=$argv[1]; }
	else {
		usage();
		exit;
	}
	if ($arg == 'start') {
		$bt->stop();
		$bt->checkAndLoadConfig();
		echo "Starting Bluetooth Daemon\n";
		$bt->run();
		}
	else if ($arg == 'stop') {
		echo "Stopping Bluetooth Daemon\n";
		$bt->stop();
		echo "Bluetooth Daemon Stopped\n";
	}
	else if ($arg == 'conf') {
		echo "Configuring Bluetooth Daemon\n";
		$bt->config();
		echo "Bluetooth Daemon Configured\n";
	}
	else {		
		usage();
		exit;
	}
}
else echo "<h1>Can't run in Browser</h1>";
?>
