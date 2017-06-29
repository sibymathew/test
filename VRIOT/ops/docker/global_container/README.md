# Easy Setup for VRIOT

## Prerequisites :

Have Docker installed.

## Build Instructions.

From the root of the repository, run

    python VRIOT/ops/scripts/build.py

## Usage Instructions

Run the image built in last step (map the ports for access.)

    docker run -p 8000:8000 -p 27017:27017 -p 9001:9001 -p 1883:1883 -p 5000:5000 -p 5672:5672 -p 5216:5216 -v <host_path>:/data/db vriothub/comprehensive:oooo.___.UT