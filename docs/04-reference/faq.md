# FAQ

## Why is Stage 2 sometimes skipped?
Stage 2 needs GCodeZAA import support and an STL file in `stl_models/`.

## Why are some comments missing after processing?
ArcWelder (Stage 3) rewrites output and strips comments.

## Do I need Open3D?
Only for full STL raycasting workflows. Core pipeline still runs without it.

## How do I install everything on Windows in one step?
Use the bootstrap installer:
```powershell
./scripts/windows/bootstrap.ps1 -InstallDev
```
This creates a venv, installs packages, checks ArcWelder, and can run tests.

## Which test command should I use?
Use:
```bash
python -m pytest -q
```

## Why does Stage 2 log "No explicit object rotation metadata found; defaulting to 0.0deg"?
Stage 2 uses metadata from G-code comments or `EXCLUDE_OBJECT_DEFINE` to align the STL to the
printed object's real position and orientation. When that metadata is absent, the pipeline falls
back to `0°` rotation. If your model was rotated in the slicer, the surface map will be
misaligned. Fix it by adding near the top of your G-code:

```gcode
; ZAA_OBJECT_POSITION: <x_center>,<y_center>
; ZAA_OBJECT_ROTATION_DEG: <degrees>
```

Or ensure your slicer emits `EXCLUDE_OBJECT_DEFINE NAME=... CENTER=x,y ROTATION=deg`.

## How do I know what transform Stage 2 actually used?
Check the log line:

```
[GCodeZAA] Using STL model '...' for surface raycasting at center=(x, y) rotation=Ndeg source=...
```

The `source` field tells you where the transform came from:
- `comment-hint` — explicit `; ZAA_OBJECT_*` comment in G-code
- `exclude-object` — `EXCLUDE_OBJECT_DEFINE` metadata from slicer
- `inferred-window-bounds` — center inferred from motion bounds inside printable window
- `default-origin` — no geometry information found; using (0, 0)

The full transform is also saved in the sidecar `.meta` file under `stage2_object_transform`.

## What licence does this project use?
GNU General Public License v3 (GPL-3.0). See `LICENSE` in the repository root.
