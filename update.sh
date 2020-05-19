#!/bin/bash
MOUNTFROM=$PWD'/..'
MOUNTTO='/home/morpheus/workspace/mount'
IMAGE='rsbyrne/mobility-aus'
SOCK='/var/run/docker.sock'
docker run -v $MOUNTFROM:$MOUNTTO -v $SOCK:$SOCK --shm-size 2g $IMAGE sudo python3 '/home/morpheus/workspace/mount/mobility-aus/update.py'
