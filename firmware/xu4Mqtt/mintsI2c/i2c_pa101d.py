import datetime
from datetime import timedelta
import logging
import smbus2
import struct
import time
import bme280
import math
import time
import pynmea2
from pa1010d import PA1010D
from mintsXU4 import mintsSensorReader as mSR
from mintsXU4 import mintsDefinitions as mD


from collections import OrderedDict

class PAI101D_:

    def __init__(self, i2c_dev,debugIn):
        
        self.gps = PA1010D(debug= debugIn)
        self.gps._i2c = i2c_dev

    def initiate(self):
        try:
            time.sleep(1)

            self.gps.update(timeout=5)

            print("Reading only RMC and GGA Commands")
            self.gps.send_command("PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")

            print("Sending to Full Power Mode")
            # self.gps.send_command("$PMTK161,0*28")
            self.gps.send_command("$PMTK225,0*2B")

            time.sleep(1)

            return self.gps.gps_qual is not None;
        except OSError:
            return False
            pass

    def readSentence(self,strExpected, timeOut=2):
        print("Setting PA101D to normal")
        self.gps.send_command("$PMTK225,0*2B")
        timeOut += time.time()
        while time.time() < timeOut:
            try:
                sentence = self.gps.read_sentence()
                print(sentence)
                if sentence.find(strExpected) >0:
                    # self.gps.send_command("$PMTK161,0*28")
                    return sentence;                
            except TimeoutError:
                continue
        # print("Setting PA101D to low power mode")
        #self.gps.send_command("$PMTK161,0*28")
        return;

    def getLatitudeCords(self,latitudeStr,latitudeDirection):
        latitude = float(latitudeStr)
        latitudeCord      =  math.floor(latitude/100) +(latitude - 100*(math.floor(latitude/100)))/60
        if(latitudeDirection=="S"):
            latitudeCord = -1*latitudeCord
        return latitudeCord

    def getLongitudeCords(self,longitudeStr,longitudeDirection):
        longitude = float(longitudeStr)
        longitudeCord      =  math.floor(longitude/100) +(longitude - 100*(math.floor(longitude/100)))/60
        if(longitudeDirection=="W"):
            longitudeCord = -1*longitudeCord
        return longitudeCord

    def readMqtt(self,strExpected, timeOut=2):
        # print("Setting PA101D to normal")
        # self.gps.send_command("$PMTK225,0*2B")
        timeOut += time.time()
        while time.time() < timeOut:
            try:
                dataString = self.gps.read_sentence()
                print(dataString)

                if dataString.find(strExpected) >0:
                    dateTime  = datetime.datetime.now()
                    dataStringPost = dataString.replace('\n', '')
                    sensorData = pynmea2.parse(dataStringPost)
                    if strExpected == "GGA":
                        if(sensorData.gps_qual>0):
                            sensorName = "GPSGPGGA2"
                            sensorDictionary = OrderedDict([
                                    ("dateTime"          ,str(dateTime)),
                                    ("timestamp"         ,str(sensorData.timestamp)),
                                    ("latitudeCoordinate" ,self.getLatitudeCords(sensorData.lat,sensorData.lat_dir)),
                                    ("longitudeCoordinate",self.getLongitudeCords(sensorData.lon,sensorData.lon_dir)),
                                    ("latitude"          ,sensorData.lat),
                                    ("latitudeDirection" ,sensorData.lat_dir),
                                    ("longitude"         ,sensorData.lon),
                                    ("longitudeDirection",sensorData.lon_dir),
                                    ("gpsQuality"        ,sensorData.gps_qual),
                                    ("numberOfSatellites",sensorData.num_sats),
                                    ("HorizontalDilution",sensorData.horizontal_dil),
                                    ("altitude"          ,sensorData.altitude),
                                    ("altitudeUnits"     ,sensorData.altitude_units),
                                    ("undulation"        ,sensorData.geo_sep),
                                    ("undulationUnits"   ,sensorData.geo_sep_units),
                                    ("age"               ,sensorData.age_gps_data),
                                    ("stationID"         ,sensorData.ref_station_id)
                                ])

                            #Getting Write Path
                            mSR.sensorFinisher(dateTime,sensorName,sensorDictionary)
                    if strExpected == "RMC":
                        if(sensorData.status=='A'):
                            sensorName = "GPSGPRMC2"
                            sensorDictionary = OrderedDict([
                                    ("dateTime"             ,str(dateTime)),
                                    ("timestamp"            ,str(sensorData.timestamp)),
                                    ("status"               ,sensorData.status),
                                    ("latitudeCoordinate"   ,self.getLatitudeCords(sensorData.lat,sensorData.lat_dir)),
                                    ("longitudeCoordinate"  ,self.getLongitudeCords(sensorData.lon,sensorData.lon_dir)),
                                    ("latitude"             ,sensorData.lat),
                                    ("latitudeDirection"    ,sensorData.lat_dir),
                                    ("longitude"            ,sensorData.lon),
                                    ("longitudeDirection"   ,sensorData.lon_dir),
                                    ("speedOverGround"      ,sensorData.spd_over_grnd),
                                    ("trueCourse"           ,sensorData.true_course),
                                    ("dateStamp"            ,sensorData.datestamp),
                                    ("magVariation"         ,sensorData.mag_variation),
                                    ("magVariationDirection",sensorData.mag_var_dir)
                                    ])
                            #Getting Write Path
                            mSR.sensorFinisher(dateTime,sensorName,sensorDictionary)

            except TimeoutError:
                continue
        return;