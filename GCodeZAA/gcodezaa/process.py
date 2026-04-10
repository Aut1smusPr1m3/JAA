from gcodezaa.context import ProcessorContext
from gcodezaa.extrusion import Extrusion, decompose_arc
from gcodezaa.surface_analysis import MAX_SURFACE_FOLLOW_SEGMENT_MM, SurfaceAnalyzer
from gcodezaa.config import MIN_BUILDPLATE_Z
from gcodezaa.slicer_syntax import SlicerSyntax
import os
import re
import math
import logging

try:
    import open3d
except ModuleNotFoundError:
    open3d = None

logger = logging.getLogger(__name__)

PRINT_OBJECT_START_RE = re.compile(r"^\s*;\s*printing object\b", re.IGNORECASE)
PRINT_OBJECT_STOP_RE = re.compile(r"^\s*;\s*stop printing object\b", re.IGNORECASE)
COMMENT_FEATURE_RE = re.compile(r"^\s*(?:TYPE|FEATURE)\s*:\s*(.+?)\s*$", re.IGNORECASE)
INLINE_FEATURE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\s*ironing\b", re.IGNORECASE), "ironing"),
    (re.compile(r"^\s*top\s+surface\b", re.IGNORECASE), "top surface"),
    (re.compile(r"^\s*outer\s+wall\b", re.IGNORECASE), "outer wall"),
    (re.compile(r"^\s*inner\s+wall\b", re.IGNORECASE), "inner wall"),
    (re.compile(r"^\s*infill\b", re.IGNORECASE), "infill"),
    (re.compile(r"^\s*perimeter\b", re.IGNORECASE), "perimeter"),
]


def _normalize_line_type(value: str | None) -> str:
    return (value or "").strip().lower()


def _detect_line_type_from_line(line: str, syntax: SlicerSyntax) -> str | None:
    """Extract semantic line-type from explicit markers or inline move comments."""
    marker_prefix = syntax.line_type
    if marker_prefix and line.startswith(marker_prefix):
        return _normalize_line_type(line.removeprefix(marker_prefix).strip())

    if ";" not in line:
        return None

    comment = line.split(";", 1)[1].strip()
    if not comment:
        return None

    feature_match = COMMENT_FEATURE_RE.match(comment)
    if feature_match:
        return _normalize_line_type(feature_match.group(1))

    for pattern, canonical in INLINE_FEATURE_PATTERNS:
        if pattern.match(comment):
            return canonical

    return None


def _normalize_device_spec(spec: str) -> str:
    value = (spec or "").strip().upper()
    if value in {"", "AUTO"}:
        return "AUTO"
    if value in {"CPU", "CPU:0"}:
        return "CPU:0"
    if value in {"SYCL", "SYCL:0"}:
        return "SYCL:0"
    if value.startswith("CPU:") or value.startswith("SYCL:"):
        return value
    if value in {"CUDA", "CUDA:0"}:
        # Open3D raycasting acceleration is exposed via SYCL backends.
        return "SYCL:0"
    return value


def detect_processing_window(gcode: list[str], syntax: SlicerSyntax) -> tuple[int, int, str]:
    """Return inclusive [start,end] line indices for printable object region."""
    executable_starts = [
        idx
        for idx, line in enumerate(gcode)
        if line.startswith(syntax.executable_block_start)
    ]
    executable_ends = [
        idx
        for idx, line in enumerate(gcode)
        if line.startswith(syntax.executable_block_end)
    ]
    if executable_starts:
        start = executable_starts[0]
        end_candidates = [idx for idx in executable_ends if idx >= start]
        end = end_candidates[-1] if end_candidates else len(gcode) - 1
        return start, end, "executable-block"

    print_starts = [idx for idx, line in enumerate(gcode) if PRINT_OBJECT_START_RE.search(line)]
    print_stops = [idx for idx, line in enumerate(gcode) if PRINT_OBJECT_STOP_RE.search(line)]
    if print_starts:
        start = print_starts[0]
        end_candidates = [idx for idx in print_stops if idx >= start]
        if end_candidates:
            end = end_candidates[-1]
        else:
            end = print_starts[-1]
        return start, end, "printing-object-comments"

    return 0, len(gcode) - 1, "full-file"


