# ***************************************************************************
#  mintsPM Corrections
#   ---------------------------------
#   Originial SW Written by: Prabuddha Dewage, 
#   Edited for live data streams on Mints systems by Lakitha Wijeratne
#   
#   Mints: Multi-scale Integrated Sensing and Simulation
#   
#   ---------------------------------
#   Date: June 11th, 2024
#   ---------------------------------
#   This module is written for MINTS Sensor systems, with the intention of 
#   particulate matter corrections due to percipitation and high humidity
#   --------------------------------------------------------------------------
#   https://github.com/mi3nts
#   http://utdmints.info/
#  ***************************************************************************


import pandas as pd 
from mintsXU4 import mintsSensorReader as mSR
from mintsXU4 import mintsDefinitions as mD
from collections import OrderedDict
import datetime
import joblib
import json

# For humidity correction
# In order to apply corrections, the sensor finisher code needs to be updated
#    1) The YAML file should have a Climate Sensor and a PM sensor - May be the model location
#    2) It needs to keep a record of the intended Climate sensor
#    3) It needs to have an updated sensor generate a copy of the updated data 
#    4) Add a couple of flags 
#        - Temperature validity 
#        - Dew Likelyhood
#        - Climate Data Current Validity


climateSensor     = mD.climateSensor
pmSensor          = mD.pmSensor
dataFolderTmp     = mD.dataFolderTmp
macAddress        = mD.macAddress
modelFile         = mD.modelFile
loaded_humidModel = joblib.load(modelFile)
    
