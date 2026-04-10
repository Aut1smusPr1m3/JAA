from gcodezaa.context import ProcessorContext
from gcodezaa.extrusion import Extrusion, decompose_arc
from gcodezaa.surface_analysis import SurfaceAnalyzer, EdgeDetector
import os
import re
import math
import logging

try:
    import open3d
except ModuleNotFoundError:
    open3d = None

logger = logging.getLogger(__name__)

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
        total_length += _segment_length(
            (points[idx - 1]["x"], points[idx - 1]["y"], points[idx - 1]["adjusted_z"]),
            (points[idx]["x"], points[idx]["y"], points[idx]["adjusted_z"]),
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
        start = (points[idx - 1]["x"], points[idx - 1]["y"], points[idx - 1]["adjusted_z"])
        end = (points[idx]["x"], points[idx]["y"], points[idx]["adjusted_z"])
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
                relative=ctx.relative_extrusion,
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
        ctx.active_object = load_object(
            ctx, plate_object[0], plate_object[1], plate_object[2]
        )
    
    # Initialize surface analysis with batching support
    surface_analyzer = SurfaceAnalyzer(ctx.active_object)
    edge_detector = EdgeDetector()
    
    has_executable_markers = any(
        line.startswith(ctx.syntax.executable_block_start) for line in ctx.gcode
    )
    is_in_executable = not has_executable_markers
    
    while ctx.gcode_line < len(ctx.gcode):
        if has_executable_markers and not is_in_executable and ctx.line.startswith(
            ctx.syntax.executable_block_start
        ):
            is_in_executable = True
        elif has_executable_markers and is_in_executable and ctx.line.startswith(ctx.syntax.executable_block_end):
            break
        elif is_in_executable:
            process_line(ctx, surface_analyzer, edge_detector)
        ctx.gcode_line += 1

    ctx.gcode[0] = f"; GCodeZAA Enhanced - Tensor Batching, Physics Compensation, Vector Retraction, Non-planar Ironing\n" + ctx.gcode[0]

    return ctx.gcode


def load_object(
    ctx: ProcessorContext, name: str, x: float, y: float
) -> object:
    """Load STL model and create raycasting scene with position offset."""
    if open3d is None:
        raise RuntimeError("open3d is required to load STL models for raycasting")

    model_path = os.path.join(ctx.model_dir, name)
    
    logger.info(f"[GCodeZAA] Loading STL model: {name}")
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

    scene = open3d.t.geometry.RaycastingScene()
    scene.add_triangles(mesh)

    return scene


def process_line(ctx: ProcessorContext, surface_analyzer: SurfaceAnalyzer, edge_detector: EdgeDetector):
    write_back = ""
    ctx.extrusion = []
    ctx.gcode[ctx.gcode_line] = ctx.line.strip() + "\n"

    if ctx.line.startswith("G0 ") or ctx.line.startswith("G1 "):
        args = parse_simple_args(ctx.line)
        
        # Get target position
        target_x = float(args["X"]) if "X" in args else None
        target_y = float(args["Y"]) if "Y" in args else None
        target_z = float(args["Z"]) if "Z" in args else None
        target_e = float(args["E"]) if "E" in args else None
        target_f = float(args["F"]) if "F" in args else None
        
        # For non-zero XY moves, use batch surface analysis
        adjusted_z = target_z
        surface_analysis = None
        
        if (surface_analyzer.scene is not None and target_x is not None and target_y is not None 
            and (target_x != ctx.last_p[0] or target_y != ctx.last_p[1])):
            # Batch analyze the segment
            segment_analysis = surface_analyzer.analyze_segment_batch(
                ctx.last_p[0], ctx.last_p[1], target_z if target_z is not None else ctx.last_p[2],
                target_x, target_y,
                layer_height=ctx.height
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
                    adjusted_z = segment_analysis[-1].get("adjusted_z", target_z)
        
        if not ctx.extrusion:
            ctx.extrusion.append(
                Extrusion(
                    p=ctx.last_p,
                    x=target_x,
                    y=target_y,
                    z=adjusted_z,
                    e=target_e,
                    f=target_f,
                    relative=ctx.relative_extrusion,
                )
            )
        
    elif ctx.line.startswith("G2 ") or ctx.line.startswith("G3 "):
        # Handle arc move (G2 = clockwise, G3 = counter-clockwise)
        args = parse_simple_args(ctx.line)
        is_clockwise = ctx.line.startswith("G2 ")
        
        # Get arc end position
        end_x = float(args["X"]) if "X" in args else None
        end_y = float(args["Y"]) if "Y" in args else None
        end_z = float(args["Z"]) if "Z" in args else None
        
        # Get arc center offset or radius
        center_i = float(args["I"]) if "I" in args else None
        center_j = float(args["J"]) if "J" in args else None
        radius = float(args["R"]) if "R" in args else None
        
        # Get feedrate and extrusion
        f = float(args["F"]) if "F" in args else None
        e = float(args["E"]) if "E" in args else None
        
        # Decompose arc into waypoints with adaptive segment resolution
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
                    "adjusted_z": waypoint[2] + analysis.get("z_offset", 0),
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
                        relative=ctx.relative_extrusion,
                    )
                )
    
    elif ctx.line.startswith(ctx.syntax.line_type):
        ctx.line_type = ctx.line.removeprefix(ctx.syntax.line_type).strip()
    elif ctx.line.startswith(ctx.syntax.layer_change):
        ctx.layer += 1
        ctx.line_type = ctx.syntax.line_type_inner_wall
    elif ctx.line.startswith(ctx.syntax.z):
        ctx.z = float(ctx.line.removeprefix(ctx.syntax.z))
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
                float(args.get("Z", ctx.last_p[2])),
            )
    elif ctx.line.startswith("EXCLUDE_OBJECT_DEFINE"):
        args = parse_klipper_args(ctx.line.removeprefix("EXCLUDE_OBJECT_DEFINE "))
        name = args["NAME"]
        x, y = map(float, args["CENTER"].split(","))

        ctx.exclude_object[name] = load_object(
            ctx, re.sub(r"\.stl_.*$", ".stl", name), x, y
        )
    elif ctx.line.startswith("EXCLUDE_OBJECT_START"):
        args = parse_klipper_args(ctx.line.removeprefix("EXCLUDE_OBJECT_START "))
        ctx.active_object = ctx.exclude_object[args["NAME"]]
    elif ctx.line.startswith("EXCLUDE_OBJECT_END"):
        ctx.active_object = None

    if (
        len(ctx.extrusion) == 1
        and not ctx.wipe
        and ctx.active_object is not None
        and (
            ctx.line_type == ctx.syntax.line_type_ironing
            or ctx.line_type == ctx.syntax.line_type_top_surface
            or ctx.line_type == ctx.syntax.line_type_outer_wall
            or ctx.line_type == ctx.syntax.line_type_inner_wall
        )
        and not ctx.relative_positioning
        and ctx.extrusion[0].length() != 0
        and ctx.extrusion[0].e is not None
        and (ctx.extrusion[0].x is not None or ctx.extrusion[0].y is not None)
    ):
        # TRUE NON-PLANAR IRONING: Use surface-following path
        if ZAA_NONPLANAR_IRONING and (
            ctx.line_type == ctx.syntax.line_type_ironing
            or (ZAA_GENERATE_IRONING and ctx.line_type in (
                ctx.syntax.line_type_top_surface,
                ctx.syntax.line_type_outer_wall,
                ctx.syntax.line_type_inner_wall,
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
                ironing_line=ctx.line_type == ctx.syntax.line_type_ironing,
                outer_line=ctx.line_type == ctx.syntax.line_type_outer_wall,
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
                z=ctx.z,
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
