$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$python = Join-Path $root '.venv/Scripts/python.exe'
if (!(Test-Path $python)) { throw 'Run setup instructions in docs/SETUP.md first.' }
$api = Start-Process -FilePath $python -ArgumentList '-m','uvicorn','apps.api.app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $root -WindowStyle Hidden -PassThru
try { Set-Location (Join-Path $root 'apps/web'); node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort } finally { Stop-Process -Id $api.Id -ErrorAction SilentlyContinue }
