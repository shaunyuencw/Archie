$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
Set-Location $root
if (!(Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 is required.' }
}
& .venv/Scripts/python.exe -m pip install -r requirements.lock
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
Push-Location apps/web
try {
    if (Get-Command pnpm -ErrorAction SilentlyContinue) { pnpm install --frozen-lockfile }
    elseif (Get-Command corepack.cmd -ErrorAction SilentlyContinue) { corepack.cmd pnpm install --frozen-lockfile }
    else { throw 'Install pnpm 11 (the repository uses pnpm-lock.yaml).' }
    if ($LASTEXITCODE -ne 0) { throw 'Web dependency installation failed.' }
} finally { Pop-Location }
if (!(Test-Path -LiteralPath '.env')) { Copy-Item -LiteralPath '.env.example' -Destination '.env' }
Write-Output 'Ready. Run ./scripts/dev.ps1 and open http://127.0.0.1:5173/.'
