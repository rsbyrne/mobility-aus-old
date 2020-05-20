#!/bin/bash
currentDir=$PWD
cd "$(dirname "$0")"
# sh pull.sh
sh update.sh
sh push.sh
cd $currentDir
