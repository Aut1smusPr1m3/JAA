from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
BOOTSTRAP_PS1 = REPO_ROOT / "scripts" / "windows" / "bootstrap.ps1"
REQ_WINDOWS = REPO_ROOT / "requirements-windows.txt"


def _non_comment_lines(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def test_requirements_windows_contract_is_explicit():
    lines = _non_comment_lines(REQ_WINDOWS)
    assert "-r requirements.txt" in lines
    assert "-r requirements-optional.txt" in lines


def test_bootstrap_default_and_optional_install_logic_match_windows_requirements():
    script = BOOTSTRAP_PS1.read_text(encoding="utf-8")

    # Default behavior should include optional Stage 2 dependency install path.
    assert "[switch]$InstallOpen3D = $true" in script
    assert "[switch]$RequireSyclGpu" in script
    assert "& $venvPython -m pip install -r requirements.txt" in script
    assert "if ($InstallOpen3D)" in script
    assert "& $venvPython -m pip install -r requirements-optional.txt" in script
    assert "[INFO] Running Open3D SYCL capability check" in script
    assert "Invoke-Open3DSyclCheck -PythonExe $venvPython -RequireGpu:$RequireSyclGpu" in script
    assert "open3d.core.sycl.is_available(open3d.core.Device(\"SYCL:0\"))" in script
    assert "[INFO] SYCL:0 available:" in script
