#!/bin/bash
currentDir=$PWD
cd "$(dirname "$0")"
sh update.sh
sh push.sh
cd $currentDir