def doPrediction(sensorID,sensorDictionary,dateTime):

    climateNullValidity     = 0
    climateDateTimeValidity = 0
    climateValidity         = 0
    humidityValidity        = 0
    dewPointValidity        = 0 
    mlValidity              = 0
 
    if sensorID ==  climateSensor:
        print("Climate data read")
        keepClimateData(dateTime,sensorID,sensorDictionary)

    if sensorID == pmSensor:
        print("-----------------------------------")
        print("------- Humidity Correction -------")
        # At this point load up the climate sensor 
        print("PM data read")
        dateTime        = dateTime
        climateData     = loadJSONLatestClimate(climateSensor)
        dateTimeClimate = datetime.datetime.strptime(climateData['dateTime'], "%Y-%m-%d %H:%M:%S.%f")

 

        pc0_1, pc0_3, pc0_5,\
            pc1_0, pc2_5, pc5_0, \
                pc10_0 = \
                        sensorDictionary['pc0_1'], sensorDictionary['pc0_3'], sensorDictionary['pc0_5'],\
                        sensorDictionary['pc1_0'], sensorDictionary['pc2_5'], sensorDictionary['pc5_0'], \
                        sensorDictionary['pc10_0']
        
        cor_pc0_1, cor_pc0_3, cor_pc0_5, \
            cor_pc1_0, cor_pc2_5, cor_pc5_0,\
                cor_pc10_0 \
                            =  float(pc0_1), float(pc0_3), float(pc0_5),\
                                float(pc1_0), float(pc2_5), float(pc5_0), \
                                    float(pc10_0) 

        pm0_1, pm0_3, pm0_5,\
            pm1_0, pm2_5, pm5_0, \
                pm10_0 = \
                        sensorDictionary['pm0_1'], sensorDictionary['pm0_3'], sensorDictionary['pm0_5'],\
                        sensorDictionary['pm1_0'], sensorDictionary['pm2_5'], sensorDictionary['pm5_0'], \
                        sensorDictionary['pm10_0']
        
        cor_pm0_1, cor_pm0_3, cor_pm0_5, \
            cor_pm1_0, cor_pm2_5, cor_pm5_0,\
                cor_pm10_0 \
                            =  pm0_1, pm0_3, pm0_5,\
                                pm1_0, pm2_5, pm5_0, \
                                    pm10_0 


        ml_pm2_5    = pm2_5
        
        temperature,humidity,pressure,dewPoint= -100,-100,-100,-100

        # Checking Validity 
        if climateData is not None:
            print("Climate data found")
            humidity, temperature, dewPoint, pressure =\
                    climateData['humidity'], climateData['temperature'], climateData['dewPoint'], climateData['pressure']
            climateNullValidity  = 1

            if is_valid_temperature(temperature) and is_valid_humidity(humidity):
                print("Climate Data is valid")
                climateValidity = 1
                if (dateTime-dateTimeClimate).total_seconds() < 300: 
                    print("Cimate date time is valid")
                    climateDateTimeValidity = 1
                    T_D = temperature - dewPoint
                    if humidity > 40:
                        humidityValidity = 1
                    if T_D < 2.5:
                        dewPointValidity = 1

        print("Validity Checks")
        if (climateNullValidity == 1 and 
            climateDateTimeValidity == 1 and 
            climateValidity == 1 and 
            humidityValidity == 1 and 
            dewPointValidity == 1):

            print("Obtaining Corrected Particle Counts")
            cor_pc0_1, cor_pc0_3, cor_pc0_5, \
                    cor_pc1_0, cor_pc2_5, cor_pc5_0,\
                        cor_pc10_0,\
                            humidity, temperature, dewPoint  = \
                                humidityCorrectedPC(\
                                    pc0_1, pc0_3, pc0_5, \
                                        pc1_0, pc2_5, pc5_0, \
                                            pc10_0, \
                                                humidity, temperature, dewPoint)
            
            cor_pm0_1, cor_pm0_3, cor_pm0_5, \
                cor_pm1_0, cor_pm2_5, cor_pm5_0, \
                    cor_pm10_0 =\
                                humidityCorrectedPM(cor_pc0_1, cor_pc0_3, cor_pc0_5,\
                                                        cor_pc1_0, cor_pc2_5, cor_pc5_0, \
                                                            cor_pc10_0)

            ml_pm2_5 ,mlValidity = \
                                mlCorrectedPM(temperature,humidity,pressure,dewPoint,\
                                            cor_pm2_5)
        
        # At this point you generate the final ordered dictionary to  be published
        # check = round(cor_pc0_1)
        # print(check)
        sensorDictionary = OrderedDict([
                    ("dateTime"                 ,str(dateTime)), # always the same
                    ("pc0_1"                    ,round(cor_pc0_1)), 
                    ("pc0_3"                    ,round(cor_pc0_3)),
                    ("pc0_5"                    ,round(cor_pc0_5)),
                    ("pc1_0"                    ,round(cor_pc1_0)),
                    ("pc2_5"                    ,round(cor_pc2_5)),
                    ("pc5_0"                    ,round(cor_pc5_0)), 
                    ("pc10_0"                   ,round(cor_pc10_0)),
                    ("pm0_1"                    ,cor_pm0_1), 
                    ("pm0_3"                    ,cor_pm0_3),
                    ("pm0_5"                    ,cor_pm0_5),
                    ("pm1_0"                    ,cor_pm1_0),
                    ("pm2_5"                    ,cor_pm2_5),
                    ("pm5_0"                    ,cor_pm5_0), 
                    ("pm10_0"                   ,cor_pm10_0),
                    ("pm2_5ML"                  ,ml_pm2_5),
                    ("temperature"              ,temperature),
                    ("pressure"                 ,pressure), 
                    ("humidity"                 ,humidity),
                    ("dewPoint"                 ,dewPoint),
                    ("climateNullValidity"      ,climateNullValidity), 
                    ("climateDateTimeValidity"  ,climateDateTimeValidity),
                    ("climateValidity"          ,climateValidity),
                    ("humidityValidity"         ,humidityValidity),
                    ("dewPointValidity"         ,dewPointValidity),
                    ("mlValidity"               ,mlValidity)
                    ])
        print(sensorDictionary)
        mSR.sensorFinisher(dateTime,"IPS7100MC",sensorDictionary)



def humidityCorrectedPM(cor_pc0_1, cor_pc0_3, cor_pc0_5,\
                        cor_pc1_0, cor_pc2_5, cor_pc5_0, \
                            cor_pc10_0):

    m0_1 = 8.355696123812269e-07
    m0_3 = 2.2560825222215327e-05
    m0_5 = 0.00010446111749483851
    m1_0 = 0.0008397941861044865
    m2_5 = 0.013925696906339288
    m5_0 = 0.12597702778750686
    m10_0 = 1.0472

    cor_pm0_1   = m0_1*cor_pc0_1
    cor_pm0_3   = cor_pm0_1 + m0_3*cor_pc0_3
    cor_pm0_5   = cor_pm0_3 + m0_5*cor_pc0_5
    cor_pm1_0   = cor_pm0_5 + m1_0*cor_pc1_0
    cor_pm2_5   = cor_pm1_0 + m2_5*cor_pc2_5
    cor_pm5_0   = cor_pm2_5 + m5_0*cor_pc5_0
    cor_pm10_0  = cor_pm5_0 + m10_0*cor_pc10_0

    print("Humidity Corrected PM")
    return cor_pm0_1, cor_pm0_3, cor_pm0_5, cor_pm1_0, cor_pm2_5, cor_pm5_0, cor_pm10_0;




