#!/usr/bin/env python3
"""This script endeavours to allow automated control of the Private
Internet Access (PIA) VPN interface by allowing the system to
automatically decide if it should activate the VPN based on factors
such as what network it is connected to.
"""

import sys, os, subprocess, netifaces
from pathlib import Path
from wireless import Wireless
from datetime import datetime, timedelta

pingAddress = "8.8.8.8" # The default is to use the Google DNS Server
pingCMD = "/sbin/ping"
piaCMD = "/usr/local/bin/piactl"
piaResetTime = 8 # Number of hours to stay disconnected before reset.

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

            logPath = homePath + "Library/Logs/"
            homePath = homePath + ".config/piaNetworkTest/"

    # If there is no home path, there clearly won't be a viable log path
    # so we need to set both.  If nothing else, we'll use the script
    # directory.
    if len(homePath) < 1:
        homePath = os.path.abspath(os.path.dirname(sys.argv[0]))
        logPath = homePath

    return homePath, logPath

def runCMD(cmdList):
    """Runs a command specified by a List variable and returns the exit
    code as well as the output, decoded to a normal string for a single
    line and a list of strings for multiple lines.
    """
    data = subprocess.run(cmdList, capture_output=True)

    # Parse the output to give either a list or a single string.
    output = data.stdout.decode().splitlines()
    if not output:
        output = ""
    elif len(output) == 1:
        output = output[0]

    return output, data.returncode

def checkInternet():
    """Will ping a network address to determine if the Internet is
    online or not, returns True or False.
    """
    result = False
    ping = [pingCMD, "-c", "1", pingAddress]
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

def vpnConnect():
    """Tell PIA to connect to the VPN."""
    runCMD([piaCMD, "connect"])

def vpnDrop():
    """Tell PIA to drop the VPN connection."""
    runCMD([piaCMD, "disconnect"])

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
        for line in logData:
            print(line) # We want to echo the log to the console for debugging.
            file.write(line)
            file.write(os.linesep)
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
    data = []
    if os.path.isfile(fileName):
        file = open(fileName, "r")
        data = file.readlines()
    else:
        # To make configuration easier, it creates emtpy files
        # If it cannot find them.
        file = open(fileName, "w")
        file.write(os.linesep)
        file.close()

    # Turn the raw data into something usable.
    if len(data) < 1:
        result = ""
    elif len(data) == 1:
        result = data[0]
    else:
        result = []
        for line in data:
            result.append(line.strip(os.linesep))

    return result

def checkTrusted(current, trustedFile):
    """Accepts a current network and a file listing of trusted networks
    and returns if the current network is trusted or not.
    """
    # Now we need to compare our network to trusted networks.
    trustedNets = dataInput(trustedFile)
    # We don't know how many entries, if any, are present so
    # we need to make sure what kind of data is returned.
    if type(trustedNets) is str:
        # If we have just 1 network, we need to turn it back into
        # a list for processing.
        if trustedNets == "":
            trustedNets = []
        else:
            trustedNets = [trustedNets]

    # Check our list of trusted networks against our current.
    if len(trustedNets) > 0:
        for name in trustedNets:
            if name == current:
                return True

    return False

