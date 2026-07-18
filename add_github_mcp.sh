#!/usr/bin/env bash
# Register GitHub's hosted MCP server with the claude CLI, using the
# GITHUB_PAT from .env. See GITHUB_MCP_SETUP.md.
set -euo pipefail

if [ ! -f .env ]; then
  echo "error: .env not found — copy .env.example to .env and set GITHUB_PAT" >&2
  exit 1
fi

pat=$(grep -E '^[[:space:]]*GITHUB_PAT[[:space:]]*=' .env | head -n 1 | cut -d= -f2-)
pat=$(printf '%s' "$pat" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^["'\'']//' -e 's/["'\'']$//')

if [ -z "$pat" ]; then
  echo "error: GITHUB_PAT is missing or empty in .env" >&2
  exit 1
fi

claude mcp add-json github "{\"type\":\"http\",\"url\":\"https://api.githubcopilot.com/mcp/\",\"headers\":{\"Authorization\":\"Bearer $pat\"}}"
echo "Registered 'github' MCP server. Verify with: claude mcp list"
