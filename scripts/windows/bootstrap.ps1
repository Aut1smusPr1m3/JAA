[CmdletBinding()]
param(
    [string]$VenvPath = ".venv",
    [switch]$InstallOpen3D = $true,
    [switch]$RequireSyclGpu,
    [switch]$UseBundledWheels,
    [string]$WheelhousePath = "wheels",
    [string]$Open3DWheelPath = "",
    [switch]$SetupSyclToolchain,
    [switch]$BuildOpen3DSyclWithWsl,
    [switch]$InstallOneApiBaseToolkit,
    [string]$WslDistro = "Ubuntu",
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

function Resolve-RepoScopedPath {
    param(
        [string]$RepoRoot,
        [string]$InputPath
    )

    if (-not $InputPath) {
        return ""
    }

    if ([System.IO.Path]::IsPathRooted($InputPath)) {
        return $InputPath
    }

    return Join-Path $RepoRoot $InputPath
}

function Install-OneApiBaseToolkitIfRequested {
    param([switch]$InstallToolkit)

    $setvarsPath = Join-Path ${env:ProgramFiles(x86)} "Intel\oneAPI\setvars.bat"
    if (Test-Path $setvarsPath) {
        return $setvarsPath
    }

    if (-not $InstallToolkit) {
        return $null
    }

    if (-not (Test-Command "winget")) {
        throw "oneAPI not found and winget is unavailable. Install Intel oneAPI Base Toolkit manually, then retry."
    }

    Write-Host "[INFO] Installing Intel oneAPI Base Toolkit via winget"
    $candidateIds = @(
        "Intel.oneAPI.BaseToolkit",
        "Intel.oneAPI.BaseKit"
    )

    $installed = $false
    foreach ($id in $candidateIds) {
        & winget install --id $id -e --accept-source-agreements --accept-package-agreements
        if ($LASTEXITCODE -eq 0) {
            $installed = $true
            break
        }
    }

    if (-not $installed) {
        throw "Failed to install Intel oneAPI Base Toolkit via winget. Install it manually and retry."
    }

    if (-not (Test-Path $setvarsPath)) {
        throw "oneAPI installation did not expose setvars.bat at expected path: $setvarsPath"
    }

    return $setvarsPath
}

function Invoke-OneApiSyclProbe {
    param([switch]$InstallToolkit)

    $setvarsPath = Install-OneApiBaseToolkitIfRequested -InstallToolkit:$InstallToolkit
    if (-not $setvarsPath) {
        Write-Host "[WARN] oneAPI setvars.bat not found; skipping oneAPI SYCL probe"
        return
    }

    $syclCommand = "call \"$setvarsPath\" >nul 2>nul && sycl-ls"
    $output = & cmd.exe /d /c $syclCommand 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to run sycl-ls after oneAPI environment setup. Ensure oneAPI installation is complete."
    }

    Write-Host "[INFO] oneAPI SYCL probe completed"
    if ($output -match '(?im)gpu') {
        Write-Host "[INFO] sycl-ls reports GPU-capable SYCL devices"
    }
    else {
        Write-Host "[WARN] sycl-ls did not report GPU-capable devices. Install/verify your GPU runtime stack."
    }

    $gpuNames = (Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
    if ($gpuNames -match 'NVIDIA') {
        Write-Host "[INFO] NVIDIA GPU detected. This bootstrap does not install or modify NVIDIA GPU drivers."
    }
}

function Convert-WindowsPathToWslPath {
    param([string]$WindowsPath)

    $fullPath = [System.IO.Path]::GetFullPath($WindowsPath)
    if ($fullPath -match '^([A-Za-z]):\\(.*)$') {
        $drive = $matches[1].ToLowerInvariant()
        $rest = $matches[2] -replace '\\', '/'
        return "/mnt/$drive/$rest"
    }

    throw "Failed to convert Windows path to WSL path: $WindowsPath"
}

function Invoke-Open3DSyclBuildViaWsl {
    param(
        [string]$RepoRoot,
        [string]$Distro
    )

    if (-not (Test-Command "wsl")) {
        throw "wsl.exe not found. Install WSL (wsl --install -d $Distro) and retry."
    }

    $repoRootWsl = Convert-WindowsPathToWslPath -WindowsPath $RepoRoot
    $wslCommand = "set -euo pipefail; cd '$repoRootWsl'; bash scripts/linux/build_open3d_sycl_from_source.sh"

    Write-Host "[INFO] Building Open3D SYCL from source in WSL distro '$Distro'"
    & wsl.exe -d $Distro -- bash -lc $wslCommand
    if ($LASTEXITCODE -ne 0) {
        throw "WSL Open3D SYCL build failed. Check WSL output and required runtime/toolchain dependencies."
    }

    Write-Host "[INFO] WSL Open3D SYCL build completed"
}

function Invoke-WindowsSyclToolchainSetup {
    param(
        [string]$RepoRoot,
        [switch]$InstallToolkit,
        [switch]$BuildWithWsl,
        [string]$Distro
    )

    Write-Host "[INFO] Starting Windows SYCL toolchain setup"
    Write-Host "[INFO] Note: NVIDIA GPU drivers are never modified by this bootstrap."

    Invoke-OneApiSyclProbe -InstallToolkit:$InstallToolkit

    if ($BuildWithWsl) {
        Invoke-Open3DSyclBuildViaWsl -RepoRoot $RepoRoot -Distro $Distro
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

if ($SetupSyclToolchain) {
    Invoke-WindowsSyclToolchainSetup `
        -RepoRoot $repoRoot `
        -InstallToolkit:$InstallOneApiBaseToolkit `
        -BuildWithWsl:$BuildOpen3DSyclWithWsl `
        -Distro $WslDistro
}

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

$resolvedWheelhouse = Resolve-RepoScopedPath -RepoRoot $repoRoot -InputPath $WheelhousePath
$resolvedOpen3DWheel = Resolve-RepoScopedPath -RepoRoot $repoRoot -InputPath $Open3DWheelPath

if ($UseBundledWheels) {
    if (-not (Test-Path $resolvedWheelhouse)) {
        throw "Bundled wheelhouse not found: $resolvedWheelhouse"
    }

    Write-Host "[INFO] Installing from bundled wheelhouse: $resolvedWheelhouse"
    & $venvPython -m pip install --no-index --find-links $resolvedWheelhouse -r requirements.txt

    if ($InstallOpen3D) {
        if ($resolvedOpen3DWheel) {
            if (-not (Test-Path $resolvedOpen3DWheel)) {
                throw "Open3DWheelPath does not exist: $resolvedOpen3DWheel"
            }
            Write-Host "[INFO] Installing Open3D from custom wheel: $resolvedOpen3DWheel"
            & $venvPython -m pip install $resolvedOpen3DWheel
        }
        else {
            & $venvPython -m pip install --no-index --find-links $resolvedWheelhouse -r requirements-optional.txt
        }
    }

    if ($InstallDev) {
        & $venvPython -m pip install --no-index --find-links $resolvedWheelhouse -r requirements-dev.txt
    }
}
else {
    & $venvPython -m pip install -r requirements.txt

    if ($InstallOpen3D) {
        if ($resolvedOpen3DWheel) {
            if (-not (Test-Path $resolvedOpen3DWheel)) {
                throw "Open3DWheelPath does not exist: $resolvedOpen3DWheel"
            }
            Write-Host "[INFO] Installing Open3D from custom wheel: $resolvedOpen3DWheel"
            & $venvPython -m pip install $resolvedOpen3DWheel
        }
        else {
            & $venvPython -m pip install -r requirements-optional.txt
        }
    }

    if ($InstallDev) {
        & $venvPython -m pip install -r requirements-dev.txt
    }
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
