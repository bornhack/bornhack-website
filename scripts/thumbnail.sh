#!/bin/sh
# Convert images to thumbnail png, named with ".png" appended to the original name.
# If the image is already a thumbnail, don't create a new one.

set -e
for image in "$@"; do
  thumbnail_to_fullsize="$(echo "$image" | sed -e 's/^thumbnail_//' -e 's/\.[pP][nN][gG]$//')"
  fullsize_to_thumbnail="thumbnail_$image.png"
  if ! test -f "$thumbnail_to_fullsize" && ! test -f "$fullsize_to_thumbnail"; then
    convert -geometry 200 "$image" "$fullsize_to_thumbnail"
  fi
done