def mlCorrectedPM(temperature,humidity,pressure,dewPoint,cor_pm2_5):
    try:
        foggy = float(temperature) - float(dewPoint)
        data = {'cor_pm2_5': [float(cor_pm2_5)], 'temperature': [float(temperature)], 'pressure': [pressure], 'humidity':[humidity], 'dewPoint':[dewPoint], 'temp_dew':[foggy]}
        df = pd.DataFrame(data)
        predicted_train_valid2 = makePrediction(loaded_humidModel, df)
        return predicted_train_valid2["Predictions"][0], 1;
    except Exception as e:
        print("An error  occured")
        print(e)
        return cor_pm2_5, 0;




def is_valid_temperature(temp):
    return -20 <= temp <= 50  # Assuming temperature is in Celsius

def is_valid_humidity(humidity):
    return 0 <= humidity <= 100  # Assuming humidity is in percentage



def keepClimateData(dateTime,sensorName,sensorDictionary):   
    climateData = [] 
    if sensorName == "BME280V2":
        climateData =  OrderedDict([
            ("dateTime"     ,str(dateTime)),
            ("temperature"  ,sensorDictionary['temperature']),
            ("pressure"     ,sensorDictionary['pressure']),
            ("humidity"     ,sensorDictionary['humidity']),
            ("dewPoint"     ,sensorDictionary['dewPoint']),
                ])

    if sensorName == "WIMDA":
        climateData =  OrderedDict([
            ("dateTime"     ,str(dateTime)),
            ("temperature"  ,sensorDictionary['airTemperature']),
            ("pressure"     ,1000*float(sensorDictionary['barrometricPressureBars'])),
            ("humidity"     ,sensorDictionary['relativeHumidity']),
            ("dewPoint"     ,sensorDictionary['dewPoint']),
                ])
        
    if climateData:
        writeJSONLatestClimate(sensorDictionary,sensorName)

def writeJSONLatestClimate(sensorDictionary,sensorName):
    directoryIn  = dataFolderTmp+"/"+macAddress+"/"+sensorName+".json"
    print(directoryIn)
    mSR.directoryCheck(directoryIn)
    try:
        with open(directoryIn,'w') as fp:
            json.dump(sensorDictionary, fp)

    except:
        print("Json Data Not Written")

def loadJSONLatestClimate(sensorName):
    directoryIn  = dataFolderTmp+"/"+macAddress+"/"+sensorName+".json"
    try:
        with open(directoryIn, 'r') as fp:
            loaded_data = json.load(fp)
            print("Json Data Loaded Successfully")
            # Now 'loaded_data' contains the Python dictionary loaded from the JSON file
            print(loaded_data)
            return loaded_data
    except FileNotFoundError:
        print("File Not Found")

    except json.JSONDecodeError:
        print("Error decoding JSON data")

    return;

def makePrediction(modelName, est_df):
    predictions_train = pd.DataFrame(modelName.predict(est_df),columns=["Predictions"])
    return predictions_train   

