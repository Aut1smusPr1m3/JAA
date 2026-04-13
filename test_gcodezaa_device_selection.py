#!/usr/bin/env python3
"""Tests for Stage 2 raycasting device selection and fallback behavior."""

import sys

import pytest

sys.path.insert(0, "GCodeZAA")

from gcodezaa import process


def test_resolve_device_auto_prefers_sycl_when_gpu_available(monkeypatch):
    monkeypatch.setenv("GCODEZAA_RAYCAST_DEVICE", "auto")
    monkeypatch.setenv("GCODEZAA_REQUIRE_GPU", "0")
    monkeypatch.setattr(process, "_sycl_gpu_available", lambda: True)

    assert process.resolve_raycast_device_spec() == "SYCL:0"


def test_resolve_device_auto_falls_back_to_cpu(monkeypatch):
    monkeypatch.setenv("GCODEZAA_RAYCAST_DEVICE", "auto")
    monkeypatch.setenv("GCODEZAA_REQUIRE_GPU", "0")
    monkeypatch.setattr(process, "_sycl_gpu_available", lambda: False)

    assert process.resolve_raycast_device_spec() == "CPU:0"


def test_resolve_device_sycl_falls_back_without_gpu(monkeypatch):
    monkeypatch.setenv("GCODEZAA_RAYCAST_DEVICE", "sycl:0")
    monkeypatch.setenv("GCODEZAA_REQUIRE_GPU", "0")
    monkeypatch.setattr(process, "_sycl_gpu_available", lambda: False)

    assert process.resolve_raycast_device_spec() == "CPU:0"


def test_resolve_device_sycl_raises_when_gpu_required(monkeypatch):
    monkeypatch.setenv("GCODEZAA_RAYCAST_DEVICE", "sycl:0")
    monkeypatch.setenv("GCODEZAA_REQUIRE_GPU", "1")
    monkeypatch.setattr(process, "_sycl_gpu_available", lambda: False)

    with pytest.raises(RuntimeError):
        process.resolve_raycast_device_spec()


def test_resolve_device_cuda_aliases_to_sycl(monkeypatch):
    monkeypatch.setenv("GCODEZAA_RAYCAST_DEVICE", "cuda")
    monkeypatch.setenv("GCODEZAA_REQUIRE_GPU", "0")
    monkeypatch.setattr(process, "_sycl_gpu_available", lambda: True)

    assert process.resolve_raycast_device_spec() == "SYCL:0"


def test_resolve_device_auto_logs_cpu_fallback(monkeypatch, caplog):
    caplog.set_level("INFO")
    monkeypatch.setenv("GCODEZAA_RAYCAST_DEVICE", "auto")
    monkeypatch.setenv("GCODEZAA_REQUIRE_GPU", "0")
    monkeypatch.setattr(process, "_sycl_gpu_available", lambda: False)

    assert process.resolve_raycast_device_spec() == "CPU:0"
    assert "Raycast device resolved: AUTO -> CPU:0" in caplog.text


def test_resolve_device_cpu_logs_explicit_selection(monkeypatch, caplog):
    caplog.set_level("INFO")
    monkeypatch.setenv("GCODEZAA_RAYCAST_DEVICE", "cpu:0")
    monkeypatch.setenv("GCODEZAA_REQUIRE_GPU", "0")

    assert process.resolve_raycast_device_spec() == "CPU:0"
    assert "Raycast device resolved: CPU:0" in caplog.text


def test_sycl_gpu_available_requires_gpu_device_and_sycl0(monkeypatch):
    class _FakeSycl:
        @staticmethod
        def get_available_devices():
            return ["SYCL GPU 0", "SYCL CPU 0"]

        @staticmethod
        def is_available(_device):
            return True

    class _FakeDevice:
        def __init__(self, spec):
            self.spec = spec

    fake_open3d = type(
        "FakeOpen3D",
        (),
        {"core": type("FakeCore", (), {"sycl": _FakeSycl, "Device": _FakeDevice})},
    )
    monkeypatch.setattr(process, "open3d", fake_open3d)

    assert process._sycl_gpu_available() is True


def test_sycl_gpu_available_rejects_host_only_fallback(monkeypatch):
    class _FakeSycl:
        @staticmethod
        def get_available_devices():
            return ["SYCL host device", "SYCL CPU 0"]

        @staticmethod
        def is_available(_device):
            return True

    class _FakeDevice:
        def __init__(self, spec):
            self.spec = spec

    fake_open3d = type(
        "FakeOpen3D",
        (),
        {"core": type("FakeCore", (), {"sycl": _FakeSycl, "Device": _FakeDevice})},
    )
    monkeypatch.setattr(process, "open3d", fake_open3d)

    assert process._sycl_gpu_available() is False


def test_sycl_gpu_available_requires_sycl0_device_availability(monkeypatch):
    class _FakeSycl:
        @staticmethod
        def get_available_devices():
            return ["SYCL GPU 0"]

        @staticmethod
        def is_available(_device):
            return False

    class _FakeDevice:
        def __init__(self, spec):
            self.spec = spec

    fake_open3d = type(
        "FakeOpen3D",
        (),
        {"core": type("FakeCore", (), {"sycl": _FakeSycl, "Device": _FakeDevice})},
    )
    monkeypatch.setattr(process, "open3d", fake_open3d)

    assert process._sycl_gpu_available() is False
