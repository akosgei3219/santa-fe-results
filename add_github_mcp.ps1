# Register GitHub's hosted MCP server with the claude CLI, using the
# GITHUB_PAT from .env. See GITHUB_MCP_SETUP.md.
$ErrorActionPreference = "Stop"

if (-not (Test-Path .env)) {
    throw ".env not found - copy .env.example to .env and set GITHUB_PAT"
}

$line = Get-Content .env | Select-String '^\s*GITHUB_PAT\s*=' | Select-Object -First 1
if (-not $line) {
    throw "GITHUB_PAT is missing from .env"
}

$pat = ($line.Line -split '=', 2)[1].Trim().Trim('"').Trim("'")
if (-not $pat) {
    throw "GITHUB_PAT is empty in .env"
}

$config = @{
    type    = "http"
    url     = "https://api.githubcopilot.com/mcp/"
    headers = @{ Authorization = "Bearer $pat" }
} | ConvertTo-Json -Compress

claude mcp add-json github $config
Write-Host "Registered 'github' MCP server. Verify with: claude mcp list"
