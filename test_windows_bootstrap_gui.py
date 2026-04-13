from pathlib import Path

from scripts.windows.bootstrap_gui import build_bootstrap_command


def test_build_bootstrap_command_defaults():
    repo_root = Path("/repo")
    cmd = build_bootstrap_command(
        repo_root=repo_root,
        install_dev=True,
        install_open3d=True,
        require_sycl_gpu=False,
        skip_tests=False,
        venv_path=".venv",
        arcwelder_path="",
        arcwelder_url="",
    )

    assert "-InstallDev" in cmd
    assert "-InstallOpen3D:$false" not in cmd
    assert "-RequireSyclGpu" not in cmd
    assert "-SkipTests" not in cmd
    assert "-VenvPath" in cmd
    assert ".venv" in cmd


def test_build_bootstrap_command_optional_switches():
    repo_root = Path("/repo")
    cmd = build_bootstrap_command(
        repo_root=repo_root,
        install_dev=False,
        install_open3d=False,
        require_sycl_gpu=True,
        skip_tests=True,
        venv_path=".venv-win",
        arcwelder_path="C:/tmp/ArcWelder.exe",
        arcwelder_url="",
    )

    assert "-InstallDev" not in cmd
    assert "-InstallOpen3D:$false" in cmd
    assert "-RequireSyclGpu" in cmd
    assert "-SkipTests" in cmd
    assert ".venv-win" in cmd
    assert "-ArcWelderPath" in cmd


def test_build_bootstrap_command_uses_url_when_path_missing():
    repo_root = Path("/repo")
    cmd = build_bootstrap_command(
        repo_root=repo_root,
        install_dev=True,
        install_open3d=True,
        require_sycl_gpu=False,
        skip_tests=False,
        venv_path=".venv",
        arcwelder_path="",
        arcwelder_url="https://example.com/ArcWelder.exe",
    )

    assert "-ArcWelderPath" not in cmd
    assert "-ArcWelderUrl" in cmd
