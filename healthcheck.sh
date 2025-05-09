#!/bin/bash

# Check if scheduler.py is running
if pgrep -f "python scheduler.py" > /dev/null; then
    exit 0
else
    exit 1
fi 