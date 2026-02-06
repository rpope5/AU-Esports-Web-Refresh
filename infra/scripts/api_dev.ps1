$ErrorActionPreference = "Stop"

Set-Location -Path "$PSScriptRoot\..\..\apps\api"

if (!(Test-Path ".venv")) {
  py -3.11 -m venv .venv
}

& .\.venv\Scripts\pip.exe install -r requirements.txt
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
