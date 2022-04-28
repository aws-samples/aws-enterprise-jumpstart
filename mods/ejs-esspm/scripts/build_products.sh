#!/usr/bin/env bash

set -e

cd cdk
npm install aws-cdk
npm update

ls

python3 -m venv .venv
source .venv/bin/activate
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade virtualenv
python3 -m pip install -r requirements.txt

npx cdk synth -o dist --app "python3 app.py"

python3 ../scripts/clean_cdk.py

cd ..
