#!/bin/bash
#
sleep 30
python3 ipReader.py
sleep 5
source /home/rxhf/lora/bin/activate && python loraReader.py

# python3 centralNodeReaderNano.py &
# sleep 10
# cd odroidShow2 && python3 mintsShow2.py
