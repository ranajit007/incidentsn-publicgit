#!/bin/bash
CURRENT_DIR=`pwd`
#Import seeds
echo " ---> CUSTOM MONGO SEEDS...";
echo "      1. Importing seed data...";
for f in /seed/files/* 
do
    echo "      > Seed: $f";
    mongoimport -d=$MONGO_INITDB_DATABASE -u=incidentUser -p=redhat --file=$f --jsonArray
done
