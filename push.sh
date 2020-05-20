#!/bin/bash
currentDir=$PWD
cd "$(dirname "$0")"
git add .
git commit -m "Automatic push."
git push
cd $currentDir
