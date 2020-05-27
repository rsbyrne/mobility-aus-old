#!/bin/bash
currentDir=$PWD
cd "$(dirname "$0")"
if [[ $* == *-u* ]]
then
#  echo 'Pulling disabled at present - see cycle.sh'
   echo 'Pulling new data...'
   ./pull.sh
   echo 'Pulled.'
fi
echo 'Updating products...'
./update.sh
echo 'Updated.'
echo 'Pushing to cloud...'
./push.sh
echo 'Pushed.'
echo 'All done.'
cd $currentDir
