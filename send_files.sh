#!/bin/bash

# Source the python environment
# If you don't have one then create it by "python -m venv env" (at least on linux)
# Then install 'rshell' like "python -m pip install rshell"
. ./env/bin/activate || exit 1

# Change this to your needs (I mostly use ttyUSB0)
port=/dev/ttyUSB0

# Command to use with rshell
command="cp";

# TODO: add more cases
case $1 in
  -c|--command|--cmd) command="$2"; shift; shift;;
esac

while [[ "$#" -gt 0 ]]; do
    base="$(basename $1)"
    echo "Moving $1 to /pyboard/$base";
    rshell --port $port -b 115200 cp $1 /pyboard/$base
    shift
done
