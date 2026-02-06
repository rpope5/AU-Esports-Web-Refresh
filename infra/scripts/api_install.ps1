$ErrorActionPreference = "Stop"

Set-Location -Path "$PSScriptRoot\..\..\apps\api"

if (!(Test-Path ".venv")) {
  py -3.11 -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -r requirements.txt
Write-Host "API dependencies installed."
