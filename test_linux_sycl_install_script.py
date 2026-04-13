from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
SCRIPT = REPO_ROOT / "scripts" / "linux" / "install_open3d_sycl.sh"
BUILD_SCRIPT = REPO_ROOT / "scripts" / "linux" / "build_open3d_sycl_from_source.sh"


def test_linux_sycl_install_script_exists_and_has_linux_guard():
    text = SCRIPT.read_text(encoding="utf-8")

    assert 'uname -s' in text
    assert 'Linux' in text
    assert 'Open3D SYCL wheels are tested upstream on Ubuntu 22.04+' in text


def test_linux_sycl_install_script_installs_xpu_wheel_and_runs_sycl_checks():
    text = SCRIPT.read_text(encoding="utf-8")

    assert 'open3d_xpu-' in text
    assert 'manylinux_2_31_x86_64.whl' in text
    assert 'o3d.core.sycl.get_available_devices()' in text
    assert 'o3d.core.sycl.is_available(o3d.core.Device("SYCL:0"))' in text


def test_linux_sycl_source_build_script_enables_sycl_module():
    text = BUILD_SCRIPT.read_text(encoding="utf-8")

    assert '-DBUILD_SYCL_MODULE=ON' in text
    assert '-DCMAKE_C_COMPILER=icx' in text
    assert '-DCMAKE_CXX_COMPILER=icpx' in text
    assert 'install-pip-package' in text
    assert 'setvars.sh' in text
