from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "windows-aio-release.yml"


def test_windows_release_workflow_builds_wheelhouse():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "python -m pip download --dest $wheelhouseWindows" in text
    assert "python -m pip download --dest $wheelhouseLinux" in text
    assert "--platform win_amd64" in text
    assert "--platform manylinux_2_31_x86_64" in text
    assert "windows_wheel_zip_path" in text
    assert "linux_wheel_zip_path" in text


def test_windows_release_launcher_uses_bundled_wheels():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "scripts\\bootstrap.bat -InstallDev -UseBundledWheels" in text


def test_windows_release_workflow_publishes_wheelhouse_assets():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "Upload Windows wheelhouse artifact" in text
    assert "Upload Linux wheelhouse artifact" in text
    assert "steps.bundle.outputs.windows_wheel_zip_path" in text
    assert "steps.bundle.outputs.linux_wheel_zip_path" in text
