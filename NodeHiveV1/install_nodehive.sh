#!/usr/bin/env bash

sudo apt-get install python-pip

sudo pip install virtualenv

sudo virtualenv nodehive

source nodehive/bin/activate

pip install -r requirements.txt

export FLASK_APP=nodehive.py

sudo flask run --host=0.0.0.0