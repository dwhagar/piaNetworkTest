#!/usr/bin/env python3
"""This script endeavours to allow automated control of the Private
Internet Access (PIA) VPN interface by allowing the system to
automatically decide if it should activate the VPN based on factors
such as what network it is connected to.
"""

import sys, os, subprocess

pingAddress = "8.8.8.8" # The default is to use the Google DNS Server
pingCMD = "/sbin/ping"

def setHomePath():
    """Sets a path for the script to store data files."""
    if 'HOME' in os.environ:
        homePath = os.environ['HOME']
        if len(homePath) > 0:
            if homePath[-1] != "/":
                homePath = homePath + "/"

            homePath = homePath + ".config/piaNetworkTest/"

    if len(homePath) < 1:
        homePath = os.path.abspath(os.path.dirname(sys.argv[0]))

    return homePath

def checkInternet():
    """Will ping a network address to determine if the Internet is
    online or not, returns True or False.
    """
    result = False
    ping = [pingCMD, "-c", "1"]
    test = subprocess.run(ping)

    if test.returncode == 0:
        result = True

    return result

def main():
    # Set a reasonable path for the script to store stuff.
    home = setHomePath()

    # Filenames for where we're going to put stuff.
    lastNetworkFile = home + "networkLast.txt"
    trustedNetworkFile = home + "trustedNetworks.txt"
    vpnLastChangeFile = home + "vpnLastChange.txt"



main()