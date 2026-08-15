# Live IDS setup for Windows
# Run in PowerShell:  .\install_live_ids.ps1

Write-Host "=== Hybrid IDS - Live Monitor Setup ===" -ForegroundColor Cyan

# 1. Python dependencies
Write-Host "`n[1/3] Installing Python packages..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip install failed. Check Python/pip is on PATH." -ForegroundColor Red
    exit 1
}

# 2. Npcap check (required for Scapy on Windows)
Write-Host "`n[2/3] Checking Npcap (required for packet capture)..." -ForegroundColor Yellow
$npcapPath = "C:\Windows\System32\Npcap\wpcap.dll"
if (Test-Path $npcapPath) {
    Write-Host "Npcap found." -ForegroundColor Green
} else {
    Write-Host "Npcap NOT found." -ForegroundColor Red
    Write-Host "Download and install Npcap from: https://npcap.com/#download"
    Write-Host "During install, enable: 'Install Npcap in WinPcap API-compatible Mode'"
}

# 3. Verify Scapy can list interfaces
Write-Host "`n[3/3] Verifying Scapy..." -ForegroundColor Yellow
python -c "from scapy.all import get_if_list; ifs=get_if_list(); print('Interfaces:', ifs if ifs else '(none - run as Administrator?)')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Scapy verification failed." -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Setup complete ===" -ForegroundColor Green
Write-Host "Train models first:  python preprocessing.py && python hybrid_ids_model.py"
Write-Host "Start live monitor:  python live_monitor.py --list-interfaces"
Write-Host "                     python live_monitor.py --interface `"Wi-Fi`""
Write-Host "`nRun PowerShell as Administrator for packet capture." -ForegroundColor Yellow
