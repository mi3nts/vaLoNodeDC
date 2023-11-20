#!/bin/bash

sleep 55
export LD_PRELOAD=/home/teamlary/.local/lib/python3.8/site-packages/scikit_learn.libs/libgomp-d22c30c5.so.1.0.0
sleep 5

kill $(pgrep -f 'python3 audioDeleter.py')
sleep 5
python3 audioDeleter.py &
sleep 5

kill $(pgrep -f 'python3 audioRecorder.py')
sleep 5
python3 audioRecorder.py &
sleep 5

kill $(pgrep -f 'ips7100ReaderV1.py')
sleep 5
python3 ips7100ReaderV1.py &
sleep 5

kill $(pgrep -f 'python3 i2cReader.py')
sleep 5
python3 i2cReader.py &
sleep 5

kill $(pgrep -f 'python3 airMarReader.py')
sleep 5
python3 airMarReader.py &
sleep 5

kill $(pgrep -f 'python3 rg15Reader.py')  
sleep 5
python3 rg15Reader.py >> /home/teamlary/logs/rainSensorCheck.txt 2>&1 &
sleep 5

kill $(pgrep -f 'audioAnalyzer.py') 
sleep 5
python3 audioAnalyzer.py &
sleep 5


python3 ipReader.py
sleep 5