def humidityCorrectedPC(pc0_1, pc0_3, pc0_5, pc1_0, pc2_5, pc5_0, pc10_0, humidity, temperature, dewPoint):

    pc0_1 = float(pc0_1)
    pc0_3 = float(pc0_3)
    pc0_5 = float(pc0_5)
    pc1_0 = float(pc1_0)
    pc2_5 = float(pc2_5)
    pc5_0 = float(pc5_0)
    pc10_0 = float(pc10_0)

    hum = float(humidity)
    tem = float(temperature)
    dew = float(dewPoint)

    print('Condition is satisfied')
    data = {'count': [pc0_1, None, pc0_3, pc0_5, pc1_0, pc2_5, pc5_0, pc10_0, None],
            'D_range': [50, 20, 200, 200, 500, 1500, 2500, 5000, None],
            'D_point': [50, 80, 100, 300, 500, 1000, 2500, 5000, 10000]}
    df1 = pd.DataFrame(data)
    df1['N/D'] = df1['count']/df1['D_range']

    df1['height_ini'] = 0
    df1.loc[7, 'height_ini'] = (2*df1.loc[7, 'count'])/5000
    df1.loc[6, 'height_ini'] = (2*df1.loc[6, 'count'])/2500 - df1.loc[7, 'height_ini']
    df1.loc[5, 'height_ini'] = (2*df1.loc[5, 'count'])/1500 - df1.loc[6, 'height_ini']
    df1.loc[4, 'height_ini'] = (2*df1.loc[4, 'count'])/500 - df1.loc[5, 'height_ini']
    df1.loc[3, 'height_ini'] = (2*df1.loc[3, 'count'])/200 - df1.loc[4, 'height_ini']
    df1.loc[2, 'height_ini'] = (2*df1.loc[2, 'count'])/200 - df1.loc[3, 'height_ini']
    df1.loc[0, 'height_ini'] = (2*df1.loc[0, 'count'])/50 - df1.loc[2, 'height_ini']
    df1.loc[1, 'height_ini'] = (20*(df1.loc[0, 'height_ini']-df1.loc[2, 'height_ini'])/50) + df1.loc[2, 'height_ini']
    df1.loc[1, 'count'] = 0.5*(df1.loc[1, 'height_ini']+df1.loc[2, 'height_ini'])*20

    RH = (hum) * 0.7
    RH = 98 if RH >= 99 else RH
    k = 0.62
    df1['D_dry_point'] = df1['D_point']/((1 + k*(RH/(100-RH)))**(1/3))

    df1['D_dry_range'] = df1['D_dry_point'].diff().shift(-1)


    df1['fit_height_ini'] = 0
    df1.loc[7, 'fit_height_ini'] = (2*df1.loc[7, 'count'])/df1.loc[7, 'D_dry_range']
    df1.loc[6, 'fit_height_ini'] = (2*df1.loc[6, 'count'])/df1.loc[6, 'D_dry_range'] - df1.loc[7, 'fit_height_ini']
    df1.loc[5, 'fit_height_ini'] = (2*df1.loc[5, 'count'])/df1.loc[5, 'D_dry_range'] - df1.loc[6, 'fit_height_ini']
    df1.loc[4, 'fit_height_ini'] = (2*df1.loc[4, 'count'])/df1.loc[4, 'D_dry_range'] - df1.loc[5, 'fit_height_ini']
    df1.loc[3, 'fit_height_ini'] = (2*df1.loc[3, 'count'])/df1.loc[3, 'D_dry_range'] - df1.loc[4, 'fit_height_ini']
    df1.loc[2, 'fit_height_ini'] = (2*df1.loc[2, 'count'])/df1.loc[2, 'D_dry_range'] - df1.loc[3, 'fit_height_ini']
    df1.loc[1, 'fit_height_ini'] = (2*df1.loc[1, 'count'])/df1.loc[1, 'D_dry_range'] - df1.loc[2, 'fit_height_ini']

    df1['slope'] = (df1['fit_height_ini'].shift(-1) - df1['fit_height_ini']) / df1['D_dry_range']
    df1['interc'] = df1['fit_height_ini'] - df1['slope'] * df1['D_dry_point']

    df1['cor_height'] = None
    df1['cor_count'] = 0

    if df1.loc[8, 'D_dry_point'] > 5000:
        df1.loc[7, 'cor_height'] = df1.loc[7, 'slope']*5000 + df1.loc[7, 'interc']
        df1.loc[7, 'cor_count'] = 0.5*df1.loc[7, 'cor_height']*(df1.loc[8, 'D_dry_point']-5000)
    else:
        df1.loc[7, 'cor_height'] = 0
        df1.loc[7, 'cor_count'] = 0
    
    if (2500<df1.loc[7, 'D_dry_point']<=5000)&(df1.loc[8, 'D_dry_point']>5000):
        df1.loc[6, 'cor_height'] = df1.loc[6, 'slope']*2500 + df1.loc[6, 'interc']
        df1.loc[6, 'cor_count'] = (0.5*(df1.loc[7, 'cor_height']+df1.loc[7, 'fit_height_ini'])*(5000-df1.loc[7, 'D_dry_point'])) + (0.5*(df1.loc[6, 'cor_height']+df1.loc[7, 'fit_height_ini'])*(df1.loc[7, 'D_dry_point']-2500))
    elif (2500<df1.loc[7, 'D_dry_point']<5000)&(df1.loc[8, 'D_dry_point']<5000):
        df1.loc[6, 'cor_height'] = df1.loc[6, 'slope']*2500 + df1.loc[6, 'interc']
        df1.loc[6, 'cor_count'] = (0.5*(df1.loc[6, 'cor_height']+df1.loc[7, 'fit_height_ini'])*(df1.loc[7, 'D_dry_point']-2500)) + (0.5*df1.loc[7, 'fit_height_ini']*(df1.loc[8, 'D_dry_point']-df1.loc[7, 'D_dry_point']))
    elif (df1.loc[7, 'D_dry_point']<2500)&(df1.loc[8, 'D_dry_point']<5000):
        df1.loc[6, 'cor_height'] = df1.loc[7, 'slope']*2500 + df1.loc[7, 'interc']
        df1.loc[6, 'cor_count'] = (0.5*df1.loc[6, 'cor_height'])*(df1.loc[8, 'D_dry_point']-2500)
    else:
        df1.loc[6, 'cor_height'] = df1.loc[7, 'slope']*2500 + df1.loc[7, 'interc']
        df1.loc[6, 'cor_count'] = 0.5*(df1.loc[7, 'cor_height']+df1.loc[6, 'cor_height'])*2500
    
    if (1000<df1.loc[6, 'D_dry_point']<=2500)&(df1.loc[7, 'D_dry_point']>2500):
        df1.loc[5, 'cor_height'] = df1.loc[5, 'slope']*1000 + df1.loc[5, 'interc']
        df1.loc[5, 'cor_count'] = (0.5*(df1.loc[6, 'cor_height']+df1.loc[6, 'fit_height_ini'])*(2500-df1.loc[6, 'D_dry_point'])) + (0.5*(df1.loc[5, 'cor_height']+df1.loc[6, 'fit_height_ini'])*(df1.loc[6, 'D_dry_point']-1000))
    elif (1000<df1.loc[6, 'D_dry_point']<2500)&(df1.loc[7, 'D_dry_point']<2500):
        df1.loc[5, 'cor_height'] = df1.loc[5, 'slope']*1000 + df1.loc[5, 'interc']
        df1.loc[5, 'cor_count'] = (0.5*(df1.loc[5, 'cor_height']+df1.loc[6, 'fit_height_ini'])*(df1.loc[6, 'D_dry_point']-1000)) + (0.5*(df1.loc[6,'fit_height_ini']+df1.loc[7,'fit_height_ini'])*(df1.loc[7,'D_dry_point']-df1.loc[6,'D_dry_point'])) + (0.5*(df1.loc[7,'fit_height_ini']+df1.loc[6,'cor_height'])*(2500-df1.loc[7,'D_dry_point']))
    elif (df1.loc[6,'D_dry_point']<1000)&(df1.loc[7,'D_dry_point']<2500):
        df1.loc[5,'cor_height'] = df1.loc[6,'slope']*1000 + df1.loc[6,'interc']
        df1.loc[5,'cor_count'] = (0.5*(df1.loc[6,'cor_height']+df1.loc[7,'fit_height_ini'])*(2500-df1.loc[7,'D_dry_point'])) + (0.5*(df1.loc[5,'cor_height']+df1.loc[7,'fit_height_ini'])*(df1.loc[7,'D_dry_point']-1000))
    else:
        df1.loc[5,'cor_height'] = df1.loc[6,'slope']*1000 + df1.loc[6,'interc']
        df1.loc[5,'cor_count'] = 0.5*(df1.loc[6,'cor_height']+df1.loc[5,'cor_height'])*1500

    if (500<df1.loc[5,'D_dry_point']<=1000)&(df1.loc[6,'D_dry_point']>1000):
        df1.loc[4,'cor_height'] = df1.loc[4,'slope']*500 + df1.loc[4,'interc']
        df1.loc[4,'cor_count'] = (0.5*(df1.loc[5,'cor_height']+df1.loc[5,'fit_height_ini'])*(1000-df1.loc[5,'D_dry_point'])) + (0.5*(df1.loc[4,'cor_height']+df1.loc[5,'fit_height_ini'])*(df1.loc[5,'D_dry_point']-500))
    elif (500<df1.loc[5,'D_dry_point']<1000)&(df1.loc[6,'D_dry_point']<1000):
        df1.loc[4,'cor_height'] = df1.loc[4,'slope']*500 + df1.loc[4,'interc']
        df1.loc[4,'cor_count'] = (0.5*(df1.loc[4,'cor_height']+df1.loc[5,'fit_height_ini'])*(df1.loc[5,'D_dry_point']-500)) + (0.5*(df1.loc[5,'fit_height_ini']+df1.loc[6,'fit_height_ini'])*(df1.loc[6,'D_dry_point']-df1.loc[5,'D_dry_point'])) + (0.5*(df1.loc[6,'fit_height_ini']+df1.loc[5,'cor_height'])*(1000-df1.loc[6,'D_dry_point']))
    elif (df1.loc[5,'D_dry_point']<500)&(df1.loc[6,'D_dry_point']<1000):
        df1.loc[4,'cor_height'] = df1.loc[5,'slope']*500 + df1.loc[5,'interc']
        df1.loc[4,'cor_count'] = (0.5*(df1.loc[5,'cor_height']+df1.loc[6,'fit_height_ini'])*(1000-df1.loc[6,'D_dry_point'])) + (0.5*(df1.loc[4,'cor_height']+df1.loc[6,'fit_height_ini'])*(df1.loc[6,'D_dry_point']-500))
    else:
        df1.loc[4,'cor_height'] = df1.loc[5,'slope']*500 + df1.loc[5,'interc']
        df1.loc[4,'cor_count'] = 0.5*(df1.loc[5,'cor_height']+df1.loc[4,'cor_height'])*500

    if (300<df1.loc[4,'D_dry_point']<=500)&(df1.loc[5,'D_dry_point']>500):
        df1.loc[3,'cor_height'] = df1.loc[3,'slope']*300 + df1.loc[3,'interc']
        df1.loc[3,'cor_count'] = (0.5*(df1.loc[4,'cor_height']+df1.loc[4,'fit_height_ini'])*(500-df1.loc[4,'D_dry_point'])) + (0.5*(df1.loc[3,'cor_height']+df1.loc[4,'fit_height_ini'])*(df1.loc[4,'D_dry_point']-300))
    elif (300<df1.loc[4,'D_dry_point']<500)&(df1.loc[5,'D_dry_point']<500):
        df1.loc[3,'cor_height'] = df1.loc[3,'slope']*300 + df1.loc[3,'interc']
        df1.loc[3,'cor_count'] = (0.5*(df1.loc[3,'cor_height']+df1.loc[4,'fit_height_ini'])*(df1.loc[4,'D_dry_point']-300)) + (0.5*(df1.loc[4,'fit_height_ini']+df1.loc[5,'fit_height_ini'])*(df1.loc[5,'D_dry_point']-df1.loc[4,'D_dry_point'])) + (0.5*(df1.loc[5,'fit_height_ini']+df1.loc[4,'cor_height'])*(500-df1.loc[5,'D_dry_point']))
    elif (df1.loc[4,'D_dry_point']<300)&(df1.loc[5,'D_dry_point']<500):
        df1.loc[3,'cor_height'] = df1.loc[4,'slope']*300 + df1.loc[4,'interc']
        df1.loc[3,'cor_count'] = (0.5*(df1.loc[4,'cor_height']+df1.loc[5,'fit_height_ini'])*(500-df1.loc[5,'D_dry_point'])) + (0.5*(df1.loc[3,'cor_height']+df1.loc[5,'fit_height_ini'])*(df1.loc[5,'D_dry_point']-300))
    else:
        df1.loc[3,'cor_height'] = df1.loc[4,'slope']*300 + df1.loc[4,'interc']
        df1.loc[3,'cor_count'] = 0.5*(df1.loc[4,'cor_height']+df1.loc[3,'cor_height'])*200

    if (100<df1.loc[3,'D_dry_point']<=300)&(df1.loc[4,'D_dry_point']>300):
        df1.loc[2,'cor_height'] = df1.loc[2,'slope']*100 + df1.loc[2,'interc']
        df1.loc[2,'cor_count'] = (0.5*(df1.loc[3,'cor_height']+df1.loc[3,'fit_height_ini'])*(300-df1.loc[3,'D_dry_point'])) + (0.5*(df1.loc[2,'cor_height']+df1.loc[3,'fit_height_ini'])*(df1.loc[3,'D_dry_point']-100))
    elif (100<df1.loc[3,'D_dry_point']<300)&(df1.loc[4,'D_dry_point']<300):
        df1.loc[2,'cor_height'] = df1.loc[2,'slope']*100 + df1.loc[2,'interc']
        df1.loc[2,'cor_count'] = (0.5*(df1.loc[2,'cor_height']+df1.loc[3,'fit_height_ini'])*(df1.loc[3,'D_dry_point']-100)) + (0.5*(df1.loc[3,'fit_height_ini']+df1.loc[4,'fit_height_ini'])*(df1.loc[4,'D_dry_point']-df1.loc[3,'D_dry_point'])) + (0.5*(df1.loc[4,'fit_height_ini']+df1.loc[3,'cor_height'])*(300-df1.loc[4,'D_dry_point']))
    elif (df1.loc[3,'D_dry_point']<100)&(df1.loc[4,'D_dry_point']<300):
        df1.loc[2,'cor_height'] = df1.loc[3,'slope']*100 + df1.loc[3,'interc']
        df1.loc[2,'cor_count'] = (0.5*(df1.loc[3,'cor_height']+df1.loc[4,'fit_height_ini'])*(300-df1.loc[4,'D_dry_point'])) + (0.5*(df1.loc[2,'cor_height']+df1.loc[4,'fit_height_ini'])*(df1.loc[4,'D_dry_point']-100))
    else:
        df1.loc[2,'cor_height'] = df1.loc[3,'slope']*100 + df1.loc[3,'interc']
        df1.loc[2,'cor_count'] = 0.5*(df1.loc[3,'cor_height']+df1.loc[2,'cor_height'])*200

    if (50<df1.loc[2,'D_dry_point']<=100)&(df1.loc[3,'D_dry_point']>100):
        df1.loc[0,'cor_height'] = df1.loc[1,'slope']*50 + df1.loc[1,'interc']
        df1.loc[0,'cor_count'] = (0.5*(df1.loc[2,'cor_height']+df1.loc[2,'fit_height_ini'])*(100-df1.loc[2,'D_dry_point'])) + (0.5*(df1.loc[0,'cor_height']+df1.loc[2,'fit_height_ini'])*(df1.loc[2,'D_dry_point']-50))
    elif (50<df1.loc[2,'D_dry_point']<100)&(df1.loc[3,'D_dry_point']>100):
        df1.loc[0,'cor_height'] = df1.loc[1,'slope']*50 + df1.loc[1,'interc']
        df1.loc[0,'cor_count'] = (0.5*(df1.loc[0,'cor_height']+df1.loc[2,'fit_height_ini'])*(df1.loc[2,'D_dry_point']-50)) + (0.5*(df1.loc[2,'fit_height_ini']+df1.loc[3,'fit_height_ini'])*(df1.loc[3,'D_dry_point']-df1.loc[2,'D_dry_point'])) + (0.5*(df1.loc[3,'fit_height_ini']+df1.loc[2,'cor_height'])*(100-df1.loc[3,'D_dry_point']))
    elif (df1.loc[2,'D_dry_point']<50)&(df1.loc[3,'D_dry_point']>100):
        df1.loc[0,'cor_height'] = df1.loc[2,'slope']*50 + df1.loc[2,'interc']
        df1.loc[0,'cor_count'] = (0.5*(df1.loc[2,'cor_height']+df1.loc[3,'fit_height_ini'])*(100-df1.loc[3,'D_dry_point'])) + (0.5*(df1.loc[0,'cor_height']+df1.loc[3,'fit_height_ini'])*(df1.loc[3,'D_dry_point']-50))
    else:
        df1.loc[0,'cor_height'] = df1.loc[2,'slope']*50 + df1.loc[2,'interc']
        df1.loc[0,'cor_count'] = 0.5*(df1.loc[2,'cor_height']+df1.loc[0,'cor_height'])*50
        
    
    pc0_1, pc0_3, pc0_5, pc1_0, pc2_5, pc5_0, pc10_0 = \
        df1.loc[0,'cor_count'], df1.loc[2,'cor_count'], df1.loc[3,'cor_count'], df1.loc[4,'cor_count'], df1.loc[5,'cor_count'], df1.loc[6,'cor_count'], df1.loc[7,'cor_count']
    
    return pc0_1, pc0_3, pc0_5, pc1_0, pc2_5, pc5_0, pc10_0, hum, tem, dew