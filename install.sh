#!/bin/bash
URL="https://raw.githubusercontent.com/Pablo-Wynistorf/lambda-layergen/prod/layergen"
DEST="/usr/local/bin/layergen"

curl -L $URL -o $DEST

chmod +x $DEST

echo "layergen has been installed to $DEST"