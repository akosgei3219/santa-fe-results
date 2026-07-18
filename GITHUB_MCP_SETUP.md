# Adding GitHub's MCP server to the claude CLI

Alongside this repo's own MCP server, you can register GitHub's hosted MCP
server (`https://api.githubcopilot.com/mcp/`) so Claude can read issues, PRs,
and code on your behalf. The token lives in `.env` — the same file the race
backends use — so it never ends up in a committed config.

## One-time setup

1. Create a fine-grained personal access token at
   <https://github.com/settings/personal-access-tokens>. Scope it to just the
   repos and permissions you actually want Claude to have.
2. Copy `.env.example` to `.env` (if you haven't already) and set:

   ```
   GITHUB_PAT=github_pat_...
   ```

3. Run the helper for your shell, from this folder:

   ```bash
   ./add_github_mcp.sh          # macOS / Linux
   ```

   ```powershell
   .\add_github_mcp.ps1         # Windows PowerShell
   ```

4. Verify:

   ```bash
   claude mcp list
   ```

Both scripts just read `GITHUB_PAT` out of `.env` (trimming quotes and
whitespace) and run `claude mcp add-json github` with an HTTP transport and a
`Bearer` auth header. If you'd rather do it by hand, that one-liner is all
there is to it — note the trailing slash on the URL.

## Notes

- `claude mcp add-json` stores the header (token included) in the claude CLI's
  local config, scoped to this project by default. Rotate the PAT like any
  other credential; re-run the script after rotating.
- To remove it: `claude mcp remove github`.
- `.env` is gitignored — keep it that way. Never paste the PAT directly into
  a committed file such as `claude_desktop_config.example.json`.
