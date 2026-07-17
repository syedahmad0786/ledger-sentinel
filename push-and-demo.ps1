Set-Location $PSScriptRoot
git config core.longpaths true
Remove-Item .git\HEAD.lock, .git\objects\maintenance.lock -Force -ErrorAction SilentlyContinue
git add -A
git -c user.name="Ahmad Bukhari" -c user.email="ahmadbukhari4245@gmail.com" commit -m "Live-verified on Windows: wording fix + run helpers" 2>&1 | Select-Object -Last 1
gh repo create syedahmad0786/ledger-sentinel --public --description "Forensic screening for SMB ledgers: Benford's Law + threshold clustering + Isolation Forest detect, LLM explains. No API keys. Live Streamlit demo." 2>&1 | Select-Object -Last 1
git remote remove origin 2>$null
git remote add origin https://github.com/syedahmad0786/ledger-sentinel.git
git push -u origin main 2>&1 | Select-Object -Last 2
# visible demo window on port 8511
Start-Process powershell -ArgumentList '-NoExit','-Command',"cd '$PSScriptRoot'; `$env:PYTHONUTF8='1'; streamlit run demo/streamlit_app.py --server.port 8511 --server.headless true"
"pushed + demo launching on http://localhost:8511"
