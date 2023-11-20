
from getmac import get_mac_address

def findMacAddress():
    macAddress= get_mac_address(interface="eth0")
    if (macAddress!= None):
        return macAddress.replace(":","")

    macAddress= get_mac_address(interface="docker0")
    if (macAddress!= None):
        return macAddress.replace(":","")

    macAddress= get_mac_address(interface="enp1s0")
    if (macAddress!= None):
        return macAddress.replace(":","")

    macAddress= get_mac_address(interface="wlan0")
    if (macAddress!= None):
        return macAddress.replace(":","")

    return "xxxxxxxx"


dataFolder            = "/home/rxhf/mintsData/raw"
macAddress            = findMacAddress()



if __name__ == "__main__":
    # the following code is for debugging
    # to make sure everything is working run python3 mintsDefinitions.py 
    print("Mac Address    : {0}".format(macAddress))
    print("Data Folder    : {0}".format(dataFolder))

