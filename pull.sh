#!/bin/bash
CREDENTIALS=` cat .credentials.txt `
SCRIPT='./../fbapi/fb_pull.sh'
URLROOT='https://www.facebook.com/geoinsights-portal/downloads/?id='
cat fbids.txt | while read line
do
echo '---'
echo $SCRIPT
echo $URLROOT$line
echo $CREDENTIALS
echo $PWD'/data/'$line
chmod -R 777 *
sh $SCRIPT $URLROOT$line $CREDENTIALS $PWD'/data/'$line
chmod -R 777 *
done