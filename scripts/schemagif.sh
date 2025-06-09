#!/bin/sh
#################################
# Loop over migrations in the
# BornHack website project, apply
# one by one, and run
# postgresql_autodoc for each.
#
# Use the generated .dot files
# to generate PNGs and watermark
# the PNG with the migration name.
#
# Finally use $whatever to combine
# all the PNGs to an animation and
# marvel at the ingenuity of Man.
#
# This scripts makes a million
# assumptions about the local env.
# and installed packages. Enjoy!
#
#            /Tykling, April 2018
#################################
#set -x

# warn the user
read -p "WARNING: This scripts deletes and recreates the local pg database named bornhackdb several times. Continue? "

# wipe database
sudo su postgres -c "dropdb bornhackdb; createdb -O bornhack bornhackdb"

# run migrate with --fake to get list of migrations
MIGRATIONS=$(python manage.py migrate --fake | grep FAKED | cut -d " " -f 4 | cut -d "." -f 1-2)

# wipe database again
sudo su postgres -c "dropdb bornhackdb; createdb -O bornhack bornhackdb"

# create output folder
sudo rm -rf postgres_autodoc
mkdir postgres_autodoc
sudo chown postgres:postgres postgres_autodoc

# loop over migrations
COUNTER=0
for MIGRATION in $MIGRATIONS; do
    COUNTER=$(( $COUNTER + 1 ))
    ALFACOUNTER=$(printf "%04d" $COUNTER)

    echo "processing migration #${COUNTER}: $MIG"
    APP=$(echo $MIGRATION | cut -d "." -f 1)
    MIG=$(echo $MIGRATION | cut -d "." -f 2)

    echo "--- running migration: APP: $APP MIGRATION: $MIG ..."
    python manage.py migrate --no-input $APP $MIG

    echo "--- running postgresql_autodoc and dot..."
    cd postgres_autodoc
    sudo su postgres -c "mkdir ${ALFACOUNTER}-$MIGRATION"
    cd "${ALFACOUNTER}-${MIGRATION}"
    # run postgresql_autodoc
    sudo su postgres -c "postgresql_autodoc -d bornhackdb"
    # create PNG from .dot file
    sudo su postgres -c "dot -Tpng bornhackdb.dot -o bornhackdb.png"
    # create watermark image with migration name as white on black text
    sudo su postgres -c "convert -background none -undercolor black -fill white -font DejaVu-Sans-Mono-Bold -size 5316x4260 -pointsize 72 -gravity SouthEast label:${ALFACOUNTER}-${MIGRATION} background.png"
    # combine the images
    sudo su postgres -c "composite -gravity center bornhackdb.png background.png final.png"
    cd ..
    cd ..
done