def main():
    # Set a reasonable path for the script to store stuff.
    home, log = setHomePath()
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    logData = [now]

    # Create directories if needed.
    Path(home).mkdir(parents=True, exist_ok=True)
    Path(log).mkdir(parents=True, exist_ok=True)

    # Filenames for where we're going to put stuff.
    outputLog = log + "piaNetworkTest.log"
    lastNetworkFile = home + "networkLast.txt"
    trustedNetworkFile = home + "trustedNetworks.txt"
    vpnLastChangeFile = home + "vpnLast.txt"

    # Check out what happened in the past.
    lastNetwork = dataInput(lastNetworkFile)
    lastVPN = dataInput(vpnLastChangeFile)

    # If there is no previous lastVPN state, make it 0.
    if lastVPN == "":
        lastVPN = 0
    else:
        lastVPN = int(lastVPN)

    currentNetwork = getNetwork() # Are we on a network?
    vpnState = vpnCheck() # What is the VPN doing?

    # If the current and last network are the same, don't do anything.
    if currentNetwork == lastNetwork:
        # Now we're going to try to make sure to bring the VPN back up
        # if this is not a trusted network and it's been off for a
        # set amount of time.
        if currentNetwork != "":
            trusted = checkTrusted(currentNetwork, trustedNetworkFile)
            if lastVPN == vpnState:
                # Some stuff here to reconnect to the VPN if necessary.
                if not trusted and vpnState == 0:
                    lastVPNTime = os.path.getmtime(vpnLastChangeFile)
                    lastVPNTime = datetime.fromtimestamp(lastVPNTime)

                    # A wait time defined in number of hours.
                    wait = timedelta(hours=piaResetTime)
                    reconnectTime = lastVPNTime + wait
                    n = datetime.now()
                    # Now, if the last time the VPN changed plus the
                    # wait time is less is not in the future, we need
                    # to reconnect the VPN.
                    if reconnectTime <= datetime.now():
                        logData.append("More than " + str(piaResetTime) + " hours has elapsed since PIA was connected.")
                        logData.append("Connecting to PIA.")
                        vpnConnect()
                        dataOutput(str(vpnState), vpnLastChangeFile)
                        logOutput(logData, outputLog)
                        return
            else:
                # Store the new VPN state.
                dataOutput(str(vpnState), vpnLastChangeFile)

                # Decide on wording.
                if vpnState == 0:
                    vpn = "disconnected."
                elif vpnState == 1:
                    vpn = "connected."
                elif vpnState == 2:
                    vpn = "connecting."

                # Log the change.
                logData.append("The VPN state has changed, you are now " + vpn)
                logOutput(logData, outputLog)

        # If we end up with the networks the same, default to just
        # returning.
        return

    # We're going to make some decisions on what to do about the VPN.
    connectVPN = True # Assume a VPN is needed.
    disconnectVPN = False # Assume we don't need to disconnect.

    # Now we want to mark the log with what time it is since we're doing
    # something.
    logData.append("The network state has changed since last check.")
    logOutput(logData, outputLog)

    # Now we need to decide if there is Internet.
    if currentNetwork == "":
        logData.append("There is no network connection.")
        if vpnState > 0:  # If the VPN still thinks we're online, fix it.
            connectVPN = False
            disconnectVPN = True
        elif vpnState == 0: # There is no network and VPN is off
            connectVPN = False
            disconnectVPN = False
        else:  # If there was an error, get out of here.
            logData.append("Something went wrong with the VPN status check, exiting immediately.")
            # This will ensure there won't be 100's of log entries
            # saying that there is an issue, in theory.
            dataOutput(currentNetwork, lastNetworkFile)
            logOutput(logData, outputLog)
            sys.exit(1) # There was a problem, so exit NOW.
    else:
        # Now what do we do if the network is live?
        # Check to see if we can Ping the Internet.
        logData.append("We are connected to the network " + currentNetwork + ".")
        haveInternet = checkInternet()
        if haveInternet:
            logData.append("We are connected to the Internet.")
            # Now we need to compare our network to trusted networks.
            trusted = checkTrusted(currentNetwork, trustedNetworkFile)
            if trusted:
                connectVPN = False
                disconnectVPN = True
                logData.append("This network is trusted.")

        else: # If there is no Internet, drop the VPN.
            logData.append("While we have a network connection, the Internet is offline.")
            disconnectVPN = True

    # After we've decided what to do, save the network name so we know
    # when something has changed.
    dataOutput(currentNetwork, lastNetworkFile)

    # Lets just go ahead and save the log output right now.
    logOutput(logData, outputLog)

    # Now we change the VPN state if we have to.
    if disconnectVPN and vpnState > 0:
        logData.append("Disconnecting from PIA.")
        vpnDrop()
        dataOutput(str(vpnState), vpnLastChangeFile)
    # It is probably not necessary to be so explicate, just feels like
    # it could save debugging later for unexpected results.
    elif (not disconnectVPN) and connectVPN and vpnState < 1:
        logData.append("Connecting to PIA.")
        vpnConnect()
        dataOutput(str(vpnState), vpnLastChangeFile)

    # Assume everything went well and flush the log / exit.
    logOutput(logData, outputLog)

main()
sys.exit(0)