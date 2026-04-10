#!/usr/bin/env python3
"""Regression tests for Stage 2 STL model selection wiring."""

from pathlib import Path

from Ultra_Optimizer import (
    _hash_file,
    build_stage2_metadata,
    enforce_stage1_success_or_raise,
    invalidate_stale_sidecar,
    load_sidecar_metadata,
    remove_sidecar_metadata,
    select_primary_stl_model,
    sidecar_hash_matches_file,
    sidecar_path_for_gcode,
    update_sidecar_stage3_status,
    validate_sidecar_metadata,
    write_sidecar_metadata,
)


def test_select_primary_stl_model_returns_none_when_dir_missing(tmp_path: Path):
    missing = tmp_path / "missing_models"
    assert select_primary_stl_model(str(missing)) is None


def test_select_primary_stl_model_filters_non_stl_and_sorts(tmp_path: Path):
    model_dir = tmp_path / "stl_models"
    model_dir.mkdir()
    (model_dir / "notes.txt").write_text("ignore", encoding="utf-8")
    (model_dir / "z_model.stl").write_text("solid z", encoding="utf-8")
    (model_dir / "A_model.STL").write_text("solid a", encoding="utf-8")

    selected = select_primary_stl_model(str(model_dir))
    assert selected == "A_model.STL"


def test_select_primary_stl_model_returns_none_without_stl(tmp_path: Path):
    model_dir = tmp_path / "stl_models"
    model_dir.mkdir()
    (model_dir / "mesh.obj").write_text("o mesh", encoding="utf-8")

    assert select_primary_stl_model(str(model_dir)) is None


def test_sidecar_path_for_gcode_suffix(tmp_path: Path):
    gcode_file = tmp_path / "sample.gcode"
    expected = str(gcode_file) + ".meta"
    assert sidecar_path_for_gcode(str(gcode_file)) == expected


def test_stage2_metadata_build_and_roundtrip(tmp_path: Path):
    gcode_file = tmp_path / "sample.gcode"
    gcode_file.write_text("G1 X1 Y1\n", encoding="utf-8")

    lines = [
        ";TYPE:Ironing\n",
        "G1 X10 Y10 Z0.2 E1.0\n",
        ";RESET_Z\n",
    ]
    metadata = build_stage2_metadata(
        lines,
        selected_model="3DBenchy.stl",
        stage2_input_sha256="in_sha",
        stage2_output_sha256="out_sha",
    )

    sidecar = write_sidecar_metadata(str(gcode_file), metadata)
    assert sidecar.endswith(".meta")

    loaded = load_sidecar_metadata(str(gcode_file))
    assert loaded is not None
    assert loaded["schema_version"] == 1
    assert loaded["selected_model"] == "3DBenchy.stl"
    assert loaded["stage2_input_sha256"] == "in_sha"
    assert loaded["stage2_output_sha256"] == "out_sha"
    assert loaded["ironing_ranges"]
    assert loaded["contour_marker_lines"] == [2]

    assert remove_sidecar_metadata(str(gcode_file)) is True
    assert load_sidecar_metadata(str(gcode_file)) is None


def test_invalidate_stale_sidecar_on_input_hash_change(tmp_path: Path):
    gcode_file = tmp_path / "sample.gcode"
    gcode_file.write_text("G1 X1 Y1\n", encoding="utf-8")

    metadata = {
        "schema_version": 1,
        "stage2_input_sha256": "old_input",
        "stage2_output_sha256": "old_output",
    }
    write_sidecar_metadata(str(gcode_file), metadata)

    removed = invalidate_stale_sidecar(str(gcode_file), "new_input")
    assert removed is True
    assert load_sidecar_metadata(str(gcode_file)) is None

    regenerated = {
        "schema_version": 1,
        "stage2_input_sha256": "new_input",
        "stage2_output_sha256": "new_output",
    }
    write_sidecar_metadata(str(gcode_file), regenerated)
    loaded = load_sidecar_metadata(str(gcode_file))
    assert loaded is not None
    assert loaded["stage2_input_sha256"] == "new_input"


def test_invalidate_stale_sidecar_keeps_matching_input_hash(tmp_path: Path):
    gcode_file = tmp_path / "sample.gcode"
    gcode_file.write_text("G1 X1 Y1\n", encoding="utf-8")

    metadata = {
        "schema_version": 1,
        "stage2_input_sha256": "same_input",
        "stage2_output_sha256": "old_output",
    }
    write_sidecar_metadata(str(gcode_file), metadata)

    removed = invalidate_stale_sidecar(str(gcode_file), "same_input")
    assert removed is False
    assert load_sidecar_metadata(str(gcode_file)) is not None


def test_stage1_guard_sets_downstream_skips_and_raises():
    stage_status = {
        "stage_1": "FAILED",
        "stage_2": "SKIPPED",
        "stage_3": "SKIPPED",
    }

    try:
        enforce_stage1_success_or_raise(stage_status)
    except RuntimeError as exc:
        assert "Stage 1 failed validation" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when Stage 1 is not complete")

    assert stage_status["stage_2"] == "SKIPPED (stage 1 failed)"
    assert stage_status["stage_3"] == "SKIPPED (stage 1 failed)"


