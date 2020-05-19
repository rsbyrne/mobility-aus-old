#!/bin/bash
currentDir=$PWD
cd "$(dirname "$0")"
sh run.sh
sh push.sh
cd $currentDir