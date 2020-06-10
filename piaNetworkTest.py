#!/usr/bin/env python3
"""This script endeavours to allow automated control of the Private
Internet Access (PIA) VPN interface by allowing the system to
automatically decide if it should activate the VPN based on factors
such as what network it is connected to.
"""

import sys, os, subprocess, netifaces
from wireless import Wireless
from datetime import datetime

pingAddress = "8.8.8.8" # The default is to use the Google DNS Server
pingCMD = "/sbin/ping"
piaCMD = "/usr/local/bin/piactl"

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

def runCMD(cmdList):
    """Runs a command specified by a List variable and returns the exit
    code as well as the output, decoded to a normal string.
    """
    data = subprocess.run(cmdList, capture_output=True)
    return data.stdout.decode(), data.returncode

def checkInternet():
    """Will ping a network address to determine if the Internet is
    online or not, returns True or False.
    """
    result = False
    ping = [pingCMD, "-c", "1"]
    text, test = runCMD(ping)

    if test == 0:
        result = True

    return result

def vpnCheck():
    """Simply checks to see the status of the VPN returning int -1 to 2.
    -1 for Error
    0 for Disconnected
    1 for Connected
    2 for Connecting
    """
    pia = [piaCMD, "get", "connectionstate"]
    data, ex = runCMD(pia)

    if data == "Disconnected":
        result = 0
    elif data == "Connected":
        result = 1
    elif data == "Connecting":
        result = 2
    else: # In the unlikely event that PIA returns something unknown.
        result = -1

    return result

def getNetwork():
    """Tries to discover the name of the current network, first the
    network interface but then the name of the WiFi network, if no
    WiFi network is present, it will return the name of the network
    interface.  If there is no default route and thus no Internet then
    it will return an empty string."""
    gws = netifaces.gateways()
    # Need to make sure the default route exists.
    if gws['default'] != {}:
        defaultGW = gws['default'][netifaces.AF_INET]
        currentNetwork = defaultGW[1]
    else: # If the above is true, there is no default route
        return ""

    # Now we need to check to see if we're on a WiFi network or not.
    w = Wireless()
    wName = w.current()
    if not wName is None:
        currentNetwork = wName

    return currentNetwork

def logOutput(logData, logFile):
    """Accepts a list of string to output to the log file."""
    # Should probably check, if the logData is empty, don't do anything.
    if len(logData) > 0:
        file = open(logFile, "a")
        file.writelines(logData)
        file.close()
        # We're going to treat the log data like a buffer so we can do
        # intermittent writes to the log.
        logData.clear()

def dataOutput(data, fileName):
    """Accepts some string data to output to a file. """
    file = open(fileName, "w")
    file.write(data)
    file.close()

def dataInput(fileName):
    """Reads a line of data from a file and returns either a string for
    when there is only a single line of data or a list when there is
    more than one line.
    """
    data = ""
    if os.path.isfile(fileName):
        file = open(fileName, "r")
        data = file.readlines()

    # Turn the raw data into something usable.
    result = data.splitlines()
    if len(result) < 1:
        result = ""
    elif len(result) == 1:
        result = result[0]

    return result

def main():
    # Set a reasonable path for the script to store stuff.
    home, log = setHomePath()
    logData = []

    # Filenames for where we're going to put stuff.
    outputLog = log + "piaNetworkTest.log"
    lastNetworkFile = home + "networkLast.txt"
    trustedNetworkFile = home + "trustedNetworks.txt"
    vpnLastChangeFile = home + "vpnLast.txt"

    lastNetwork = dataInput(lastNetworkFile)
    currentNetwork = getNetwork()

    # If the current and last network are the same, don't do anything.
    if currentNetwork == lastNetwork:
        sys.exit(0)

    # We're going to make some decisions on what to do about the VPN.
    connectVPN = True # Assume a VPN is needed.
    disconnectVPN = False # Assume we don't need to disconnect.

    # Now we want to mark the log with what time it is since we're doing
    # something.
    now = datetime.now()
    dt = now.strftime("%Y/%m/%d %H:%M:%S")
    logData.append(dt)
    logData.append("The network state has changed since last check.")
    logOutput(logData, outputLog)

    # Now we need to decide if there is Internet.
    vpnStat = vpnCheck() # What is the VPN doing?
    if currentNetwork == "":
        if vpnStat > 0:  # If the VPN still thinks we're online, fix it.
            disconnectVPN = True
        elif vpnStat < 0:  # If there was an error, get out of here.
            logData.append("Something went wrong with the VPN status check.")
            # This will ensure there won't be 100's of log entries
            # saying that there is an issue, in theory.
            dataOutput(currentNetwork, lastNetworkFile)
            logOutput(logData, outputLog)
            sys.exit(1) # There was a problem, so exit NOW.
    else:
        # Now what do we do if the network is live?
        # Check to see if we can Ping the Internet.
        haveInternet = checkInternet()
        if haveInternet:
            # Now we need to compare our network to trusted networks.
            trustedNets = dataInput(trustedNetworkFile)
            # We don't know how many entries, if any, are present so
            # we need to make sure what kind of data is returned.
            if type(trustedNets) is str:
                # If we have just 1 network, we need to turn it back into
                # a list for processing.
                trustedNets = [trustedNets]

            for name in trustedNets:
                if name == currentNetwork:
                    connectVPN = False
                    break # We're on a trusted network, stop checking.

        else: # If there is no Internet, drop the VPN.
            disconnectVPN = True

main()