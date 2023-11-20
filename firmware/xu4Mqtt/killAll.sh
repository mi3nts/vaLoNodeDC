#!/bin/bash
#
sleep 2
kill $(pgrep -f 'ips7100ReaderV1.py')
sleep 1
kill $(pgrep -f 'python3 rainReader.py')
sleep 1
kill $(pgrep -f 'python3 i2cReader.py')
sleep 1
kill $(pgrep -f 'python3 airMarReader.py')
sleep 1
kill $(pgrep -f 'python3 GPSReader.py')
sleep 1
kill $(pgrep -f 'python3 audioDeleter.py')
sleep 1
kill $(pgrep -f 'python3 audioRecorder.py')
sleep 1
kill $(pgrep -f 'audioAnalyzer.py')
