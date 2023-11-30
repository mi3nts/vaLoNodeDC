#!/bin/bash

sleep 30
python3 audioDeleter.py &
sleep 5
python3 deleter.py &
sleep 5