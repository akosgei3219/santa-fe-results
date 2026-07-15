#!/bin/sh
# Build the static leaderboard client.
#
# Generates the static publish directory from leaderboard.html, injecting:
#   1. the backend URLs, so the client fetches cross-origin instead of same-origin
#   2. a minimal header bar linking back to the main WordPress site
#
# leaderboard.html reads window.LEADERBOARD_URL / window.RESULT_URL at
# script-parse time and falls back to same-origin "/leaderboard.json" and
# "/result.json". The Docker web service serves that file directly from disk
# and relies on the same-origin fallback, so this script must not modify it —
# it only ever writes into the output directory.
#
# That constraint is also what keeps the header out of the iframe embed: the
# header exists only in the built output, so /leaderboard (served by
# server.py from leaderboard.html) stays header-free and the embed on
# santafehalfmarathon.com does not grow a nav bar inside itself.
#
# Usage: sh build_static.sh
# Env:   BACKEND_URL   backend origin, no trailing slash
#        HOME_URL      main site, linked from the header
#        PUBLISH_DIR   output directory (default: public)

set -eu

BACKEND_URL="${BACKEND_URL:-https://santa-fe-results.onrender.com}"
HOME_URL="${HOME_URL:-https://santafehalfmarathon.com}"
PUBLISH_DIR="${PUBLISH_DIR:-public}"
SRC="leaderboard.html"

if [ ! -f "$SRC" ]; then
  echo "build_static.sh: $SRC not found (run from the repo root)" >&2
  exit 1
fi

# Strip any trailing slash so the injected URLs don't end up doubled.
BACKEND_URL="${BACKEND_URL%/}"
HOME_URL="${HOME_URL%/}"

rm -rf "$PUBLISH_DIR"
mkdir -p "$PUBLISH_DIR"

# --- head injection -------------------------------------------------------
# Config must land before the inline script at the bottom of the page, which
# reads the two globals at parse time. Anything after that point is ignored.
#
# Brand palette: Espresso #20140E ground, Cream #F5EBD8 text,
# Amber #FFCE6B hover, Terracotta #BE4824 focus ring.
CONFIG="<script>window.LEADERBOARD_URL=\"${BACKEND_URL}/leaderboard.json\";window.RESULT_URL=\"${BACKEND_URL}/result.json\";</script>"

STYLE="<style>.sitebar{background:#20140E;border-bottom:1px solid #3A2A20}.sitebar__inner{max-width:680px;margin:0 auto;padding:12px 16px}.sitebar__home{display:inline-block;color:#F5EBD8;text-decoration:none;font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;font-size:14px;font-weight:600;letter-spacing:.2px;border-radius:4px}.sitebar__home:hover{color:#FFCE6B}.sitebar__home:focus-visible{outline:2px solid #BE4824;outline-offset:3px}</style>"

# --- body injection -------------------------------------------------------
# The ampersand in the &#8592; (left arrow) entity is escaped as \& because an
# unescaped & in a sed replacement expands to the whole matched text — it would
# render the link as "<body>#8592; Santa Fe Half Marathon". Using the entity
# rather than a literal arrow keeps this script pure ASCII, so no locale or
# encoding assumptions ride along into Render's builder.
HEADER="<header class=\"sitebar\"><div class=\"sitebar__inner\"><a class=\"sitebar__home\" href=\"${HOME_URL}\">\&#8592; Santa Fe Half Marathon</a></div></header>"

sed \
  -e "s|</head>|${CONFIG}${STYLE}</head>|" \
  -e "s|<body>|<body>${HEADER}|" \
  "$SRC" > "$PUBLISH_DIR/index.html"

# --- verify ---------------------------------------------------------------
# Fail loudly rather than publishing a client that silently points at itself
# or ships a half-injected header.
if ! grep -q "window.LEADERBOARD_URL=" "$PUBLISH_DIR/index.html"; then
  echo "build_static.sh: config injection failed — no </head> in $SRC?" >&2
  exit 1
fi

if ! grep -q "class=\"sitebar\"" "$PUBLISH_DIR/index.html"; then
  echo "build_static.sh: header injection failed — no <body> in $SRC?" >&2
  exit 1
fi

if ! grep -q "sitebar__home" "$PUBLISH_DIR/index.html"; then
  echo "build_static.sh: header styles missing from output" >&2
  exit 1
fi

echo "build_static.sh: wrote $PUBLISH_DIR/index.html"
echo "  backend -> $BACKEND_URL"
echo "  home    -> $HOME_URL"
