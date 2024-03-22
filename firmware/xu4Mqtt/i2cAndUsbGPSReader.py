
# MQTT Client demo
# Continuously monitor two different MQTT topics for data,
# check if the received data matches two predefined 'commands'
import itertools
import base64
from cgitb import strong
# import imp
# from this import d
import paho.mqtt.client as mqtt
import datetime 
from datetime import timedelta
import yaml
import collections
import json
import time 
import serial.tools.list_ports
from collections import OrderedDict
from glob import glob
from mintsXU4 import mintsDefinitions as mD
from mintsXU4 import mintsSensorReader as mSR

# from mintsXU4 import mintsPoLo as mPL
from collections import OrderedDict
import struct
import numpy as np
import pynmea2
import shutil

#import SI1132
from mintsI2c.i2c_bme280   import BME280
from mintsI2c.i2c_scd30    import SCD30
from mintsI2c.i2c_as7265x  import AS7265X
from mintsI2c.i2c_pa101d   import PAI101D_


import math
import sys
import time
import os
import smbus2






debug  = False 


dataFolder = mD.dataFolder
gpsPort    =  mD.USBGPSPort
baudRate  = 9600



bus     = smbus2.SMBus(1)

scd30   = SCD30(bus,debug)
bme280  = BME280(bus,debug)
as7265x = AS7265X(bus,debug)
pa101d  = PAI101D_(bus,debug)

reader = pynmea2.NMEAStreamReader()


lastGPRMC = time.time()
lastGPGGA = time.time()
lastGNRMC = time.time()
lastGNGGA = time.time()
delta  = 10
#this will store the line
line = []



def is_serial_port_open(port):
    try:
        # Attempt to open the serial port
        ser = serial.Serial(
        port= port,\
        baudrate=baudRate,\
        parity  =serial.PARITY_NONE,\
        stopbits=serial.STOPBITS_ONE,\
        bytesize=serial.EIGHTBITS,\
        timeout=0)
        print("connected to: " + ser.portstr)
        # If successfully opened, close the port and return True
        return True, ser
    except serial.SerialException:
        # If an exception occurs (port is not available or already open), return False
        ser = []
        return False, ser




if __name__ == "__main__":
    
    print()
    print("============ MINTS I2C + USB GPS Reader ============")
    print()
    

    usbGPSAvailability,serialConnection  = is_serial_port_open(gpsPort[0])

    # I2C Devices 
    as7265xOnline  =  as7265x.initiate()
    as7265xReadTime  = time.time()

    bme280Online   =  bme280.initiate(30)
    bme280ReadTime  = time.time()

    scd30Online    =  scd30.initiate(30)
    scd30ReadTime  = time.time()
    
    pa101dOnline   =  pa101d.initiate()
    pa101dGGAReadTime  = time.time()
    pa101dRMCReadTime  = time.time()    


    while True:
        try:
            if usbGPSAvailability:
                try:       
                    for c in serialConnection.read():
                        line.append(chr(c))
                        if chr(c) == '\n':
                            dataString     = (''.join(line)).split('\r')[0]
                            # print(dataString)
                            dateTime  = datetime.datetime.now()
                            if (dataString.startswith("$GPGGA") and mSR.getDeltaTime(lastGPGGA,delta)):
                                mSR.GPSGPGGA2Write(dataString.split('\r')[0],dateTime)
                                lastGPGGA = time.time()
                            if (dataString.startswith("$GPRMC") and mSR.getDeltaTime(lastGPRMC,delta)):
                                mSR.GPSGPRMC2Write(dataString.split('\r')[0],dateTime)
                                lastGPRMC = time.time()
                            if (dataString.startswith("$GNGGA") and mSR.getDeltaTime(lastGNGGA,delta)):
                                mSR.GPSGPGGA2Write(dataString.split('\r')[0],dateTime)
                                lastGNGGA = time.time()
                            if (dataString.startswith("$GNRMC") and mSR.getDeltaTime(lastGNRMC,delta)):
                                mSR.GPSGPRMC2Write(dataString.split('\r')[0],dateTime)
                                lastGNRMC = time.time()                    
                            line = []
                            break
                except Exception as e:
                    time.sleep(.5)
                    line = []
                    print ("USB GPS Error and type: %s - %s." % (e,type(e)))
                    print("Errornous String")
                    print(dataString)
                    print("+=+=+=+=+=+=+=+=")
                    time.sleep(.5)
        
                              
            if as7265xOnline and mSR.getDeltaTimeAM(as7265xReadTime,delta):
                as7265xReadTime  = time.time()
                as7265x.readMqtt();
            
            if pa101dOnline and mSR.getDeltaTimeAM(pa101dGGAReadTime,delta):
                pa101dGGAReadTime  = time.time()
                print("---GGA---")
                pa101d.readMqtt("GGA");                  
         
            if bme280Online and mSR.getDeltaTimeAM(bme280ReadTime,delta):
                bme280ReadTime  = time.time()                
                bme280.readMqtt();
            
            if pa101dOnline and mSR.getDeltaTimeAM(pa101dRMCReadTime,delta):
                pa101dRMCReadTime  = time.time()
                print("---RMC---")
                pa101d.readMqtt("RMC");               
            
            if scd30Online and mSR.getDeltaTimeAM(scd30ReadTime,delta):
                scd30.readMqtt();
                scd30ReadTime  = time.time()

       

        except Exception as e:
            time.sleep(.5)
            print ("Error and type: %s - %s." % (e,type(e)))
            time.sleep(.5)
        
                  
        
        
        

        
        
        
        
        