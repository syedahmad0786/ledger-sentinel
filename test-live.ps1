Set-Location $PSScriptRoot
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
pip install scikit-learn --quiet 2>&1 | Select-Object -Last 1
python cli.py 2>&1 | Tee-Object -FilePath "$env:TEMP\ledger.log" | Select-Object -Last 16
