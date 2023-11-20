#!/bin/bash
#
sleep 30
python3 airMarReader.py &
sleep 5
python3 nanoReader.py 0 & 
sleep 5
python3 ipReader.py


# python3 centralNodeReaderNano.py &
# sleep 10
# cd odroidShow2 && python3 mintsShow2.py
