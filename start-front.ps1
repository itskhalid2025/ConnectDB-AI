# Start the Next.js frontend. Runs npm install on first run.
$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location (Join-Path $ScriptDir 'frontend')

if (-not (Test-Path 'node_modules')) {
    Write-Host '==> Installing Node.js dependencies'
    npm install
}

if (-not (Test-Path '.env.local') -and (Test-Path '.env.local.example')) {
    Write-Host '==> No .env.local found — copying from .env.local.example'
    Copy-Item '.env.local.example' '.env.local'
}

Write-Host '==> Starting Next.js on http://localhost:3000'
npm run dev
