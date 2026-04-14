#!/usr/bin/env python3
"""Regression tests for Stage 2 STL model selection wiring."""

from pathlib import Path

from Ultra_Optimizer import (
    _hash_file,
    _hash_text_lines,
    _rank_stage2_object_metadata_candidates,
    _validate_polygon_motion_consistency,
    detect_stage2_layout_collisions,
    Stage2ObjectMetadata,
    Stage2RankedObjectCandidate,
    Stage2ObjectTransform,
    build_stage2_execution_contract_metadata,
    build_stage2_runtime_env_snapshot,
    build_stage2_metadata,
    detect_ironing_sections,
    enforce_stage1_success_or_raise,
    extract_stage2_object_metadata,
    invalidate_stale_sidecar,
    load_sidecar_metadata,
    remove_sidecar_metadata,
    resolve_stage2_plate_objects,
    resolve_stage2_object_transform,
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


def test_build_stage2_runtime_env_snapshot_defaults(monkeypatch):
    monkeypatch.delenv("GCODEZAA_RAYCAST_DEVICE", raising=False)
    monkeypatch.delenv("GCODEZAA_REQUIRE_GPU", raising=False)
    monkeypatch.delenv("GCODEZAA_SAMPLE_DISTANCE_MM", raising=False)
    monkeypatch.delenv("GCODEZAA_MAX_SEGMENT_SAMPLES", raising=False)
    monkeypatch.delenv("GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM", raising=False)

    snapshot = build_stage2_runtime_env_snapshot()

    assert "GCODEZAA_RAYCAST_DEVICE=<default>" in snapshot
    assert "GCODEZAA_REQUIRE_GPU=<default>" in snapshot
    assert "GCODEZAA_SAMPLE_DISTANCE_MM=<default>" in snapshot
    assert "GCODEZAA_MAX_SEGMENT_SAMPLES=<default>" in snapshot
    assert "GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM=<default>" in snapshot


def test_build_stage2_runtime_env_snapshot_overrides(monkeypatch):
    monkeypatch.setenv("GCODEZAA_RAYCAST_DEVICE", "sycl:0")
    monkeypatch.setenv("GCODEZAA_REQUIRE_GPU", "1")
    monkeypatch.setenv("GCODEZAA_SAMPLE_DISTANCE_MM", "0.30")
    monkeypatch.setenv("GCODEZAA_MAX_SEGMENT_SAMPLES", "256")
    monkeypatch.setenv("GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM", "1200")

    snapshot = build_stage2_runtime_env_snapshot()

    assert "GCODEZAA_RAYCAST_DEVICE=sycl:0" in snapshot
    assert "GCODEZAA_REQUIRE_GPU=1" in snapshot
    assert "GCODEZAA_SAMPLE_DISTANCE_MM=0.30" in snapshot
    assert "GCODEZAA_MAX_SEGMENT_SAMPLES=256" in snapshot
    assert "GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM=1200" in snapshot


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
    assert loaded["stage2_execution_contract_schema_version"] == 1
    assert loaded["stage2_execution_contract"]["public_handoff_mode"] == "single-plate-object"
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


def test_validate_sidecar_metadata_with_crlf_file_uses_on_disk_hash(tmp_path: Path):
    gcode_file = tmp_path / "sidecar_crlf.gcode"

    normalized_lines = [
        "G1 X1 Y1 E0.1\n",
        "G1 X2 Y2 E0.2\n",
    ]
    with open(gcode_file, "w", encoding="utf-8", newline="\r\n") as f:
        f.writelines(normalized_lines)

    # Text-line hashing can differ from file-byte hashing on CRLF files.
    assert _hash_text_lines(normalized_lines) != _hash_file(str(gcode_file))

    metadata = build_stage2_metadata(
        normalized_lines,
        selected_model="Model.stl",
        stage2_input_sha256="input_sha",
        stage2_output_sha256=_hash_file(str(gcode_file)),
    )

    valid, msg = validate_sidecar_metadata(str(gcode_file), metadata)
    assert valid is True
    assert msg == "ok"


def test_validate_sidecar_metadata_rejects_non_mapping_execution_contract(tmp_path: Path):
    gcode_file = tmp_path / "sidecar_execution_contract_bad.gcode"
    gcode_file.write_text("G1 X1 Y1 E0.1\n", encoding="utf-8")

    metadata = build_stage2_metadata(
        ["G1 X1 Y1 E0.1\n"],
        selected_model="Model.stl",
        stage2_input_sha256="input_sha",
        stage2_output_sha256=_hash_file(str(gcode_file)),
    )
    metadata["stage2_execution_contract"] = ["not", "a", "mapping"]

    valid, msg = validate_sidecar_metadata(str(gcode_file), metadata)
    assert valid is False
    assert msg == "stage2_execution_contract must be a mapping when present"


def test_detect_ironing_sections_with_feature_and_inline_comments():
    lines = [
        "M205 X15 Y15 Z0.8 E2 ; adjust jerk\n",
        "; FEATURE: Ironing\n",
        "G1 F2100\n",
        "G1 X72.658 Y130.688 E.00078 ; ironing\n",
        "G1 X72.505 Y130.662 E.00019 ; ironing\n",
        "G1 X70.582 Y131.053 E.00019 ; ironing\n",
        "; FEATURE: Internal solid infill\n",
        "G1 X67.37 Y125.569 E.00681 ; infill | Old Flow Value: 0.01161 Length: 0.35570\n",
    ]

    sections = detect_ironing_sections(lines)
    assert sections == [(1, 6)]


def test_resolve_stage2_object_transform_infers_center_from_window_bounds():
    gcode = [
        "; machine start\n",
        "G90\n",
        "; printing object cube id:1 copy 0\n",
        "G1 X10 Y20\n",
        "G1 X30 Y40\n",
        "; stop printing object cube id:1 copy 0\n",
    ]

    transform = resolve_stage2_object_transform(gcode)
    assert isinstance(transform, Stage2ObjectTransform)
    assert transform.center_x == 20.0
    assert transform.center_y == 30.0
    assert transform.rotation_deg == 0.0
    assert transform.source == "inferred-window-bounds"
    assert transform.metadata_family == "inferred-window-bounds"
    assert transform.inferred_bounds == {
        "min_x": 10.0,
        "max_x": 30.0,
        "min_y": 20.0,
        "max_y": 40.0,
    }


def test_resolve_stage2_object_transform_prefers_comment_hints_with_rotation():
    gcode = [
        "; ZAA_OBJECT_POSITION: 55.5,66.75\n",
        "; ZAA_OBJECT_ROTATION_DEG: 37.5\n",
        "G90\n",
        "; printing object cube id:1 copy 0\n",
        "G1 X10 Y20\n",
        "G1 X30 Y40\n",
        "; stop printing object cube id:1 copy 0\n",
    ]

    transform = resolve_stage2_object_transform(gcode)
    assert isinstance(transform, Stage2ObjectTransform)
    assert transform.center_x == 55.5
    assert transform.center_y == 66.75
    assert transform.rotation_deg == 37.5
    assert transform.source == "comment-hint"
    assert transform.metadata_family == "comment-hint"


def test_resolve_stage2_object_transform_reads_exclude_object_define_rotation():
    gcode = [
        "EXCLUDE_OBJECT_DEFINE NAME=benchy.stl_0 CENTER=12.5,17.5 ROTATION=90\n",
        "G90\n",
        "; printing object benchy id:1 copy 0\n",
        "G1 X0 Y0\n",
        "; stop printing object benchy id:1 copy 0\n",
    ]

    transform = resolve_stage2_object_transform(gcode)
    assert isinstance(transform, Stage2ObjectTransform)
    assert transform.center_x == 12.5
    assert transform.center_y == 17.5
    assert transform.rotation_deg == 90.0
    assert transform.source == "exclude-object"
    assert transform.metadata_family == "exclude-object"
    assert "selected-object:benchy.stl_0" in transform.notes


def test_resolve_stage2_object_transform_uses_metadata_rotation_when_comment_hint_is_partial():
    gcode = [
        "; ZAA_OBJECT_POSITION: 55.5,66.75\n",
        "EXCLUDE_OBJECT_DEFINE NAME=benchy.stl_0 CENTER=12.5,17.5 ROTATION=90\n",
        "G90\n",
        "; printing object benchy id:1 copy 0\n",
        "G1 X0 Y0\n",
        "; stop printing object benchy id:1 copy 0\n",
    ]

    transform = resolve_stage2_object_transform(gcode)
    assert isinstance(transform, Stage2ObjectTransform)
    assert transform.center_x == 55.5
    assert transform.center_y == 66.75
    assert transform.rotation_deg == 90.0
    assert transform.source == "comment-hint"
    assert transform.metadata_family == "comment-hint"
    assert "selected-object:benchy.stl_0" in transform.notes
    assert "rotation-from-exclude-object" in transform.notes


def test_resolve_stage2_object_transform_avoids_arbitrary_multi_object_metadata_selection():
    gcode = [
        "EXCLUDE_OBJECT_DEFINE NAME=left CENTER=10,10 ROTATION=0\n",
        "EXCLUDE_OBJECT_DEFINE NAME=right CENTER=90,90 ROTATION=180\n",
        "G90\n",
        "; printing object plate id:1 copy 0\n",
        "G1 X10 Y10\n",
        "G1 X90 Y90\n",
        "; stop printing object plate id:1 copy 0\n",
    ]

    transform = resolve_stage2_object_transform(gcode)
    assert isinstance(transform, Stage2ObjectTransform)
    assert transform.center_x == 50.0
    assert transform.center_y == 50.0
    assert transform.rotation_deg == 0.0
    assert transform.source == "inferred-window-bounds"
    assert transform.metadata_family == "inferred-window-bounds"
    assert "object-metadata-ambiguous" in transform.notes


def test_resolve_stage2_object_transform_uses_exclude_object_window_when_center_missing():
    gcode = [
        'EXCLUDE_OBJECT_DEFINE NAME="cube_0"\n',
        'EXCLUDE_OBJECT_START NAME="cube_0"\n',
        'G1 X10 Y20\n',
        'G1 X30 Y40\n',
        'EXCLUDE_OBJECT_END NAME="cube_0"\n',
    ]

    transform = resolve_stage2_object_transform(gcode)
    assert isinstance(transform, Stage2ObjectTransform)
    assert transform.center_x == 20.0
    assert transform.center_y == 30.0
    assert transform.rotation_deg == 0.0
    assert transform.source == "exclude-object"
    assert transform.metadata_family == "exclude-object"
    assert transform.inferred_bounds == {
        "min_x": 10.0,
        "max_x": 30.0,
        "min_y": 20.0,
        "max_y": 40.0,
    }
    assert "selected-object:cube_0" in transform.notes
    assert "center-from-object-window" in transform.notes


def test_resolve_stage2_object_transform_uses_polygon_centroid_when_center_missing():
    gcode = [
        'EXCLUDE_OBJECT_DEFINE NAME="cube_0" POLYGON=[[10,20],[30,20],[30,40],[10,40]] ROTATION=15\n',
    ]

    transform = resolve_stage2_object_transform(gcode)
    assert isinstance(transform, Stage2ObjectTransform)
    assert transform.center_x == 20.0
    assert transform.center_y == 30.0
    assert transform.rotation_deg == 15.0
    assert transform.source == "exclude-object"
    assert transform.metadata_family == "exclude-object"
    assert transform.inferred_bounds is None
    assert "selected-object:cube_0" in transform.notes
    assert "center-from-object-polygon" in transform.notes


def test_resolve_stage2_object_transform_aggregates_repeated_spans_without_coarse_window_collapse():
    gcode = [
        'EXCLUDE_OBJECT_DEFINE NAME="cube_0"\n',
        'EXCLUDE_OBJECT_START NAME="cube_0"\n',
        'G1 X10 Y20\n',
        'EXCLUDE_OBJECT_END NAME="cube_0"\n',
        'G1 X100 Y100\n',
        'EXCLUDE_OBJECT_START NAME="cube_0"\n',
        'G1 X30 Y40\n',
        'EXCLUDE_OBJECT_END NAME="cube_0"\n',
    ]

    transform = resolve_stage2_object_transform(gcode)
    assert isinstance(transform, Stage2ObjectTransform)
    assert transform.center_x == 20.0
    assert transform.center_y == 30.0
    assert transform.source == "exclude-object"
    assert transform.metadata_family == "exclude-object"
    assert transform.inferred_bounds == {
        "min_x": 10.0,
        "max_x": 30.0,
        "min_y": 20.0,
        "max_y": 40.0,
    }
    assert "selected-object:cube_0" in transform.notes
    assert "center-from-object-spans" in transform.notes


def test_resolve_stage2_object_transform_prefers_polygon_over_window_for_selected_object():
    gcode = [
        'EXCLUDE_OBJECT_DEFINE NAME="cube_0" POLYGON=[[10,20],[30,20],[30,40],[10,40]]\n',
        'EXCLUDE_OBJECT_START NAME="cube_0"\n',
        'G1 X0 Y0\n',
        'G1 X100 Y100\n',
        'EXCLUDE_OBJECT_END NAME="cube_0"\n',
    ]

    transform = resolve_stage2_object_transform(gcode)
    assert isinstance(transform, Stage2ObjectTransform)
    assert transform.center_x == 20.0
    assert transform.center_y == 30.0
    assert transform.rotation_deg == 0.0
    assert transform.source == "exclude-object"
    assert transform.metadata_family == "exclude-object"
    assert transform.inferred_bounds is None
    assert "selected-object:cube_0" in transform.notes
    assert "center-from-object-polygon" in transform.notes
    assert "center-from-object-window" not in transform.notes


def test_resolve_stage2_object_transform_respects_g91_state_within_object_span():
    gcode = [
        "G90\n",
        "G1 X10 Y10\n",
        'M486 S0 A"cube_0"\n',
        'M486 S0\n',
        "G91\n",
        "G1 X10 Y0\n",
        "G1 X0 Y10\n",
        'M486 S-1\n',
    ]

    transform = resolve_stage2_object_transform(gcode)
    assert isinstance(transform, Stage2ObjectTransform)
    assert transform.center_x == 20.0
    assert transform.center_y == 15.0
    assert transform.source == "m486"
    assert transform.metadata_family == "m486"
    assert transform.inferred_bounds == {
        "min_x": 20.0,
        "max_x": 20.0,
        "min_y": 10.0,
        "max_y": 20.0,
    }


def test_resolve_stage2_object_transform_uses_m486_window_when_center_missing():
    gcode = [
        'M486 S0 A"cube_0"\n',
        'M486 S0\n',
        'G1 X10 Y20\n',
        'G1 X30 Y40\n',
        'M486 S-1\n',
    ]

    transform = resolve_stage2_object_transform(gcode)
    assert isinstance(transform, Stage2ObjectTransform)
    assert transform.center_x == 20.0
    assert transform.center_y == 30.0
    assert transform.rotation_deg == 0.0
    assert transform.source == "m486"
    assert transform.metadata_family == "m486"
    assert transform.inferred_bounds == {
        "min_x": 10.0,
        "max_x": 30.0,
        "min_y": 20.0,
        "max_y": 40.0,
    }
    assert "selected-object:cube_0" in transform.notes
    assert "center-from-object-window" in transform.notes


def test_rank_stage2_object_metadata_candidates_prefers_declared_center_over_span_inference():
    gcode = [
        'EXCLUDE_OBJECT_DEFINE NAME="centered" CENTER=10,20\n',
        'EXCLUDE_OBJECT_DEFINE NAME="windowed"\n',
        'EXCLUDE_OBJECT_START NAME="windowed"\n',
        'G1 X80 Y80\n',
        'G1 X100 Y100\n',
        'EXCLUDE_OBJECT_END NAME="windowed"\n',
    ]

    ranked, unresolved = _rank_stage2_object_metadata_candidates(gcode, 0, len(gcode) - 1)

    assert unresolved == []
    assert [candidate.name for candidate in ranked] == ["centered", "windowed"]
    assert ranked[0].center_source == "declared-center"
    assert ranked[1].center_source == "object-window"
    assert ranked[0].score > ranked[1].score


def test_rank_stage2_object_metadata_candidates_penalizes_polygon_motion_mismatch():
    gcode = [
        'EXCLUDE_OBJECT_DEFINE NAME="cube_0" POLYGON=[[10,10],[20,10],[20,20],[10,20]]\n',
        'EXCLUDE_OBJECT_START NAME="cube_0"\n',
        'G1 X10 Y10\n',
        'G1 X40 Y40\n',
        'EXCLUDE_OBJECT_END NAME="cube_0"\n',
    ]

    ranked, unresolved = _rank_stage2_object_metadata_candidates(gcode, 0, len(gcode) - 1)

    assert unresolved == []
    assert ranked[0].name == "cube_0"
    assert "polygon-motion-mismatch" in ranked[0].ambiguity_markers
    assert "polygon-motion-mismatch" in ranked[0].notes


def test_validate_polygon_motion_consistency_accepts_motion_within_polygon_tolerance():
    gcode = [
        'EXCLUDE_OBJECT_START NAME="cube_0"\n',
        'G1 X11 Y11\n',
        'G1 X19 Y19\n',
        'EXCLUDE_OBJECT_END NAME="cube_0"\n',
    ]
    candidate = Stage2ObjectMetadata(
        name="cube_0",
        source_family="exclude-object",
        polygon=((10.0, 10.0), (20.0, 10.0), (20.0, 20.0), (10.0, 20.0)),
        spans=(),
    )
    candidate = Stage2ObjectMetadata(
        name=candidate.name,
        source_family=candidate.source_family,
        polygon=candidate.polygon,
        spans=extract_stage2_object_metadata(gcode)[0].spans,
    )

    valid, notes, polygon_bounds, motion_bounds = _validate_polygon_motion_consistency(candidate, gcode)

    assert valid is True
    assert notes == ()
    assert polygon_bounds == {"min_x": 10.0, "max_x": 20.0, "min_y": 10.0, "max_y": 20.0}
    assert motion_bounds == {"min_x": 11.0, "max_x": 19.0, "min_y": 11.0, "max_y": 19.0}


def test_detect_stage2_layout_collisions_flags_candidates_with_insufficient_clearance():
    left = Stage2RankedObjectCandidate(
        name="cube_0",
        source_family="exclude-object",
        center_x=15.0,
        center_y=15.0,
        rotation_deg=0.0,
        center_source="polygon-centroid",
        inferred_bounds=None,
        polygon_bounds={"min_x": 10.0, "max_x": 20.0, "min_y": 10.0, "max_y": 20.0},
        score=0.92,
        exact_window_match=True,
        overlapping_span_count=1,
        span_count=1,
        complete_span_count=1,
        incomplete_span_count=0,
        window_start=0,
        window_end=10,
    )
    right = Stage2RankedObjectCandidate(
        name="cube_1",
        source_family="exclude-object",
        center_x=29.9,
        center_y=15.0,
        rotation_deg=0.0,
        center_source="polygon-centroid",
        inferred_bounds=None,
        polygon_bounds={"min_x": 24.9, "max_x": 34.9, "min_y": 10.0, "max_y": 20.0},
        score=0.92,
        exact_window_match=True,
        overlapping_span_count=1,
        span_count=1,
        complete_span_count=1,
        incomplete_span_count=0,
        window_start=11,
        window_end=20,
    )

    collisions, unresolved_bounds = detect_stage2_layout_collisions([left, right])

    assert unresolved_bounds == []
    assert collisions == {"cube_0": ["cube_1"], "cube_1": ["cube_0"]}


def test_resolve_stage2_plate_objects_batches_non_overlapping_copies():
    ranked_candidates = [
        Stage2RankedObjectCandidate(
            name="cube_0",
            source_family="exclude-object",
            center_x=15.0,
            center_y=15.0,
            rotation_deg=0.0,
            center_source="polygon-centroid",
            inferred_bounds=None,
            polygon_bounds={"min_x": 10.0, "max_x": 20.0, "min_y": 10.0, "max_y": 20.0},
            score=0.92,
            exact_window_match=True,
            overlapping_span_count=1,
            span_count=1,
            complete_span_count=1,
            incomplete_span_count=0,
            window_start=0,
            window_end=10,
        ),
        Stage2RankedObjectCandidate(
            name="cube_1",
            source_family="exclude-object",
            center_x=35.0,
            center_y=15.0,
            rotation_deg=0.0,
            center_source="polygon-centroid",
            inferred_bounds=None,
            polygon_bounds={"min_x": 30.0, "max_x": 40.0, "min_y": 10.0, "max_y": 20.0},
            score=0.91,
            exact_window_match=True,
            overlapping_span_count=1,
            span_count=1,
            complete_span_count=1,
            incomplete_span_count=0,
            window_start=11,
            window_end=20,
        ),
    ]
    transform = Stage2ObjectTransform(
        center_x=15.0,
        center_y=15.0,
        rotation_deg=0.0,
        source="exclude-object",
        window_start=0,
        window_end=10,
        inferred_bounds=None,
        metadata_family="exclude-object",
    )

    plate_objects, validation_notes, handoff_mode = resolve_stage2_plate_objects(
        "Model.stl",
        transform,
        ranked_candidates,
    )

    assert handoff_mode == "multi-object-batch"
    assert validation_notes == ["multi-object-handoff:2-objects"]
    assert plate_objects == [
        ("cube_0", "Model.stl", 15.0, 15.0, 0.0),
        ("cube_1", "Model.stl", 35.0, 15.0, 0.0),
    ]


def test_resolve_stage2_plate_objects_falls_back_when_collision_bounds_conflict():
    ranked_candidates = [
        Stage2RankedObjectCandidate(
            name="cube_0",
            source_family="exclude-object",
            center_x=15.0,
            center_y=15.0,
            rotation_deg=0.0,
            center_source="polygon-centroid",
            inferred_bounds=None,
            polygon_bounds={"min_x": 10.0, "max_x": 20.0, "min_y": 10.0, "max_y": 20.0},
            score=0.92,
            exact_window_match=True,
            overlapping_span_count=1,
            span_count=1,
            complete_span_count=1,
            incomplete_span_count=0,
            window_start=0,
            window_end=10,
        ),
        Stage2RankedObjectCandidate(
            name="cube_1",
            source_family="exclude-object",
            center_x=28.0,
            center_y=15.0,
            rotation_deg=0.0,
            center_source="polygon-centroid",
            inferred_bounds=None,
            polygon_bounds={"min_x": 23.0, "max_x": 33.0, "min_y": 10.0, "max_y": 20.0},
            score=0.91,
            exact_window_match=True,
            overlapping_span_count=1,
            span_count=1,
            complete_span_count=1,
            incomplete_span_count=0,
            window_start=11,
            window_end=20,
        ),
    ]
    transform = Stage2ObjectTransform(
        center_x=15.0,
        center_y=15.0,
        rotation_deg=0.0,
        source="exclude-object",
        window_start=0,
        window_end=10,
        inferred_bounds=None,
        metadata_family="exclude-object",
    )

    plate_objects, validation_notes, handoff_mode = resolve_stage2_plate_objects(
        "Model.stl",
        transform,
        ranked_candidates,
    )

    assert handoff_mode == "single-plate-object"
    assert plate_objects == [("Model.stl", 15.0, 15.0, 0.0)]
    assert validation_notes == [
        "single-object-handoff:collisions-detected:cube_0:cube_1;cube_1:cube_0"
    ]


def test_resolve_stage2_plate_objects_batches_distinct_models_when_candidates_map_to_stls():
    ranked_candidates = [
        Stage2RankedObjectCandidate(
            name="cube_0",
            source_family="exclude-object",
            center_x=15.0,
            center_y=15.0,
            rotation_deg=0.0,
            center_source="polygon-centroid",
            inferred_bounds=None,
            polygon_bounds={"min_x": 10.0, "max_x": 20.0, "min_y": 10.0, "max_y": 20.0},
            score=0.92,
            exact_window_match=True,
            overlapping_span_count=1,
            span_count=1,
            complete_span_count=1,
            incomplete_span_count=0,
            window_start=0,
            window_end=10,
        ),
        Stage2RankedObjectCandidate(
            name="cone_0",
            source_family="exclude-object",
            center_x=45.0,
            center_y=15.0,
            rotation_deg=15.0,
            center_source="polygon-centroid",
            inferred_bounds=None,
            polygon_bounds={"min_x": 40.0, "max_x": 50.0, "min_y": 10.0, "max_y": 20.0},
            score=0.91,
            exact_window_match=True,
            overlapping_span_count=1,
            span_count=1,
            complete_span_count=1,
            incomplete_span_count=0,
            window_start=11,
            window_end=20,
        ),
    ]
    transform = Stage2ObjectTransform(
        center_x=15.0,
        center_y=15.0,
        rotation_deg=0.0,
        source="exclude-object",
        window_start=0,
        window_end=10,
        inferred_bounds=None,
        metadata_family="exclude-object",
    )

    plate_objects, validation_notes, handoff_mode = resolve_stage2_plate_objects(
        "cube.stl",
        transform,
        ranked_candidates,
        available_models=["cone.stl", "cube.stl"],
    )

    assert handoff_mode == "multi-object-batch"
    assert validation_notes == ["multi-object-handoff:2-objects"]
    assert plate_objects == [
        ("cube_0", "cube.stl", 15.0, 15.0, 0.0),
        ("cone_0", "cone.stl", 45.0, 15.0, 15.0),
    ]


def test_resolve_stage2_plate_objects_uses_unique_fuzzy_model_match_when_safe():
    ranked_candidates = [
        Stage2RankedObjectCandidate(
            name="benchy_0",
            source_family="exclude-object",
            center_x=15.0,
            center_y=15.0,
            rotation_deg=0.0,
            center_source="polygon-centroid",
            inferred_bounds=None,
            polygon_bounds={"min_x": 10.0, "max_x": 20.0, "min_y": 10.0, "max_y": 20.0},
            score=0.92,
            exact_window_match=True,
            overlapping_span_count=1,
            span_count=1,
            complete_span_count=1,
            incomplete_span_count=0,
            window_start=0,
            window_end=10,
        ),
        Stage2RankedObjectCandidate(
            name="cube_0",
            source_family="exclude-object",
            center_x=45.0,
            center_y=15.0,
            rotation_deg=0.0,
            center_source="polygon-centroid",
            inferred_bounds=None,
            polygon_bounds={"min_x": 40.0, "max_x": 50.0, "min_y": 10.0, "max_y": 20.0},
            score=0.91,
            exact_window_match=True,
            overlapping_span_count=1,
            span_count=1,
            complete_span_count=1,
            incomplete_span_count=0,
            window_start=11,
            window_end=20,
        ),
    ]
    transform = Stage2ObjectTransform(
        center_x=15.0,
        center_y=15.0,
        rotation_deg=0.0,
        source="exclude-object",
        window_start=0,
        window_end=10,
        inferred_bounds=None,
        metadata_family="exclude-object",
    )

    plate_objects, validation_notes, handoff_mode = resolve_stage2_plate_objects(
        "3DBenchy.stl",
        transform,
        ranked_candidates,
        available_models=["3DBenchy.stl", "cube.stl"],
    )

    assert handoff_mode == "multi-object-batch"
    assert validation_notes == [
        "model-resolution:benchy_0->3DBenchy.stl:fuzzy-root",
        "multi-object-handoff:2-objects",
    ]
    assert plate_objects == [
        ("benchy_0", "3DBenchy.stl", 15.0, 15.0, 0.0),
        ("cube_0", "cube.stl", 45.0, 15.0, 0.0),
    ]


def test_resolve_stage2_plate_objects_falls_back_when_model_match_is_ambiguous():
    ranked_candidates = [
        Stage2RankedObjectCandidate(
            name="benchy_0",
            source_family="exclude-object",
            center_x=15.0,
            center_y=15.0,
            rotation_deg=0.0,
            center_source="polygon-centroid",
            inferred_bounds=None,
            polygon_bounds={"min_x": 10.0, "max_x": 20.0, "min_y": 10.0, "max_y": 20.0},
            score=0.92,
            exact_window_match=True,
            overlapping_span_count=1,
            span_count=1,
            complete_span_count=1,
            incomplete_span_count=0,
            window_start=0,
            window_end=10,
        ),
        Stage2RankedObjectCandidate(
            name="cube_0",
            source_family="exclude-object",
            center_x=45.0,
            center_y=15.0,
            rotation_deg=0.0,
            center_source="polygon-centroid",
            inferred_bounds=None,
            polygon_bounds={"min_x": 40.0, "max_x": 50.0, "min_y": 10.0, "max_y": 20.0},
            score=0.91,
            exact_window_match=True,
            overlapping_span_count=1,
            span_count=1,
            complete_span_count=1,
            incomplete_span_count=0,
            window_start=11,
            window_end=20,
        ),
    ]
    transform = Stage2ObjectTransform(
        center_x=15.0,
        center_y=15.0,
        rotation_deg=0.0,
        source="exclude-object",
        window_start=0,
        window_end=10,
        inferred_bounds=None,
        metadata_family="exclude-object",
    )

    plate_objects, validation_notes, handoff_mode = resolve_stage2_plate_objects(
        "3DBenchy.stl",
        transform,
        ranked_candidates,
        available_models=["3DBenchy.stl", "MiniBenchy.stl", "cube.stl"],
    )

    assert handoff_mode == "single-plate-object"
    assert plate_objects == [("3DBenchy.stl", 15.0, 15.0, 0.0)]
    assert validation_notes == [
        "single-object-handoff:ambiguous-model-match:benchy_0->3DBenchy.stl,MiniBenchy.stl"
    ]


def test_extract_stage2_object_metadata_preserves_repeated_spans_and_mixed_families():
    gcode = [
        'EXCLUDE_OBJECT_DEFINE NAME="cube_0" CENTER=12.5,17.5\n',
        'EXCLUDE_OBJECT_START NAME="cube_0"\n',
        'G1 X10 Y10 E0.1\n',
        'EXCLUDE_OBJECT_END NAME="cube_0"\n',
        'M486 S0 A"cube_1"\n',
        'M486 S0\n',
        'G1 X30 Y30 E0.1\n',
        'M486 S-1\n',
        'EXCLUDE_OBJECT_START NAME="cube_0"\n',
        'G1 X12 Y14 E0.1\n',
        'EXCLUDE_OBJECT_END NAME="cube_0"\n',
    ]

    objects = extract_stage2_object_metadata(gcode)

    assert [obj.name for obj in objects] == ["cube_0", "cube_1"]
    cube_0 = objects[0]
    cube_1 = objects[1]
    assert cube_0.source_family == "exclude-object"
    assert cube_0.window_start == 1
    assert cube_0.window_end == 10
    assert len(cube_0.spans) == 2
    assert cube_0.spans[0].start == 1
    assert cube_0.spans[0].end == 3
    assert cube_0.spans[1].start == 8
    assert cube_0.spans[1].end == 10
    assert cube_1.source_family == "m486"
    assert len(cube_1.spans) == 1
    assert cube_1.spans[0].start == 5
    assert cube_1.spans[0].end == 7


def test_build_stage2_metadata_persists_object_transform():
    lines = ["G1 X1 Y1 E0.1\n"]
    transform = Stage2ObjectTransform(
        center_x=10.0,
        center_y=20.0,
        rotation_deg=45.0,
        source="comment-hint",
        window_start=0,
        window_end=0,
        inferred_bounds=None,
        metadata_family="comment-hint",
    )
    candidate = Stage2ObjectMetadata(
        name="cube_0",
        source_family="exclude-object",
        center_x=10.0,
        center_y=20.0,
        rotation_deg=45.0,
        polygon=((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),
        window_start=0,
        window_end=0,
    )
    ranked_candidate = Stage2RankedObjectCandidate(
        name="cube_0",
        source_family="exclude-object",
        center_x=10.0,
        center_y=20.0,
        rotation_deg=45.0,
        center_source="declared-center",
        inferred_bounds=None,
        polygon_bounds={"min_x": 0.0, "max_x": 1.0, "min_y": 0.0, "max_y": 1.0},
        score=1.0,
        exact_window_match=True,
        overlapping_span_count=1,
        span_count=1,
        complete_span_count=1,
        incomplete_span_count=0,
        window_start=0,
        window_end=0,
        score_details=("center-source:declared-center",),
    )

    metadata = build_stage2_metadata(
        lines,
        selected_model="Model.stl",
        stage2_input_sha256="in",
        stage2_output_sha256="out",
        stage2_object_transform=transform,
        stage2_object_metadata_candidates=[candidate],
        stage2_ranked_object_candidates=[ranked_candidate],
        stage2_runtime_env_snapshot="GCODEZAA_RAYCAST_DEVICE=<default>",
        stage2_elapsed_seconds=1.25,
    )

    assert metadata["stage2_object_transform"] == transform.as_metadata_dict()
    assert metadata["stage2_object_transform_schema_version"] == 1
    assert metadata["stage2_execution_contract_schema_version"] == 1
    assert metadata["stage2_execution_contract"] == build_stage2_execution_contract_metadata(
        "Model.stl",
        transform,
    )
    assert metadata["stage2_object_metadata_candidates"] == [candidate.as_metadata_dict()]
    assert metadata["stage2_ranked_object_candidates"] == [ranked_candidate.as_metadata_dict()]
    assert metadata["stage2_runtime_env_snapshot"] == "GCODEZAA_RAYCAST_DEVICE=<default>"
    assert metadata["stage2_elapsed_seconds"] == 1.25


def test_extract_stage2_object_metadata_reads_exclude_object_define_and_window():
    gcode = [
        'EXCLUDE_OBJECT_DEFINE NAME="cube_0" CENTER=12.5,17.5 ROTATION=90 POLYGON=[[10,10],[15,10],[15,20],[10,20]]\n',
        'EXCLUDE_OBJECT_START NAME="cube_0"\n',
        'G1 X10 Y10 E0.1\n',
        'EXCLUDE_OBJECT_END NAME="cube_0"\n',
    ]

    objects = extract_stage2_object_metadata(gcode)

    assert len(objects) == 1
    obj = objects[0]
    assert isinstance(obj, Stage2ObjectMetadata)
    assert obj.name == "cube_0"
    assert obj.source_family == "exclude-object"
    assert obj.center_x == 12.5
    assert obj.center_y == 17.5
    assert obj.rotation_deg == 90.0
    assert obj.polygon == ((10.0, 10.0), (15.0, 10.0), (15.0, 20.0), (10.0, 20.0))
    assert obj.window_start == 1
    assert obj.window_end == 3


def test_extract_stage2_object_metadata_reads_m486_sequence():
    gcode = [
        'M486 S0 A"cube_0"\n',
        'M486 S0\n',
        'G1 X10 Y10 E0.1\n',
        'M486 S-1\n',
    ]

    objects = extract_stage2_object_metadata(gcode)

    assert len(objects) == 1
    obj = objects[0]
    assert isinstance(obj, Stage2ObjectMetadata)
    assert obj.name == "cube_0"
    assert obj.source_family == "m486"
    assert obj.window_start == 1
    assert obj.window_end == 3
    assert "m486-definition" in obj.notes
