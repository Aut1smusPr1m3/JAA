[CmdletBinding()]
param(
    [string]$VenvPath = ".venv",
    [switch]$InstallOpen3D = $true,
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
