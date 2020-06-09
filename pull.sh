#!/bin/bash
MOUNTFROM=$PWD
MOUNTTO='/home/morpheus/workspace/mount'
IMAGE='rsbyrne/mobility-aus'
SOCK='/var/run/docker.sock'
sudo chmod -R 777 'data'
docker run -v $MOUNTFROM:$MOUNTTO -v $SOCK:$SOCK --shm-size 2g $IMAGE sudo python3 '/home/morpheus/workspace/mount/pull.py'
sudo chmod -R 777 'data'