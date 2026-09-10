$ErrorActionPreference = "Stop"

py -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,windows]"

Write-Host "Local environment ready."
Write-Host "Copy the corrected Lab 101 DOCX into .\source and run the command shown in README.md."