def test_sidecar_stage3_update_and_hash_sync(tmp_path: Path):
    gcode_file = tmp_path / "sample.gcode"
    gcode_file.write_text("G1 X1 Y1\n", encoding="utf-8")

    stage2_metadata = {
        "schema_version": 1,
        "stage": "stage_2",
        "stage2_input_sha256": "input_sha",
        "stage2_output_sha256": "outdated_sha",
    }
    write_sidecar_metadata(str(gcode_file), stage2_metadata)

    loaded = load_sidecar_metadata(str(gcode_file))
    assert loaded is not None
    assert sidecar_hash_matches_file(str(gcode_file), loaded, "stage2_output_sha256") is False

    loaded["stage2_output_sha256"] = _hash_file(str(gcode_file))
    write_sidecar_metadata(str(gcode_file), loaded)
    reloaded = load_sidecar_metadata(str(gcode_file))
    assert reloaded is not None
    assert sidecar_hash_matches_file(str(gcode_file), reloaded, "stage2_output_sha256") is True

    updated = update_sidecar_stage3_status(str(gcode_file), "COMPLETE", include_output_hash=True)
    assert updated is True

    final_meta = load_sidecar_metadata(str(gcode_file))
    assert final_meta is not None
    assert final_meta["stage_3"] == "COMPLETE"
    assert "stage3_output_sha256" in final_meta


def test_stage2_to_stage3_sidecar_lifecycle_preserves_stage2_fields(tmp_path: Path):
    gcode_file = tmp_path / "pipeline.gcode"
    lines = ["G1 X1 Y1 E0.1\n", "G1 X2 Y2 E0.2\n"]
    gcode_file.write_text("".join(lines), encoding="utf-8")

    stage2_meta = build_stage2_metadata(
        lines,
        selected_model="Model.stl",
        stage2_input_sha256="input_sha",
        stage2_output_sha256=_hash_file(str(gcode_file)),
    )
    write_sidecar_metadata(str(gcode_file), stage2_meta)

    loaded = load_sidecar_metadata(str(gcode_file))
    assert loaded is not None
    assert sidecar_hash_matches_file(str(gcode_file), loaded, "stage2_output_sha256") is True

    updated = update_sidecar_stage3_status(str(gcode_file), "SKIPPED (ArcWelder unavailable)")
    assert updated is True

    final_meta = load_sidecar_metadata(str(gcode_file))
    assert final_meta is not None
    assert final_meta["selected_model"] == "Model.stl"
    assert final_meta["stage2_input_sha256"] == "input_sha"
    assert final_meta["stage_3"] == "SKIPPED (ArcWelder unavailable)"


def test_validate_sidecar_metadata_passes_when_hashes_match(tmp_path: Path):
    gcode_file = tmp_path / "sidecar_ok.gcode"
    gcode_file.write_text("G1 X1 Y1 E0.1\n", encoding="utf-8")

    metadata = build_stage2_metadata(
        ["G1 X1 Y1 E0.1\n"],
        selected_model="Model.stl",
        stage2_input_sha256="input_sha",
        stage2_output_sha256=_hash_file(str(gcode_file)),
    )
    write_sidecar_metadata(str(gcode_file), metadata)

    valid, msg = validate_sidecar_metadata(str(gcode_file), metadata)
    assert valid is True
    assert msg == "ok"


def test_validate_sidecar_metadata_fails_on_stage2_hash_mismatch(tmp_path: Path):
    gcode_file = tmp_path / "sidecar_bad.gcode"
    gcode_file.write_text("G1 X1 Y1 E0.1\n", encoding="utf-8")

    metadata = build_stage2_metadata(
        ["G1 X1 Y1 E0.1\n"],
        selected_model="Model.stl",
        stage2_input_sha256="input_sha",
        stage2_output_sha256="bad_hash",
    )
    write_sidecar_metadata(str(gcode_file), metadata)

    valid, msg = validate_sidecar_metadata(str(gcode_file), metadata)
    assert valid is False
    assert "stage2_output_sha256" in msg


def test_validate_sidecar_metadata_accepts_final_stage3_hash(tmp_path: Path):
    gcode_file = tmp_path / "sidecar_stage3.gcode"
    gcode_file.write_text("G1 X1 Y1 E0.1\n", encoding="utf-8")

    metadata = build_stage2_metadata(
        ["G1 X1 Y1 E0.1\n"],
        selected_model="Model.stl",
        stage2_input_sha256="input_sha",
        stage2_output_sha256=_hash_file(str(gcode_file)),
    )
    write_sidecar_metadata(str(gcode_file), metadata)

    # Simulate post-stage2 mutation (e.g. ArcWelder or safety rewrite).
    gcode_file.write_text("G1 X2 Y2 E0.2\n", encoding="utf-8")
    metadata["stage3_output_sha256"] = _hash_file(str(gcode_file))
    write_sidecar_metadata(str(gcode_file), metadata)

    valid, msg = validate_sidecar_metadata(
        str(gcode_file),
        metadata,
        check_stage2_file_hash=False,
    )
    assert valid is True
    assert msg == "ok"
