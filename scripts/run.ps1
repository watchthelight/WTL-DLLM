# wtl-dllm · scripts/run.ps1
# what: one command up — server (real ckpt if present, else stub) + vite dev
# by:   <wtl> watchthelight

param(
    [switch]$Build,
    [string]$Ckpt = ""
)

$root = Split-Path $PSScriptRoot -Parent
$py = Join-Path $root ".venv\Scripts\python.exe"

if (-not $Ckpt) {
    $latest = Get-ChildItem (Join-Path $root "runs\ckpt") -Recurse -Filter "step*.pt" -ErrorAction SilentlyContinue |
        Where-Object { $_.Directory.Name -like "*diffusion*" } |
        Sort-Object LastWriteTime | Select-Object -Last 1
    if ($latest) { $Ckpt = $latest.FullName }
}

$serverArgs = @("-m", "dllm.serve.app")
if ($Ckpt) {
    Write-Host "model: $Ckpt"
    $serverArgs += @("--ckpt", $Ckpt)
} else {
    Write-Host "no checkpoint found - serving the STUB model" -ForegroundColor Yellow
    $serverArgs += "--stub"
}

$server = Start-Process -FilePath $py -ArgumentList $serverArgs -WorkingDirectory $root -PassThru -NoNewWindow

try {
    if ($Build) {
        Push-Location (Join-Path $root "ui")
        npm run build
        npm run preview
        Pop-Location
    } else {
        Push-Location (Join-Path $root "ui")
        Write-Host "ui: http://localhost:5173  (server on :7311)"
        npm run dev
        Pop-Location
    }
} finally {
    if ($server -and -not $server.HasExited) { Stop-Process -Id $server.Id -Force }
    Write-Host "server stopped."
}
