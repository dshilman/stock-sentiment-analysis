#!/bin/sh
sudo wget https://bootstrap.pypa.io/get-pip.py
sudo python3 ./get-pip.py
mldir=~/tmp
sudo dnf install cronie cronie-anacron
cd stock-sentiment-analysis
sudo TMPDIR=~/tmp/ python3 -m pip install -r requirements.txt --no-cache-dir
cd code
sudo python3 app.py