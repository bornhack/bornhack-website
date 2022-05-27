#!/bin/sh
# Convert images to thumbnail png, named with ".png" appended to the original name.
# If the image is already a thumbnail, don't create a new one.

set -e
for full_size in "$@"; do
  if test png = "$(echo "$full_size" | sed 's/^.*\.//' | tr '[A-Z]' '[a-z]')"; then
    if ! test -f "$(echo "$full_size" | sed 's/\.[pP][nN][gG]$//')"; then
      thumbnail="$full_size.png"
      if ! test -f "$thumbnail"; then
        convert -geometry 200 "$full_size" "$thumbnail"
      fi
    fi
  fi
done
