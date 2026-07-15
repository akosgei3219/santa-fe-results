#!/bin/sh
# Build the static leaderboard client.
#
# Generates the static publish directory from leaderboard.html, injecting the
# backend URLs so the client fetches cross-origin instead of same-origin.
#
# leaderboard.html reads window.LEADERBOARD_URL / window.RESULT_URL at
# script-parse time and falls back to same-origin "/leaderboard.json" and
# "/result.json". The Docker web service serves that file directly from disk
# and relies on the same-origin fallback, so this script must not modify it —
# it only ever writes into the output directory.
#
# Usage: ./build_static.sh
# Env:   BACKEND_URL   backend origin (no trailing slash)
#        PUBLISH_DIR   output directory (default: public)

set -eu

BACKEND_URL="${BACKEND_URL:-https://santa-fe-results.onrender.com}"
PUBLISH_DIR="${PUBLISH_DIR:-public}"
SRC="leaderboard.html"

if [ ! -f "$SRC" ]; then
  echo "build_static.sh: $SRC not found (run from the repo root)" >&2
  exit 1
fi

# Strip any trailing slash so the injected URLs don't end up doubled.
BACKEND_URL="${BACKEND_URL%/}"

rm -rf "$PUBLISH_DIR"
mkdir -p "$PUBLISH_DIR"

# Inject the config immediately before </head>, so it runs before the inline
# script at the bottom of the page reads the two globals.
CONFIG="<script>window.LEADERBOARD_URL=\"${BACKEND_URL}/leaderboard.json\";window.RESULT_URL=\"${BACKEND_URL}/result.json\";</script>"

sed "s|</head>|${CONFIG}</head>|" "$SRC" > "$PUBLISH_DIR/index.html"

# Fail loudly rather than publishing a client that silently points at itself.
if ! grep -q "window.LEADERBOARD_URL=" "$PUBLISH_DIR/index.html"; then
  echo "build_static.sh: config injection failed — no </head> in $SRC?" >&2
  exit 1
fi

echo "build_static.sh: wrote $PUBLISH_DIR/index.html -> $BACKEND_URL"
