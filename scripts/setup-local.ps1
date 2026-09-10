$ErrorActionPreference = "Stop"

py -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,windows]"

Write-Host "Microcredential Video Generator local environment ready."
Write-Host "Next: read .\docs\USER_MANUAL.md, configure Gemini and TTS credentials, and run microvid with an explicit --source DOCX path."
