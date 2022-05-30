#!/bin/sh
# Convert images to thumbnail png, named with ".png" appended to the original name.
# If the image is already a thumbnail, don't create a new one.

find src/static_src/img/bornhack-* \
  -type f \
  -and \( -iname '*.jpg' -or -iname '*.png' \) \
  -and -not -name 'thumbnail_*' -and -not -path '*/logo/*' \
  -execdir convert -geometry 200 "{}" "thumbnail_{}.png" \;
