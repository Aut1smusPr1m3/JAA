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
