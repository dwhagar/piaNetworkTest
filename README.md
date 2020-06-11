# piaNetworkTest

The purpose of this script is to automatically control the Private Internet Access (PIA) VPN similarly to how the "Network Manager" phone feature controls the app.  It is designed for use on macOS but should work with minimal changes on Linux type platforms.  It may work on Windows, but file paths will have to change.

## Prerequisites

This script is written for use with python 3.7 and uses the `wireless` and `netifaces` libraries and they are required.  Other versions of python3 should work, I believe going back to 3.5 but I have not tested this.  I recommend installing Python3 with [Homebrew](https://brew.sh/).  You should be able to install Pythin3 by execiting:

```
$ brew install python3
```

Once Python is installed you can install the packages.  Note, I use `sudo -H` so that it installs the packages system-wide, I prefer this myself but I don't blieve it is required.

```
$ sudo -H pip3 install wireless netifaces
```

## Usage

The program will try to create a folder in your home folder under `.config` for files it needs.  If it cannot locate your home directory via the HOME variable it will use the scripts own directory to store files in.

### Files

`trustedNetworks.txt` contains a list (one network per line) of networks that are trusted or otherwise should have have PIA activated while using.  These can be either interface names (such as `en0`) or WiFi SSID names.  These networks will cause the script to disconnect from PIA when a network change is detected.

`networkLast.txt` contains the name of the last network the script saw and should not be changed by anything but the script.

`vpnLast.txt` contains the last state of the PIA VPN.  For those who wonder, a 0 means disconnected, a 1 means connected, and a 2 means connecting.

## Usage

When executed the script checks to see if the network has changed since it was last run.  If it has, it will look for the network on the trusted networks list and either connect or disconnect PIA depending on the current state of the connection.  If no network connection is found or the Internet is unreachable it will tell PIA to disconnect since PIA tends to try for quite a while when network connectivity is lost.

### Timer

There is also a default 8 hour timer.  Since the script only makes changes when a network change is detected (i.e. the network name changes) a person can connect and disconnect PIA as often as they need to and the program will largely ignore it until the network changes.  If PIA is left disabled on an untrusted network for more than a set time (default is 8 hours) the script will automatically reconnect to PIA again.

### Logging

Since this is designed for a Mac the script automatically logs to `~/Library/Logs` if it can find your home directory.  This can be changed in the script itself.

## Options

Configuration options are in the script except for the trusted networks list.  There are several variables at the top of the script that describe the paths for executables (such as the ping utility and the PIA control command) as well as what site is pinged to determine connectivity (defaults to Google's DNS server at `8.8.8.8` since it should always be online and reachable).

## PLIST File for Launchd

This script could be run by **cron** easily enough.  Since I'm making it on a Mac and I don't want it to run when I'm not actually logged in (the PIA control command requires the GUI to be up in most cases) I'm using Launchd and a PLIST file.  I've provided a sample here which can be easily modified.

```
<dict>
	<key>HOME</key>
	<string>/Users/cyclops</string>
	<key>PATH</key>
	<string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
</dict>

<key>Program</key>
<string>/Users/cyclops/Library/Mobile Documents/com~apple~CloudDocs/Scripts/piaNetworkTest.py</string>
```

Above are the two sections which need to be changed.  The string below the HOME key should be the full path to your home folder and will pass that on to the script.

Next the string under the Program key is the actual script location and should be set accordingly.

Launchd is not exactly the most forgiving tool but once set and working, it should never need to be touched again.
