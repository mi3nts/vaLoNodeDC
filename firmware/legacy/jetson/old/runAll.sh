#!/bin/bash
#
sleep 30
source /home/rxhf/lora/bin/activate && python loraReader.py
sleep 5
python3 ipReader.py


# python3 centralNodeReaderNano.py &
# sleep 10
# cd odroidShow2 && python3 mintsShow2.py
