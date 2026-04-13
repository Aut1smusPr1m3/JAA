[CmdletBinding()]
param(
    [string]$VenvPath = ".venv",
    [switch]$InstallOpen3D = $true,
    [switch]$RequireSyclGpu,
    [switch]$InstallDev,
    [string]$ArcWelderPath = "",
    [string]$ArcWelderUrl = "",
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "This bootstrap script is for Windows only."
}

function Test-Command {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Resolve-PythonLauncher {
    $candidates = @(
        @{ Exe = "py"; Args = @("-3.12") },
        @{ Exe = "py"; Args = @("-3.11") },
        @{ Exe = "python"; Args = @() },
        @{ Exe = "python3"; Args = @() }
    )

    foreach ($candidate in $candidates) {
        if (-not (Test-Command $candidate.Exe)) {
            continue
        }

        try {
            & $candidate.Exe @($candidate.Args + @("--version")) | Out-Null
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        }
        catch {
        }
    }

    throw "No compatible Python launcher found. Install Python 3.11 or 3.12 first."
}

function Ensure-ArcWelder {
    param(
        [string]$RepoRoot,
        [string]$SourcePath,
        [string]$DownloadUrl
    )

    $target = Join-Path $RepoRoot "ArcWelder.exe"
    if (Test-Path $target) {
        Write-Host "[INFO] ArcWelder already present at $target"
        return
    }

    if ($SourcePath) {
        if (-not (Test-Path $SourcePath)) {
            throw "ArcWelderPath does not exist: $SourcePath"
        }
        Copy-Item -Path $SourcePath -Destination $target -Force
        Write-Host "[INFO] ArcWelder copied from local path"
    }
    elseif ($DownloadUrl) {
        Write-Host "[INFO] Downloading ArcWelder.exe from URL"
        Invoke-WebRequest -Uri $DownloadUrl -OutFile $target
    }
    else {
        throw "ArcWelder.exe not found. Provide -ArcWelderPath or -ArcWelderUrl."
    }

    if (-not (Test-Path $target)) {
        throw "ArcWelder provisioning failed."
    }

    $size = (Get-Item $target).Length
    if ($size -le 0) {
        throw "ArcWelder.exe is empty after provisioning."
    }
}

function Invoke-Open3DSyclCheck {
    param(
        [string]$PythonExe,
        [switch]$RequireGpu
    )

    $checkScript = @"
import importlib.util
import platform
import sys

if importlib.util.find_spec("open3d") is None:
    print("[WARN] Open3D not installed; skipping SYCL capability check")
    sys.exit(2)

import open3d

if not hasattr(open3d.core, "sycl"):
    print("[WARN] Open3D runtime does not expose SYCL backend")
    sys.exit(3)

try:
    devices = [str(d) for d in open3d.core.sycl.get_available_devices()]
except Exception as exc:
    print(f"[WARN] Failed to query SYCL devices: {exc}")
    sys.exit(4)

try:
    sycl0_available = bool(open3d.core.sycl.is_available(open3d.core.Device("SYCL:0")))
except Exception as exc:
    print(f"[WARN] Failed to check SYCL:0 availability: {exc}")
    sys.exit(6)

gpu_devices = [d for d in devices if "gpu" in d.lower()]
print(f"[INFO] Host platform: {platform.system()} {platform.release()}")
print(f"[INFO] SYCL devices: {devices if devices else 'none'}")
print(f"[INFO] SYCL:0 available: {sycl0_available}")
print(f"[INFO] SYCL GPU candidates: {gpu_devices if gpu_devices else 'none'}")

if platform.system().lower() == "windows" and not gpu_devices:
    print("[WARN] Open3D upstream SYCL Python wheels are Linux-focused (Ubuntu 22.04+). Windows SYCL GPU usually requires a custom Open3D/SYCL toolchain build.")

sys.exit(0 if (sycl0_available and gpu_devices) else 5)
"@

    & $PythonExe -c $checkScript
    $checkExitCode = $LASTEXITCODE

    if ($checkExitCode -eq 0) {
        return
    }

    if ($RequireGpu) {
        throw "SYCL GPU check failed. Use Open3D SYCL setup guidance (Linux x86_64 wheel/runtime or custom build), install correct GPU drivers, and ensure at least one SYCL GPU device is available."
    }

    Write-Host "[WARN] SYCL GPU not available; Stage 2 will use CPU fallback unless SYCL runtime/devices are installed."
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptRoot "..\..\")).Path
Set-Location $repoRoot

Write-Host "[INFO] Repo root: $repoRoot"

$pythonLauncher = Resolve-PythonLauncher
Write-Host "[INFO] Python launcher: $($pythonLauncher.Exe) $($pythonLauncher.Args -join ' ')"

$venvAbsolute = Join-Path $repoRoot $VenvPath
$venvPython = Join-Path $venvAbsolute "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "[INFO] Creating virtual environment at $venvAbsolute"
    & $pythonLauncher.Exe @($pythonLauncher.Args + @("-m", "venv", $venvAbsolute))
}
else {
    Write-Host "[INFO] Reusing existing virtual environment at $venvAbsolute"
}

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment python not found: $venvPython"
}

Write-Host "[INFO] Installing dependencies"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt

if ($InstallOpen3D) {
    & $venvPython -m pip install -r requirements-optional.txt
}

if ($InstallDev) {
    & $venvPython -m pip install -r requirements-dev.txt
}

Ensure-ArcWelder -RepoRoot $repoRoot -SourcePath $ArcWelderPath -DownloadUrl $ArcWelderUrl

New-Item -ItemType Directory -Path (Join-Path $repoRoot "stl_models") -Force | Out-Null

Write-Host "[INFO] Running bootstrap smoke checks"
& $venvPython -c "import importlib.util, numpy; print('numpy', numpy.__version__); print('open3d', bool(importlib.util.find_spec('open3d')))"

if ($InstallOpen3D) {
    Write-Host "[INFO] Running Open3D SYCL capability check"
    Invoke-Open3DSyclCheck -PythonExe $venvPython -RequireGpu:$RequireSyclGpu
}

if (-not $SkipTests -and $InstallDev) {
    & $venvPython -m pytest -q -r s
}
elseif (-not $SkipTests) {
    Write-Host "[WARN] Tests skipped because -InstallDev was not set."
}

Write-Host ""
Write-Host "[SUCCESS] Windows bootstrap completed."
Write-Host "Activate venv: $VenvPath\Scripts\Activate.ps1"
Write-Host "Run tests: $VenvPath\Scripts\python.exe -m pytest -q -r s"
