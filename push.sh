#!/bin/bash
currentDir=$PWD
cd "$(dirname "$0")"
chmod 700 $PWD/.ssh/*
eval `ssh-agent -s`
ssh-add $PWD/.ssh/*.key
git add .
git commit -m "Automatic push."
git fetch
git merge -m "Automatic merge."
git push
cd $currentDir
