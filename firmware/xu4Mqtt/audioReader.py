#from importlib_metadata import files

from scipy.io.wavfile import write
import os

import csv

import sys
from collections import OrderedDict
import datetime

import numpy as np
import pandas as pd

import time

time.sleep(1) 

from mintsXU4 import mintsSensorReader as mSR
from mintsXU4 import mintsDefinitions as mD

from multiprocessing import Pool, freeze_support
from audioMints import config as cfg
from audioMints import functions as fn

sampleRate         = 44100  # Sample rate
period             = 9 # Duration of recording
channelSelected    = 1
audioFileNamePre   = "mintsAudio"
tmpFolderName      = "/home/teamlary/NC/"
minConfidence      = .3
numOfThreads       = 4

dataFolder         = mD.dataFolder


currentIndex = 0 


def main(cfg,currentIndex):
    labels = pd.read_csv("audioMints/labels/labels.csv") 
    mSR.directoryCheck(tmpFolderName)

    while True:
        try:
            dateTime = datetime.datetime.now()
            recording = fn.makeAudioFile(sampleRate,period,channelSelected,audioFileNamePre+ ".wav",tmpFolderName)

            # Freeze support for excecutable
            freeze_support()
            cfg = fn.configSetUp(cfg,tmpFolderName,minConfidence,numOfThreads)
            soundClassData = pd.read_csv(tmpFolderName + '/'+ audioFileNamePre+  '.BirdNET.results.csv')
            soundClassData["Labels"] = soundClassData["Scientific name"].map(labels.set_index("Scientific name")["Labels"])
            print(soundClassData)
            for index, row in soundClassData.iterrows():
                sensorDictionary = OrderedDict([
                    ("dateTime"     ,str(dateTime + datetime.timedelta(seconds = row['Start (s)']))),
                    ("label"        ,row['Labels']),
                    ("confidence"   ,row['Confidence'])
                     ])
                mSR.sensorFinisher(dateTime,"MBC001",sensorDictionary)
      
            print("=============")
            print()

        except OSError as e:
            print ("Error: %s - %s." % (e.filename, e.strerror))
            print("Microphone Not Connected: Check connection")
            

if __name__ == "__main__":
    print("=============")
    print("    MINTS    ")
    print("=============")
    print("Connecting to the microphone on Channel: {0}".format(channelSelected) + " with Sample Rate " + str(sampleRate))
    main(cfg,currentIndex)    









