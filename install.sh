#!/bin/bash

set -e

OS="$(uname -s)"
case "$OS" in
  Linux*)  OS_NAME="linux" ;;
  Darwin*) OS_NAME="darwin" ;;
  *)       echo "Unsupported OS: $OS"; exit 1 ;;
esac

ARCH="$(uname -m)"
case "$ARCH" in
  x86_64)  ARCH_NAME="amd64" ;;
  aarch64) ARCH_NAME="arm64" ;;
  arm64)   ARCH_NAME="arm64" ;;
  *)       echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

# macOS on Apple Silicon can report x86_64 under Rosetta

# Since we only build arm64 for macOS, always use arm64 on darwin
if [ "$OS_NAME" = "darwin" ]; then
  ARCH_NAME="arm64"
fi

BINARY_NAME="layergen-${OS_NAME}-${ARCH_NAME}"

echo "Detected platform: ${OS_NAME}/${ARCH_NAME}"
echo "Looking for asset: ${BINARY_NAME}"

LATEST_RELEASE=$(curl -s https://api.github.com/repos/Pablo-Wynistorf/lambda-layergen/releases/latest)

ASSET_URL=$(echo "$LATEST_RELEASE" | grep "browser_download_url" | grep "$BINARY_NAME" | cut -d '"' -f 4)

if [ -z "$ASSET_URL" ]; then
  echo "No binary found for ${OS_NAME}/${ARCH_NAME}."
  echo "Available assets:"
  echo "$LATEST_RELEASE" | grep "browser_download_url" | cut -d '"' -f 4
  exit 1
fi

DEST="/usr/local/bin/layergen"

echo "Downloading from: $ASSET_URL"

if [ -w "$(dirname $DEST)" ]; then
  curl -sL "$ASSET_URL" -o "$DEST"
  chmod +x "$DEST"
else
  echo "Requesting sudo to install to $DEST"
  sudo curl -sL "$ASSET_URL" -o "$DEST"
  sudo chmod +x "$DEST"
fi

echo "layergen has been installed to $DEST"
echo "Run 'layergen --help' to get started."
