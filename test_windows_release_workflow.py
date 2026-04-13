from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "windows-aio-release.yml"


def test_windows_release_workflow_builds_wheelhouse():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "python -m pip download --dest $wheelhouse -r requirements.txt" in text
    assert "python -m pip download --dest $wheelhouse -r requirements-optional.txt" in text
    assert "python -m pip download --dest $wheelhouse -r requirements-dev.txt" in text


def test_windows_release_launcher_uses_bundled_wheels():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "scripts\\bootstrap.bat -InstallDev -UseBundledWheels" in text
