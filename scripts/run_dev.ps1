# ==============================================================================
# Development Server Startup Script
# Gujarat Cyber Crime Social Media Intelligence & Early Warning System
# ==============================================================================

param (
    [int]$Port = 8080
)

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " Starting Gujarat Cyber Crime SOC Intelligence Gateway           " -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Activate virtual environment if available
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "[INFO] Activating virtual environment (venv)..." -ForegroundColor Gray
    & ".\venv\Scripts\Activate.ps1"
}

# 2. Check if selected port is available, or find an open fallback
$candidatePorts = @($Port, 8080, 8081, 8001, 5000, 8888)
$targetPort = $null

foreach ($p in $candidatePorts) {
    try {
        $testSocket = New-Object System.Net.Sockets.TcpClient
        $asyncResult = $testSocket.BeginConnect("127.0.0.1", $p, $null, $null)
        $success = $asyncResult.AsyncWaitHandle.WaitOne(200, $false)
        if ($success -and $testSocket.Connected) {
            # Connection succeeded, meaning another process is actively using this port
            $testSocket.Close()
            continue
        } else {
            $testSocket.Close()
            $targetPort = $p
            break
        }
    } catch {
        $targetPort = $p
        break
    }
}

if (-not $targetPort) {
    $targetPort = 8080
}

Write-Host "[INFO] Gateway binding to: http://127.0.0.1:$targetPort/" -ForegroundColor Green
Write-Host "[INFO] Press CTRL+C to stop server." -ForegroundColor Gray
Write-Host "-----------------------------------------------------------------" -ForegroundColor DarkGray

# 3. Launch Uvicorn with auto-reload
python -m uvicorn app.main:app --host 127.0.0.1 --port $targetPort --reload
