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
    # The entire point of this function is to get around the fact that
    # macOS doesn't have a really good way to set a universal path for
    # all users in a launchd plist file.

    # Must make the IDE happy and stop warning me about possible
    # reference before assignment.
    homePath = ""
    logPath = ""

    if 'HOME' in os.environ:
        homePath = os.environ['HOME']
        if len(homePath) > 0:
            if homePath[-1] != "/":
                homePath = homePath + "/"

            homePath = homePath + ".config/piaNetworkTest/"
            logPath = homePath + "Library/Logs/"

    # If there is no home path, there clearly won't be a viable log path
    # so we need to set both.  If nothing else, we'll use the script
    # directory.
    if len(homePath) < 1:
        homePath = os.path.abspath(os.path.dirname(sys.argv[0]))
        logPath = homePath

    return homePath, logPath

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

def logOutput(logData, logFile):
    """Accepts a list of string to output to the log file."""
    file = open(logFile, "a")
    file.writelines(logData)
    file.close()

def dataOutput(data, fileName):
    """Accepts some string data to output to a file. """
    file = open(fileName, "w")
    file.write(data)
    file.close()

def dataInput(fileName):
    """Reads a line of data from a file and returns it as a string."""
    if os.path.isfile(fileName):
        file = open(fileName, "r")
        result = file.read()
    else:
        result = ""

    return result

def main():
    # Set a reasonable path for the script to store stuff.
    home, log = setHomePath()

    # Filenames for where we're going to put stuff.
    outputLog = log + "piaNetworkTest.log"
    lastNetworkFile = home + "networkLast.txt"
    trustedNetworkFile = home + "trustedNetworks.txt"
    vpnLastChangeFile = home + "vpnLastChange.txt"



main()