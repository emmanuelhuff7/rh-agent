#!/bin/bash
# Builds QuickPlayer.app directly with swiftc (SwiftPM's manifest linking
# is broken on this machine's Command Line Tools install, so we skip it).
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="$DIR/QuickPlayer.app"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS"
cp "$DIR/Info.plist" "$APP/Contents/Info.plist"

swiftc -O \
    -o "$APP/Contents/MacOS/QuickPlayer" \
    "$DIR"/Sources/QuickPlayer/*.swift

echo "Built $APP"