def _prime_context_state_for_line(ctx: ProcessorContext, line: str) -> None:
    """Update context motion/extrusion state without modifying line content."""
    detected_line_type = _detect_line_type_from_line(line, ctx.syntax)
    if detected_line_type is not None:
        ctx.line_type = detected_line_type

    if line.startswith(ctx.syntax.layer_change):
        ctx.layer += 1
        ctx.line_type = _normalize_line_type(ctx.syntax.line_type_inner_wall)
        return
    if line.startswith(ctx.syntax.z):
        ctx.z = clamp_buildplate_z(float(line.removeprefix(ctx.syntax.z)))
        return
    if line.startswith(ctx.syntax.height):
        ctx.height = float(line.removeprefix(ctx.syntax.height))
        return
    if line.startswith(ctx.syntax.width):
        ctx.width = float(line.removeprefix(ctx.syntax.width))
        return
    if line.startswith(ctx.syntax.wipe_start):
        ctx.wipe = True
        return
    if line.startswith(ctx.syntax.wipe_end):
        ctx.wipe = False
        return

    if line.startswith("M82"):
        ctx.relative_extrusion = False
        return
    if line.startswith("M83"):
        ctx.relative_extrusion = True
        return
    if line.startswith("G90"):
        ctx.relative_positioning = False
        return
    if line.startswith("G91"):
        ctx.relative_positioning = True
        return
    if line.startswith("G92"):
        args = parse_simple_args(line)
        if "E" in args:
            ctx.last_e = float(args["E"])
        if "X" in args or "Y" in args or "Z" in args:
            ctx.last_p = (
                float(args.get("X", ctx.last_p[0])),
                float(args.get("Y", ctx.last_p[1])),
                clamp_buildplate_z(float(args.get("Z", ctx.last_p[2]))),
            )
        return

    if line.startswith("G0 ") or line.startswith("G1 "):
        args = parse_simple_args(line)
        x = float(args["X"]) if "X" in args else None
        y = float(args["Y"]) if "Y" in args else None
        z = clamp_buildplate_z(float(args["Z"])) if "Z" in args else None
        if x is not None or y is not None or z is not None:
            if ctx.relative_positioning:
                ctx.last_p = (
                    ctx.last_p[0] + (x or 0.0),
                    ctx.last_p[1] + (y or 0.0),
                    clamp_buildplate_z(ctx.last_p[2] + (z or 0.0)),
                )
            else:
                ctx.last_p = (
                    x if x is not None else ctx.last_p[0],
                    y if y is not None else ctx.last_p[1],
                    z if z is not None else ctx.last_p[2],
                )

        if "E" in args:
            e_val = float(args["E"])
            if ctx.relative_extrusion:
                ctx.last_e += e_val
            else:
                ctx.last_e = e_val

        return

    if line.startswith("G2 ") or line.startswith("G3 "):
        args = parse_simple_args(line)
        x = float(args["X"]) if "X" in args else None
        y = float(args["Y"]) if "Y" in args else None
        z = clamp_buildplate_z(float(args["Z"])) if "Z" in args else None
        if x is not None or y is not None or z is not None:
            if ctx.relative_positioning:
                ctx.last_p = (
                    ctx.last_p[0] + (x or 0.0),
                    ctx.last_p[1] + (y or 0.0),
                    clamp_buildplate_z(ctx.last_p[2] + (z or 0.0)),
                )
            else:
                ctx.last_p = (
                    x if x is not None else ctx.last_p[0],
                    y if y is not None else ctx.last_p[1],
                    z if z is not None else ctx.last_p[2],
                )

        if "E" in args:
            e_val = float(args["E"])
            if ctx.relative_extrusion:
                ctx.last_e += e_val
            else:
                ctx.last_e = e_val


def _sycl_devices() -> list[str]:
    if open3d is None:
        return []
    if not hasattr(open3d.core, "sycl"):
        return []
    try:
        devices = open3d.core.sycl.get_available_devices()
        return [str(d) for d in devices]
    except Exception:
        return []


def _sycl_gpu_available() -> bool:
    devices = _sycl_devices()
    if not devices:
        return False
    return any("gpu" in d.lower() for d in devices)


