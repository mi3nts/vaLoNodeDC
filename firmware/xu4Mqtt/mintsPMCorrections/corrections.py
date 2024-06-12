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
    print("Mints Prediction")
    # For Humidity Correction
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
        # At this point load up the climate sensor 
        print("PM data read")
        dateTime        = dateTime
        climateData     = loadJSONLatestClimate(climateSensor)
        dateTimeClimate = datetime.strptime(climateData['dateTime'], "%Y-%m-%d %H:%M:%S.%f")

        cor_pm2_5   = sensorDictionary['pm2_5']
        ml_pm2_5    = sensorDictionary['pm2_5']

        pc0_1, pc0_3, pc0_5,\
            pc1_0, pc2_5, pc5_0, \
                pc10_0 = \
                        sensorDictionary['pc0_1'], sensorDictionary['pc0_3'], sensorDictionary['pc0_5'],\
                        sensorDictionary['pc1_0'], sensorDictionary['pc2_5'], sensorDictionary['pc5_0'], \
                        sensorDictionary['pc10_0']
        
        temperature,humidity,pressure,dewPoint= -100,-100,-100,-100

        cor_pc0_1, cor_pc0_3, cor_pc0_5, \
            cor_pc1_0, cor_pc2_5, cor_pc5_0,\
                cor_pc10_0 \
                            =  pc0_1, pc0_3, pc0_5,\
                                pc1_0, pc2_5, pc5_0, \
                                    pc10_0 

        # Checking Validity 
        if climateData is not None:
            print("No climate data found")
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




        # if humidityValidity and dewPointValidity:
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
        
        sensorDictionary = OrderedDict([
                    ("dateTime"                 ,str(dateTime)), # always the same
                    ("pc0_1"                    ,cor_pc0_1), 
                    ("pc0_3"                    ,cor_pc0_3),
                    ("pc0_5"                    ,cor_pc0_5),
                    ("pc1_0"                    ,cor_pc1_0),
                    ("pc2_5"                    ,cor_pc2_5),
                    ("pc5_0"                    ,cor_pc5_0), 
                    ("pc10_0"                   ,cor_pc10_0),
                    ("pm0_1"                    ,cor_pm0_1), 
                    ("pm0_3"                    ,cor_pm0_3),
                    ("pm0_5"                    ,cor_pm0_5),
                    ("pm1_0"                    ,cor_pm1_0),
                    ("pm2_5"                    ,cor_pm2_5),
                    ("pm5_0"                    ,cor_pm5_0), 
                    ("pm10_0"                   ,cor_pm10_0),
                    ("pm2_5ML"                  ,ml_pm2_5),
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
    df1['height_ini'][7] = (2*df1['count'][7])/5000
    df1['height_ini'][6] = (2*df1['count'][6])/2500 - df1['height_ini'][7]
    df1['height_ini'][5] = (2*df1['count'][5])/1500 - df1['height_ini'][6]
    df1['height_ini'][4] = (2*df1['count'][4])/500 - df1['height_ini'][5]
    df1['height_ini'][3] = (2*df1['count'][3])/200 - df1['height_ini'][4]
    df1['height_ini'][2] = (2*df1['count'][2])/200 - df1['height_ini'][3]
    df1['height_ini'][0] = (2*df1['count'][0])/50 - df1['height_ini'][2]
    df1['height_ini'][1] = (20*(df1['height_ini'][0]-df1['height_ini'][2])/50) + df1['height_ini'][2]
    df1['count'][1] = 0.5*(df1['height_ini'][1]+df1['height_ini'][2])*20

    RH = (hum) * 0.7
    RH = 98 if RH >= 99 else RH
    k = 0.62
    df1['D_dry_point'] = df1['D_point']/((1 + k*(RH/(100-RH)))**(1/3))

    df1['D_dry_range'] = df1['D_dry_point'].diff().shift(-1)

    df1['fit_height_ini'] = 0
    df1['fit_height_ini'][7] = (2*df1['count'][7])/df1['D_dry_range'][7]
    df1['fit_height_ini'][6] = (2*df1['count'][6])/df1['D_dry_range'][6] - df1['fit_height_ini'][7]
    df1['fit_height_ini'][5] = (2*df1['count'][5])/df1['D_dry_range'][5] - df1['fit_height_ini'][6]
    df1['fit_height_ini'][4] = (2*df1['count'][4])/df1['D_dry_range'][4] - df1['fit_height_ini'][5]
    df1['fit_height_ini'][3] = (2*df1['count'][3])/df1['D_dry_range'][3] - df1['fit_height_ini'][4]
    df1['fit_height_ini'][2] = (2*df1['count'][2])/df1['D_dry_range'][2] - df1['fit_height_ini'][3]
    df1['fit_height_ini'][1] = (2*df1['count'][1])/df1['D_dry_range'][1] - df1['fit_height_ini'][2]

    df1['slope'] = (df1['fit_height_ini'].shift(-1) - df1['fit_height_ini']) / df1['D_dry_range']
    df1['interc'] = df1['fit_height_ini'] - df1['slope'] * df1['D_dry_point']

    df1['cor_height'] = None
    df1['cor_count'] = 0

    if df1['D_dry_point'][8] > 5000:
        df1['cor_height'][7] = df1['slope'][7]*5000 + df1['interc'][7]
        df1['cor_count'][7] = 0.5*df1['cor_height'][7]*(df1['D_dry_point'][8]-5000)
    else:
        df1['cor_height'][7] = 0
        df1['cor_count'][7] = 0
    
    if (2500<df1['D_dry_point'][7]<=5000)&(df1['D_dry_point'][8]>5000):
        df1['cor_height'][6] = df1['slope'][6]*2500 + df1['interc'][6]
        df1['cor_count'][6] = \
                (0.5*(df1['cor_height'][7]+df1['fit_height_ini'][7])*(5000-df1['D_dry_point'][7])) +\
                (0.5*(df1['cor_height'][6]+df1['fit_height_ini'][7])*(df1['D_dry_point'][7]-2500))
        
    elif (2500<df1['D_dry_point'][7]<5000)&(df1['D_dry_point'][8]<5000):
        df1['cor_height'][6] = df1['slope'][6]*2500 + df1['interc'][6]
        df1['cor_count'][6] = \
                (0.5*(df1['cor_height'][6]+df1['fit_height_ini'][7])*(df1['D_dry_point'][7]-2500)) + \
                (0.5*df1['fit_height_ini'][7]*(df1['D_dry_point'][8]-df1['D_dry_point'][7]))
    
    elif (df1['D_dry_point'][7]<2500)&(df1['D_dry_point'][8]<5000):
        df1['cor_height'][6] = df1['slope'][7]*2500 + df1['interc'][7]
        df1['cor_count'][6]  = (0.5*df1['cor_height'][6])*(df1['D_dry_point'][8]-2500)
    else:
        df1['cor_height'][6] = df1['slope'][7]*2500 + df1['interc'][7]
        df1['cor_count'][6]  = 0.5*(df1['cor_height'][7]+df1['cor_height'][6])*2500
    
    if (1000<df1['D_dry_point'][6]<=2500)&(df1['D_dry_point'][7]>2500):
        df1['cor_height'][5] = df1['slope'][5]*1000 + df1['interc'][5]
        df1['cor_count'][5] = \
                    (0.5*(df1['cor_height'][6]+ \
                    df1['fit_height_ini'][6])*(2500-df1['D_dry_point'][6])) + \
                    (0.5*(df1['cor_height'][5]+df1['fit_height_ini'][6])*(df1['D_dry_point'][6]-1000))
        
    elif (1000<df1['D_dry_point'][6]<2500)&(df1['D_dry_point'][7]<2500):
        df1['cor_height'][5] = df1['slope'][5]*1000 + df1['interc'][5]
        df1['cor_count'][5] = \
        (0.5*(df1['cor_height'][5]+df1['fit_height_ini'][6])*(df1['D_dry_point'][6]-1000)) +\
        (0.5*(df1['fit_height_ini'][6]+df1['fit_height_ini'][7])*(df1['D_dry_point'][7]-df1['D_dry_point'][6])) + \
        (0.5*(df1['fit_height_ini'][7]+df1['cor_height'][6])*(2500-df1['D_dry_point'][7]))
        
    elif (df1['D_dry_point'][6]<1000)&(df1['D_dry_point'][7]<2500):
        df1['cor_height'][5] = df1['slope'][6]*1000 + df1['interc'][6]
        df1['cor_count'][5] = (0.5*(df1['cor_height'][6]+ \
                                    df1['fit_height_ini'][7])*(2500-df1['D_dry_point'][7])) + \
                                    (0.5*(df1['cor_height'][5]+df1['fit_height_ini'][7])*(df1['D_dry_point'][7]-1000))
    else:
        df1['cor_height'][5] = df1['slope'][6]*1000 + df1['interc'][6]
        df1['cor_count'][5] = 0.5*(df1['cor_height'][6]+df1['cor_height'][5])*1500

    if (500<df1['D_dry_point'][5]<=1000)&(df1['D_dry_point'][6]>1000):
        df1['cor_height'][4] = df1['slope'][4]*500 + df1['interc'][4]
        df1['cor_count'][4]  = (0.5*(df1['cor_height'][5]+df1['fit_height_ini'][5])*(1000-df1['D_dry_point'][5])) + \
            (0.5*(df1['cor_height'][4]+df1['fit_height_ini'][5])*(df1['D_dry_point'][5]-500))
    elif (500<df1['D_dry_point'][5]<1000)&(df1['D_dry_point'][6]<1000):
        df1['cor_height'][4] = df1['slope'][4]*500 + df1['interc'][4]
        df1['cor_count'][4] = (0.5*(df1['cor_height'][4]+df1['fit_height_ini'][5])*(df1['D_dry_point'][5]-500)) + \
            (0.5*(df1['fit_height_ini'][5]+df1['fit_height_ini'][6])*(df1['D_dry_point'][6]-df1['D_dry_point'][5])) +\
                (0.5*(df1['fit_height_ini'][6]+df1['cor_height'][5])*(1000-df1['D_dry_point'][6]))
    elif (df1['D_dry_point'][5]<500)&(df1['D_dry_point'][6]<1000):
        df1['cor_height'][4] = df1['slope'][5]*500 + df1['interc'][5]
        df1['cor_count'][4] = (0.5*(df1['cor_height'][5]+df1['fit_height_ini'][6])*(1000-df1['D_dry_point'][6])) +\
            (0.5*(df1['cor_height'][4]+df1['fit_height_ini'][6])*(df1['D_dry_point'][6]-500))
    else:
        df1['cor_height'][4] = df1['slope'][5]*500 + df1['interc'][5]
        df1['cor_count'][4] = 0.5*(df1['cor_height'][5]+df1['cor_height'][4])*500

    if (300<df1['D_dry_point'][4]<=500)&(df1['D_dry_point'][5]>500):
        df1['cor_height'][3] = df1['slope'][3]*300 + df1['interc'][3]
        df1['cor_count'][3] = (0.5*(df1['cor_height'][4]+df1['fit_height_ini'][4])*(500-df1['D_dry_point'][4])) +\
            (0.5*(df1['cor_height'][3]+df1['fit_height_ini'][4])*(df1['D_dry_point'][4]-300))
    elif (300<df1['D_dry_point'][4]<500)&(df1['D_dry_point'][5]<500):
        df1['cor_height'][3] = df1['slope'][3]*300 + df1['interc'][3]
        df1['cor_count'][3] = (0.5*(df1['cor_height'][3]+df1['fit_height_ini'][4])*(df1['D_dry_point'][4]-300)) + \
            (0.5*(df1['fit_height_ini'][4]+df1['fit_height_ini'][5])*(df1['D_dry_point'][5]-df1['D_dry_point'][4])) +\
                (0.5*(df1['fit_height_ini'][5]+df1['cor_height'][4])*(500-df1['D_dry_point'][5]))
    elif (df1['D_dry_point'][4]<300)&(df1['D_dry_point'][5]<500):
        df1['cor_height'][3] = df1['slope'][4]*300 + df1['interc'][4]
        df1['cor_count'][3] = (0.5*(df1['cor_height'][4]+df1['fit_height_ini'][5])*(500-df1['D_dry_point'][5])) + \
            (0.5*(df1['cor_height'][3]+df1['fit_height_ini'][5])*(df1['D_dry_point'][5]-300))
    else:
        df1['cor_height'][3] = df1['slope'][4]*300 + df1['interc'][4]
        df1['cor_count'][3] = 0.5*(df1['cor_height'][4]+df1['cor_height'][3])*200

    if (100<df1['D_dry_point'][3]<=300)&(df1['D_dry_point'][4]>300):
        df1['cor_height'][2] = df1['slope'][2]*100 + df1['interc'][2]
        df1['cor_count'][2] = (0.5*(df1['cor_height'][3]+df1['fit_height_ini'][3])*(300-df1['D_dry_point'][3])) +\
            (0.5*(df1['cor_height'][2]+df1['fit_height_ini'][3])*(df1['D_dry_point'][3]-100))
    elif (100<df1['D_dry_point'][3]<300)&(df1['D_dry_point'][4]<300):
        df1['cor_height'][2] = df1['slope'][2]*100 + df1['interc'][2]
        df1['cor_count'][2] = (0.5*(df1['cor_height'][2]+df1['fit_height_ini'][3])*(df1['D_dry_point'][3]-100)) +\
            (0.5*(df1['fit_height_ini'][3]+df1['fit_height_ini'][4])*(df1['D_dry_point'][4]-df1['D_dry_point'][3])) + \
                (0.5*(df1['fit_height_ini'][4]+df1['cor_height'][3])*(300-df1['D_dry_point'][4]))
    elif (df1['D_dry_point'][3]<100)&(df1['D_dry_point'][4]<300):
        df1['cor_height'][2] = df1['slope'][3]*100 + df1['interc'][3]
        df1['cor_count'][2] = (0.5*(df1['cor_height'][3]+df1['fit_height_ini'][4])*(300-df1['D_dry_point'][4])) +\
            (0.5*(df1['cor_height'][2]+df1['fit_height_ini'][4])*(df1['D_dry_point'][4]-100))
    else:
        df1['cor_height'][2] = df1['slope'][3]*100 + df1['interc'][3]
        df1['cor_count'][2] = 0.5*(df1['cor_height'][3]+df1['cor_height'][2])*200

    if (50<df1['D_dry_point'][2]<=100)&(df1['D_dry_point'][3]>100):
        df1['cor_height'][0] = df1['slope'][1]*50 + df1['interc'][1]
        df1['cor_count'][0] = (0.5*(df1['cor_height'][2]+df1['fit_height_ini'][2])*(100-df1['D_dry_point'][2])) +\
            (0.5*(df1['cor_height'][0]+df1['fit_height_ini'][2])*(df1['D_dry_point'][2]-50))
    elif (50<df1['D_dry_point'][2]<100)&(df1['D_dry_point'][3]>100):
        df1['cor_height'][0] = df1['slope'][1]*50 + df1['interc'][1]
        df1['cor_count'][0] = (0.5*(df1['cor_height'][0]+df1['fit_height_ini'][2])*(df1['D_dry_point'][2]-50)) + \
            (0.5*(df1['fit_height_ini'][2]+df1['fit_height_ini'][3])*(df1['D_dry_point'][3]-df1['D_dry_point'][2])) + \
                (0.5*(df1['fit_height_ini'][3]+df1['cor_height'][2])*(100-df1['D_dry_point'][3]))
    elif (df1['D_dry_point'][2]<50)&(df1['D_dry_point'][3]>100):
        df1['cor_height'][0] = df1['slope'][2]*50 + df1['interc'][2]
        df1['cor_count'][0] = (0.5*(df1['cor_height'][2]+df1['fit_height_ini'][3])*(100-df1['D_dry_point'][3])) + \
            (0.5*(df1['cor_height'][0]+df1['fit_height_ini'][3])*(df1['D_dry_point'][3]-50))
    else:
        df1['cor_height'][0] = df1['slope'][2]*50 + df1['interc'][2]
        df1['cor_count'][0] = 0.5*(df1['cor_height'][2]+df1['cor_height'][0])*50

    pc0_1, pc0_3, pc0_5, pc1_0, pc2_5, pc5_0, pc10_0 = \
        df1['cor_count'][0], df1['cor_count'][2], df1['cor_count'][3], df1['cor_count'][4], df1['cor_count'][5], df1['cor_count'][6], df1['cor_count'][7]
    # else:
    #     print('Condition is not satisfied')
    return pc0_1, pc0_3, pc0_5, pc1_0, pc2_5, pc5_0, pc10_0, hum, tem, dew