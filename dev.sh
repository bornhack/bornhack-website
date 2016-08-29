#!/bin/bash

# Directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if ! [ -f "$DIR/.env" ]
then
	echo "Creating .env file from template..."
	echo "MEDIA_ROOT=\"$DIR/.dev/media\"" > "$DIR/bornhack/settings/.env"
	cat "$DIR/.env_template" >> "$DIR/bornhack/settings/.env"
fi

if ! [ -d "$DIR/.dev" ]
then
	echo "Creating .dev dir for development stuff"
	mkdir -p "$DIR/.dev/media"
fi

python "$DIR/manage.py" $@ --settings=bornhack.settings.development
