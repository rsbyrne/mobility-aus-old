#!/bin/bash
currentDir=$PWD
cd "$(dirname "$0")"
git add .
git commit -m "Automatic push."
git fetch
git merge -m "Automatic merge."
git push
cd $currentDir