def resolve_raycast_device_spec() -> str:
    """Resolve raycasting device target from environment with safe fallback behavior."""
    requested = _normalize_device_spec(os.getenv("GCODEZAA_RAYCAST_DEVICE", "AUTO"))
    require_gpu = os.getenv("GCODEZAA_REQUIRE_GPU", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if requested == "AUTO":
        if _sycl_gpu_available():
            logger.info("[GCodeZAA] Raycast device resolved: AUTO -> SYCL:0 (SYCL GPU detected)")
            return "SYCL:0"
        if require_gpu:
            msg = (
                "GCODEZAA_REQUIRE_GPU is set but open3d is not available"
                if open3d is None
                else "GCODEZAA_REQUIRE_GPU is set but no SYCL GPU was detected"
            )
            raise RuntimeError(msg)
        logger.info("[GCodeZAA] Raycast device resolved: AUTO -> CPU:0 (no SYCL GPU detected)")
        return "CPU:0"

    if requested.startswith("SYCL"):
        if _sycl_gpu_available():
            logger.info("[GCodeZAA] Raycast device resolved: %s", requested)
            return requested
        if require_gpu:
            msg = (
                "GCODEZAA_REQUIRE_GPU is set but open3d is not available"
                if open3d is None
                else f"GCODEZAA_REQUIRE_GPU is set but requested device {requested} is not available"
            )
            raise RuntimeError(msg)
        logger.warning(
            "[GCodeZAA] Requested raycast device %s but no SYCL GPU detected; falling back to CPU:0",
            requested,
        )
        return "CPU:0"

    if requested.startswith("CPU"):
        logger.info("[GCodeZAA] Raycast device resolved: %s", requested)
        return requested

    logger.warning(
        "[GCodeZAA] Unknown GCODEZAA_RAYCAST_DEVICE=%s; falling back to CPU:0",
        requested,
    )
    return "CPU:0"


def make_raycast_device():
    """Create and return an Open3D Device for raycasting scene execution."""
    spec = resolve_raycast_device_spec()
    try:
        return open3d.core.Device(spec), spec
    except Exception as exc:
        logger.warning(
            "[GCodeZAA] Failed to create raycast device %s (%s); using CPU:0",
            spec,
            exc,
        )
        return open3d.core.Device("CPU:0"), "CPU:0"

# === ENHANCED ZAA CONFIGURATION ===
ZAA_ADAPTIVE_RESOLUTION = True          # Adapt resolution to geometry
ZAA_MAX_Z_DEVIATION = 0.5              # Max Z deviation from nominal layer
ZAA_NORMAL_SMOOTHING = 3                # Normal smoothing window
ZAA_MIN_DEVIATION_THRESHOLD = 0.01      # Ignore Z deviations < this
ZAA_EDGE_DETECTION = True               # Preserve wall edges
ZAA_FLOW_COMPENSATION_MODE = "physics"  # "linear", "quadratic", "physics", or "adaptive"
ZAA_VECTOR_ALIGNED_RETRACTION = True    # Retract along surface normal
ZAA_NONPLANAR_IRONING = True            # True surface following ironing
ZAA_GENERATE_IRONING = True             # Generate ironing paths for surface-aware top and wall layers
ZAA_LONGER_SMOOTHING_ENABLED = True     # Enable longer coherent smoothing lines
ZAA_VERBOSE_TENSOR_LOGGING = False      # Disable tensor batch logging for performance

SURFACE_FOLLOW_LINE_TYPES = {
    # Ironing is always surface-following when enabled.
    "ironing",
    # Top/outer/inner walls may also follow surface when generation is enabled.
    "top surface",
    "outer wall",
    "inner wall",
}


def parse_simple_args(gcode: str) -> dict:
    return dict(
        map(
            lambda x: (x[0], x[1:].strip()),
            filter(lambda x: x != "", gcode.split(";", maxsplit=1)[0].split(" ")),
        )
    )


def parse_klipper_args(gcode: str) -> dict:
    return dict(map(lambda x: list(map(str.strip, x.split("=", 1))), gcode.split(" ")))


def compensate_extrusion_physics(
    base_extrusion: float,
    z_offset: float,
    layer_height: float,
    line_width: float,
    surface_normal: tuple,
    confidence: float,
    compensation_mode: str = "physics"
) -> float:
    """
    Advanced extrusion compensation using physics-based calculations.
    
    Accounts for:
    - Layer height changes from Z offset
    - Line width adjustments
    - Surface normal orientation
    - Confidence in surface analysis
    """
    if z_offset == 0 or confidence < 0.2:
        return base_extrusion
    
    # Calculate effective layer height when contouring
    effective_height = layer_height + z_offset
    
    # Calculate area change factor
    # Assumption: line cross-section = layer_height * line_width when planar
    nominal_area = layer_height * line_width
    contoured_area = effective_height * line_width  # Width stays same, height changes
    area_factor = contoured_area / nominal_area if nominal_area > 0 else 1.0
    
    if compensation_mode == "linear":
        # Linear compensation: E ∝ height
        factor = area_factor
    
    elif compensation_mode == "quadratic":
        # Quadratic: E ∝ height²
        factor = area_factor ** 2
    
    elif compensation_mode == "physics":
        # Physics-based compensation with tilt-aware width scaling
        factor = area_factor
        normal_z = abs(surface_normal[2])  # How upright the surface is
        tilt_factor = 0.6 + 0.4 * normal_z
        factor *= tilt_factor
    
    else:  # adaptive
        linear_factor = area_factor
        physics_factor = area_factor * (0.6 + 0.4 * abs(surface_normal[2]))
        factor = linear_factor + (physics_factor - linear_factor) * min(1.0, max(0.0, confidence))
    
    # Smooth application of compensation with confidence weighting
    final_factor = 1.0 + (factor - 1.0) * min(1.0, confidence)
    final_factor = max(0.6, min(1.6, final_factor))

    return base_extrusion * final_factor


def create_vector_aligned_retraction(
    current_pos: tuple,
    surface_normal: tuple,
    retraction_length: float = 1.5,
    layer_height: float = 0.2
) -> tuple:
    """
    Create a retraction move along the surface normal vector.
    Reduces ooze and string formation.
    
    Returns: (retract_x, retract_y, retract_z) relative movement
    """
    # Retract length scales with layer height
    scale = retraction_length * (layer_height / 0.2)  # Normalize to 0.2mm reference
    
    return (
        surface_normal[0] * scale,
        surface_normal[1] * scale,
        surface_normal[2] * scale
    )


def _segment_length(p1: tuple[float, float, float], p2: tuple[float, float, float]) -> float:
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dz = p2[2] - p1[2]
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _is_extruding_move(ctx: ProcessorContext, target_e: float | None) -> bool:
    if target_e is None:
        return False

    if ctx.relative_extrusion:
        return target_e > 0.0

    return target_e > (float(ctx.last_e) + 1e-9)


def _should_apply_surface_following(ctx: ProcessorContext, target_e: float | None) -> bool:
    if ctx.active_object is None or ctx.wipe or ctx.relative_positioning:
        return False

    if not _is_extruding_move(ctx, target_e):
        return False

    line_type = ctx.line_type.lower()
    if line_type not in SURFACE_FOLLOW_LINE_TYPES:
        return False

    if line_type == "ironing":
        return True

    return ZAA_GENERATE_IRONING


def clamp_buildplate_z(z_value: float | None, min_z: float = MIN_BUILDPLATE_Z) -> float | None:
    """Clamp absolute Z values to the build-plate plane for print safety."""
    if z_value is None:
        return None
    return max(min_z, z_value)


def _build_surface_extrusions(
    ctx: ProcessorContext,
    points: list[dict],
    total_e: float | None,
    feedrate: float | None,
    layer_height: float
) -> list[Extrusion]:
    if len(points) < 2:
        return []

    base_e = 0.0
    if total_e is not None and not ctx.relative_extrusion:
        base_e = float(ctx.last_e or 0.0)

    total_length = 0.0
    for idx in range(1, len(points)):
        start_z = clamp_buildplate_z(points[idx - 1]["adjusted_z"])
        end_z = clamp_buildplate_z(points[idx]["adjusted_z"])
        total_length += _segment_length(
            (points[idx - 1]["x"], points[idx - 1]["y"], start_z),
            (points[idx]["x"], points[idx]["y"], end_z),
        )

    if total_length <= 0:
        return []

    extrusion_amount = 0.0
    if total_e is not None:
        if ctx.relative_extrusion:
            extrusion_amount = total_e
        else:
            extrusion_amount = total_e - base_e

    rate = extrusion_amount / total_length if total_length > 0 else 0.0
    current_e = base_e
    output = []
    previous_pos = ctx.last_p

    for idx in range(1, len(points)):
        start = (
            points[idx - 1]["x"],
            points[idx - 1]["y"],
            clamp_buildplate_z(points[idx - 1]["adjusted_z"]),
        )
        end = (
            points[idx]["x"],
            points[idx]["y"],
            clamp_buildplate_z(points[idx]["adjusted_z"]),
        )
        length = _segment_length(start, end)
        if length <= 1e-6:
            continue

        normalized = points[idx].get("normal", (0.0, 0.0, 1.0))
        confidence = points[idx].get("confidence", 0.0)
        z_offset = points[idx].get("z_offset", 0.0)

        segment_e = None
        if total_e is not None and rate != 0.0:
            raw_e = rate * length
            adjusted_e = compensate_extrusion_physics(
                raw_e,
                z_offset,
                layer_height,
                ctx.width,
                normalized,
                confidence,
                ZAA_FLOW_COMPENSATION_MODE,
            )

            if ctx.relative_extrusion:
                segment_e = adjusted_e
            else:
                current_e += adjusted_e
                segment_e = current_e

        output.append(
            Extrusion(
                p=previous_pos,
                x=end[0],
                y=end[1],
                z=end[2],
                e=segment_e,
                f=feedrate if idx == 1 else None,
                relative=ctx.relative_positioning,
            )
        )
        previous_pos = end

    return output


def process_gcode(
    gcode: list[str],
    model_dir: str,
    plate_object: tuple[str, float, float] | None = None,
) -> list[str]:
    ctx = ProcessorContext(gcode, model_dir)
    if plate_object is not None:
        scene, device = load_object(
            ctx, plate_object[0], plate_object[1], plate_object[2]
        )
        ctx.active_object = scene
        ctx.active_object_device = device
    
    # Initialize surface analysis with batching support
    surface_analyzer = SurfaceAnalyzer(ctx.active_object, ctx.active_object_device)

    process_start, process_end, reason = detect_processing_window(ctx.gcode, ctx.syntax)
    logger.info(
        "[GCodeZAA] Processing window (%s): lines %d-%d",
        reason,
        process_start,
        process_end,
    )

    for line in ctx.gcode[:process_start]:
        _prime_context_state_for_line(ctx, line)

    ctx.gcode_line = process_start
    while ctx.gcode_line <= process_end and ctx.gcode_line < len(ctx.gcode):
        process_line(ctx, surface_analyzer)
        ctx.gcode_line += 1

    return ctx.gcode


def load_object(
    ctx: ProcessorContext, name: str, x: float, y: float
) -> tuple[object, object]:
    """Load STL model and create raycasting scene with position offset."""
    if open3d is None:
        raise RuntimeError("open3d is required to load STL models for raycasting")

    device, device_spec = make_raycast_device()

    model_path = os.path.join(ctx.model_dir, name)
    
    logger.info(f"[GCodeZAA] Loading STL model: {name} on device {device_spec}")
    mesh = open3d.t.io.read_triangle_mesh(model_path, enable_post_processing=True)
    
    min_bound = mesh.get_min_bound()
    max_bound = mesh.get_max_bound()
    center = min_bound + (max_bound - min_bound) / 2
    
    # Translate mesh to position on build plate
    mesh.translate([x - center[0].item(), y - center[1].item(), -min_bound[2].item()])
    
    x_span = float((max_bound[0] - min_bound[0]).item())
    y_span = float((max_bound[1] - min_bound[1]).item())
    z_span = float((max_bound[2] - min_bound[2]).item())
    logger.info(f"[GCodeZAA] Model bounds: X={x_span:.1f}mm, Y={y_span:.1f}mm, Z={z_span:.1f}mm")

    mesh = mesh.to(device)
    scene = open3d.t.geometry.RaycastingScene(device=device)
    scene.add_triangles(mesh)

    return scene, device


def process_line(ctx: ProcessorContext, surface_analyzer: SurfaceAnalyzer):
    write_back = ""
    ctx.extrusion = []
    ctx.gcode[ctx.gcode_line] = ctx.line.strip() + "\n"

    detected_line_type = _detect_line_type_from_line(ctx.line, ctx.syntax)
    if detected_line_type is not None:
        ctx.line_type = detected_line_type

    if ctx.line.startswith("G0 ") or ctx.line.startswith("G1 "):
        args = parse_simple_args(ctx.line)
        
        # Get target position
        target_x = float(args["X"]) if "X" in args else None
        target_y = float(args["Y"]) if "Y" in args else None
        target_z = clamp_buildplate_z(float(args["Z"])) if "Z" in args else None
        target_e = float(args["E"]) if "E" in args else None
        target_f = float(args["F"]) if "F" in args else None
        should_surface_follow = _should_apply_surface_following(ctx, target_e)
        
        # For non-zero XY moves, use batch surface analysis
        adjusted_z = target_z
        surface_analysis = None
        
        if (
            should_surface_follow
            and surface_analyzer.scene is not None
            and target_x is not None
            and target_y is not None
            and (target_x != ctx.last_p[0] or target_y != ctx.last_p[1])
        ):
            segment_label = f"line={ctx.gcode_line + 1} cmd={ctx.line.split(';', 1)[0].strip()}"
            # Batch analyze the segment
            segment_analysis = surface_analyzer.analyze_segment_batch(
                ctx.last_p[0],
                ctx.last_p[1],
                target_z if target_z is not None else ctx.last_p[2],
                target_x,
                target_y,
                layer_height=ctx.height,
                segment_label=segment_label,
            )

            if not segment_analysis:
                distance = math.hypot(target_x - ctx.last_p[0], target_y - ctx.last_p[1])
                if distance > MAX_SURFACE_FOLLOW_SEGMENT_MM:
                    logger.warning(
                        "[GCodeZAA] Surface-follow state jump candidate at line %d: start=(%.3f, %.3f, %.3f) target=(%.3f, %.3f, %.3f) distance=%.2fmm relative_positioning=%s relative_extrusion=%s",
                        ctx.gcode_line + 1,
                        ctx.last_p[0],
                        ctx.last_p[1],
                        ctx.last_p[2],
                        target_x,
                        target_y,
                        target_z if target_z is not None else ctx.last_p[2],
                        distance,
                        ctx.relative_positioning,
                        ctx.relative_extrusion,
                    )
            
            if segment_analysis:
                ctx.extrusion = _build_surface_extrusions(
                    ctx,
                    segment_analysis,
                    target_e,
                    target_f,
                    ctx.height,
                )

                for analysis in segment_analysis:
                    ctx.record_surface_normal(analysis.get("normal", (0, 0, 1)), analysis.get("confidence", 0))
                    ctx.record_z_offset(analysis.get("z_offset", 0), analysis.get("confidence", 0))

                if ctx.extrusion:
                    adjusted_z = clamp_buildplate_z(
                        segment_analysis[-1].get("adjusted_z", target_z)
                    )
        
        if not ctx.extrusion:
            ctx.extrusion.append(
                Extrusion(
                    p=ctx.last_p,
                    x=target_x,
                    y=target_y,
                    z=adjusted_z,
                    e=target_e,
                    f=target_f,
                    relative=ctx.relative_positioning,
                )
            )
        
    elif ctx.line.startswith("G2 ") or ctx.line.startswith("G3 "):
        # Handle arc move (G2 = clockwise, G3 = counter-clockwise)
        args = parse_simple_args(ctx.line)
        is_clockwise = ctx.line.startswith("G2 ")
        
        # Get arc end position
        end_x = float(args["X"]) if "X" in args else None
        end_y = float(args["Y"]) if "Y" in args else None
        end_z = clamp_buildplate_z(float(args["Z"])) if "Z" in args else None
        
        # Get arc center offset or radius
        center_i = float(args["I"]) if "I" in args else None
        center_j = float(args["J"]) if "J" in args else None
        radius = float(args["R"]) if "R" in args else None
        
        # Get feedrate and extrusion
        f = float(args["F"]) if "F" in args else None
        e = float(args["E"]) if "E" in args else None
        should_surface_follow = _should_apply_surface_following(ctx, e)
        
        # Only decompose and raycast arcs when we will actually apply surface-following output.
        if should_surface_follow and surface_analyzer.scene is not None:
            segment_length = 0.4
            if ZAA_LONGER_SMOOTHING_ENABLED:
                segment_length = max(0.2, min(0.75, ctx.height * 1.5))

            waypoints = decompose_arc(
                start_pos=ctx.last_p,
                end_x=end_x,
                end_y=end_y,
                end_z=end_z,
                center_i=center_i,
                center_j=center_j,
                radius=radius,
                is_clockwise=is_clockwise,
                segment_length=segment_length
            )

        else:
            waypoints = []

        # Batch analyze waypoints if we have multiple
        if len(waypoints) > 1 and surface_analyzer.scene is not None:
            arc_analysis = surface_analyzer.batch_analyze_points(
                [(wp[0], wp[1], wp[2]) for wp in waypoints],
                ctx.height,
            )

            arc_points = []
            for waypoint, analysis in zip(waypoints, arc_analysis):
                arc_points.append({
                    "x": waypoint[0],
                    "y": waypoint[1],
                    "adjusted_z": clamp_buildplate_z(waypoint[2] + analysis.get("z_offset", 0)),
                    "z_offset": analysis.get("z_offset", 0),
                    "normal": analysis.get("normal", (0,0,1)),
                    "confidence": analysis.get("confidence", 0),
                })

            for analysis in arc_analysis:
                ctx.record_surface_normal(analysis.get("normal", (0,0,1)), analysis.get("confidence", 0))
                ctx.record_z_offset(analysis.get("z_offset", 0), analysis.get("confidence", 0))

            ctx.extrusion = _build_surface_extrusions(
                ctx,
                arc_points,
                e,
                f,
                ctx.height,
            )
        else:
            # Fallback: degenerate arc without batch analysis
            if end_x is not None and end_y is not None:
                ctx.extrusion.append(
                    Extrusion(
                        p=ctx.last_p,
                        x=end_x,
                        y=end_y,
                        z=end_z,
                        e=e,
                        f=f,
                        relative=ctx.relative_positioning,
                    )
                )
    
    elif ctx.line.startswith(ctx.syntax.layer_change):
        ctx.layer += 1
        ctx.line_type = _normalize_line_type(ctx.syntax.line_type_inner_wall)
    elif ctx.line.startswith(ctx.syntax.z):
        ctx.z = clamp_buildplate_z(float(ctx.line.removeprefix(ctx.syntax.z)))
    elif ctx.line.startswith(ctx.syntax.height):
        ctx.height = float(ctx.line.removeprefix(ctx.syntax.height))
    elif ctx.line.startswith(ctx.syntax.width):
        ctx.width = float(ctx.line.removeprefix(ctx.syntax.width))
    elif ctx.line.startswith(ctx.syntax.wipe_start):
        ctx.wipe = True
    elif ctx.line.startswith(ctx.syntax.wipe_end):
        ctx.wipe = False
    elif ctx.line.startswith("M82"):
        ctx.relative_extrusion = False
    elif ctx.line.startswith("M83"):
        ctx.relative_extrusion = True
    elif ctx.line.startswith("G90"):
        ctx.relative_positioning = False
    elif ctx.line.startswith("G91"):
        ctx.relative_positioning = True
    elif ctx.line.startswith("G92"):
        args = parse_simple_args(ctx.line)
        if "E" in args:
            ctx.last_e = float(args["E"])
        if "X" in args or "Y" in args or "Z" in args:
            ctx.last_p = (
                float(args.get("X", ctx.last_p[0])),
                float(args.get("Y", ctx.last_p[1])),
                clamp_buildplate_z(float(args.get("Z", ctx.last_p[2]))),
            )
    elif ctx.line.startswith("EXCLUDE_OBJECT_DEFINE"):
        args = parse_klipper_args(ctx.line.removeprefix("EXCLUDE_OBJECT_DEFINE "))
        name = args["NAME"]
        x, y = map(float, args["CENTER"].split(","))

        scene, device = load_object(
            ctx, re.sub(r"\.stl_.*$", ".stl", name), x, y
        )
        ctx.exclude_object[name] = scene
        ctx.exclude_object_device[name] = device
    elif ctx.line.startswith("EXCLUDE_OBJECT_START"):
        args = parse_klipper_args(ctx.line.removeprefix("EXCLUDE_OBJECT_START "))
        ctx.active_object = ctx.exclude_object[args["NAME"]]
        ctx.active_object_device = ctx.exclude_object_device.get(args["NAME"])
    elif ctx.line.startswith("EXCLUDE_OBJECT_END"):
        ctx.active_object = None
        ctx.active_object_device = None

    if (
        len(ctx.extrusion) == 1
        and _should_apply_surface_following(ctx, ctx.extrusion[0].e)
        and ctx.extrusion[0].length() != 0
        and ctx.extrusion[0].e is not None
        and (ctx.extrusion[0].x is not None or ctx.extrusion[0].y is not None)
    ):
        line_type = _normalize_line_type(ctx.line_type)
        ironing_type = _normalize_line_type(ctx.syntax.line_type_ironing)
        top_surface_type = _normalize_line_type(ctx.syntax.line_type_top_surface)
        outer_wall_type = _normalize_line_type(ctx.syntax.line_type_outer_wall)
        inner_wall_type = _normalize_line_type(ctx.syntax.line_type_inner_wall)

        # TRUE NON-PLANAR IRONING: Use surface-following path
        if ZAA_NONPLANAR_IRONING and (
            line_type == ironing_type
            or (ZAA_GENERATE_IRONING and line_type in (
                top_surface_type,
                outer_wall_type,
                inner_wall_type,
            ))
        ):
            ironing_path = surface_analyzer.get_nonplanar_ironing_path(
                ctx.last_p[0], ctx.last_p[1], ctx.z,
                ctx.extrusion[0].x or ctx.last_p[0],
                ctx.extrusion[0].y or ctx.last_p[1],
                layer_height=ctx.height
            )

            if ironing_path:
                ctx.extrusion = _build_surface_extrusions(
                    ctx,
                    ironing_path,
                    ctx.extrusion[0].e,
                    (ctx.extrusion[0].f or 1200) * 0.7,
                    ctx.height,
                )
        else:
            # Standard planar contouring
            contour = ctx.extrusion[0].contour_z(
                ctx.active_object,
                z=ctx.z,
                height=float(ctx.config_block["layer_height"]),
                ironing_line=line_type == ironing_type,
                outer_line=line_type == outer_wall_type,
                demo_split=None,
            )
            if any(map(lambda extrusion: extrusion.z != ctx.z, contour)):
                ctx.extrusion = contour
                write_back = f"{ctx.line_type.upper()}_CONTOUR"
                ctx.last_contoured_z = contour[-1].z

    if not write_back and ctx.last_contoured_z is not None and len(ctx.extrusion) > 0:
        ctx.extrusion = [
            Extrusion(
                p=ctx.last_p,
                x=None,
                y=None,
                z=clamp_buildplate_z(ctx.z),
                e=None,
                f=None,
                relative=False,
            ),
            *ctx.extrusion,
        ]
        ctx.last_contoured_z = None
        write_back = "RESET_Z"

    if len(ctx.extrusion) > 0:
        if ctx.extrusion[-1].e is not None:
            if ctx.relative_extrusion:
                # In relative mode, keep an absolute running total for state continuity.
                ctx.last_e += ctx.extrusion[-1].e
            else:
                ctx.last_e = ctx.extrusion[-1].e
        ctx.last_p = ctx.extrusion[-1].pos()

    if write_back == "":
        return

    if ctx.extrusion:
        ctx.gcode[ctx.gcode_line] = (
            f";{write_back} "
            + ctx.line
            + str.join(
                "",
                map(
                    lambda extrusion: (
                        ctx.line.split(" ", 1)[0]
                        + str(extrusion)
                        + ";"
                        + extrusion.meta
                        + "\n"
                    ),
                    ctx.extrusion,
                ),
            )
            + f";{write_back}_END\n"
        )
