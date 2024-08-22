#!/bin/bash

sleep 55

kill $(pgrep -f 'ips7100ReaderV1.py')
sleep 5
python3 ips7100ReaderV1.py &
sleep 5

kill $(pgrep -f 'python3 i2cAndUsbGPSReader.py')
sleep 5
python3 i2cAndUsbGPSReader.py &
sleep 5


kill $(pgrep -f 'python3 rg15Reader.py')  
sleep 5
python3 rg15Reader.py &
sleep 5


kill $(pgrep -f 'python3 rg15USBReader.py')  
sleep 5
python3 rg15USBReader.py &
sleep 5


kill $(pgrep -f 'python3 airMarReader.py')
sleep 5
python3 airMarReader.py &
sleep 5

python3 ipReader.py
sleep 5