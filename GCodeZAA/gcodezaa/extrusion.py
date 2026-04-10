import math
import logging

try:
    import open3d
except ModuleNotFoundError:
    open3d = None

logger = logging.getLogger(__name__)


def format_gcode_number(number: float) -> str:
    """Format number with proper G-code precision."""
    if number is None:
        return ""
    formatted = f"{number:.6f}"
    formatted = formatted.rstrip("0")
    formatted = formatted.rstrip(".")
    return formatted


def calculate_arc_radius(
    start_x: float, start_y: float,
    end_x: float | None, end_y: float | None,
    center_i: float | None = None,
    center_j: float | None = None,
    radius: float | None = None
) -> float:
    """Calculate the radius of an arc from its parameters."""
    if center_i is not None and center_j is not None:
        return math.sqrt(center_i**2 + center_j**2)
    elif radius is not None:
        return radius
    elif end_x is not None and end_y is not None:
        # Estimate from end point
        dx = end_x - start_x
        dy = end_y - start_y
        return math.sqrt(dx**2 + dy**2) / 2
    return 0


def decompose_arc(
    start_pos: tuple[float, float, float],
    end_x: float | None,
    end_y: float | None,
    end_z: float | None,
    center_i: float | None = None,
    center_j: float | None = None,
    radius: float | None = None,
    is_clockwise: bool = True,
    segment_length: float = 1.0,
) -> list[tuple[float, float, float]]:
    """
    Decompose a G2/G3 arc into line segments.
    Returns list of (x, y, z) waypoints along the arc.
    
    Args:
        start_pos: Starting (x, y, z) position
        end_x, end_y, end_z: End position
        center_i, center_j: Offset from current position to arc center (XY plane)
        radius: Optional arc radius (alternative to I/J)
        is_clockwise: True for G2 (clockwise), False for G3 (counter-clockwise)
        segment_length: Maximum length of each linear segment
    """
    if end_x is None or end_y is None:
        return [start_pos]
    
    # Determine end position
    end_pos = (end_x, end_y, end_z if end_z is not None else start_pos[2])
    
    # Determine arc center
    if center_i is not None and center_j is not None:
        center_x = start_pos[0] + center_i
        center_y = start_pos[1] + center_j
    elif radius is not None:
        # Calculate center from radius
        dx = end_x - start_pos[0]
        dy = end_y - start_pos[1]
        
        # Distance to end point
        q = math.sqrt(dx**2 + dy**2)
        
        if q == 0:
            return [start_pos, end_pos]
        
        # Calculate center position with offset
        x = dx / 2
        y = dy / 2
        
        a = math.sqrt(max(0, radius**2 - (q/2)**2))
        
        if is_clockwise:
            center_x = start_pos[0] + x + a * dy / q
            center_y = start_pos[1] + y - a * dx / q
        else:
            center_x = start_pos[0] + x - a * dy / q
            center_y = start_pos[1] + y + a * dx / q
    else:
        # Invalid arc parameters
        return [start_pos, end_pos]
    
    # Calculate arc radius
    arc_radius = math.sqrt((start_pos[0] - center_x)**2 + (start_pos[1] - center_y)**2)
    
    if arc_radius < 0.01:
        # Degenerate arc
        return [start_pos, end_pos]
    
    # Calculate angles
    start_angle = math.atan2(start_pos[1] - center_y, start_pos[0] - center_x)
    end_angle = math.atan2(end_pos[1] - center_y, end_pos[0] - center_x)
    
    # Adjust angles for arc direction
    if is_clockwise:
        if end_angle > start_angle:
            end_angle -= 2 * math.pi
        delta_angle = start_angle - end_angle
    else:
        if end_angle < start_angle:
            end_angle += 2 * math.pi
        delta_angle = end_angle - start_angle
    
    delta_angle = abs(delta_angle)
    
    # Calculate arc length and number of segments
    arc_length = arc_radius * delta_angle
    num_segments = max(2, int(math.ceil(arc_length / segment_length)))
    
    # Generate waypoints along arc
    waypoints = [start_pos]
    
    for i in range(1, num_segments):
        t = i / num_segments
        
        if is_clockwise:
            current_angle = start_angle - t * delta_angle
        else:
            current_angle = start_angle + t * delta_angle
        
        # Z interpolation (linear)
        current_z = start_pos[2] + t * (end_pos[2] - start_pos[2])
        
        # XY position on arc
        current_x = center_x + arc_radius * math.cos(current_angle)
        current_y = center_y + arc_radius * math.sin(current_angle)
        
        waypoints.append((current_x, current_y, current_z))
    
    # Add end point
    waypoints.append(end_pos)
    
    return waypoints


class Extrusion:
    p: tuple[float, float, float]
    x: float | None
    y: float | None
    z: float | None
    e: float | None
    f: float | None
    relative: bool
    meta = ""

    def __init__(
        self,
        p: tuple[float, float, float],
        x: float | None,
        y: float | None,
        z: float | None,
        e: float | None,
        f: float | None,
        relative: bool,
    ):
        self.p = p
        self.x = x
        self.y = y
        self.z = z
        self.e = e
        self.f = f
        self.relative = relative

    def __str__(self) -> str:
        line = ""
        if self.x is not None:
            line += f" X{format_gcode_number(self.x)}"
        if self.y is not None:
            line += f" Y{format_gcode_number(self.y)}"
        if self.z is not None:
            line += f" Z{format_gcode_number(self.z)}"
        if self.e is not None:
            line += f" E{format_gcode_number(self.e)}"
        if self.f is not None:
            line += f" F{format_gcode_number(self.f)}"
        return line

    def pos(self) -> tuple[float, float, float]:
        return (
            (
                self.p[0] + (self.x or 0),
                self.p[1] + (self.y or 0),
                self.p[2] + (self.z or 0),
            )
            if self.relative
            else (self.x or self.p[0], self.y or self.p[1], self.z or self.p[2])
        )

    def delta(self) -> tuple[float, float, float]:
        return (
            (self.x or 0, self.y or 0, self.z or 0)
            if self.relative
            else (
                self.x - self.p[0] if self.x is not None else 0,
                self.y - self.p[1] if self.y is not None else 0,
                self.z - self.p[2] if self.z is not None else 0,
            )
        )

    def length(self) -> float:
        delta = self.delta()
        return math.sqrt(delta[0] ** 2 + delta[1] ** 2 + delta[2] ** 2)

    def contour_z(
        self,
        scene,
        z: float,
        height: float,
        ironing_line: bool,
        outer_line: bool,
        resolution=0.1,
        demo_split: float | None = None,
    ) -> list["Extrusion"]:
        if open3d is None:
            raise RuntimeError("open3d is required for contour_z raycasting")
        if self.relative:
            raise ValueError("Cannot contour with relative positioning")
        if not self.e:
            raise ValueError("Cannot contour with no extrusion")

        dx, dy, _ = self.delta()
        l = math.sqrt(dx**2 + dy**2)
        dir = (dx / l, dy / l)

        self.p = (self.p[0], self.p[1], z)

        num_segments = math.ceil(self.length() / resolution)
        rays_up = [
            [
                self.p[0] + dx * i / num_segments,
                self.p[1] + dy * i / num_segments,
                z,
                0,
                0,
                1,
            ]
            for i in range(num_segments + 1)
        ]
        hits_up = scene.cast_rays(
            open3d.core.Tensor(rays_up, dtype=open3d.core.Dtype.Float32)
        )
        rays_down = [
            [
                self.p[0] + dx * i / num_segments,
                self.p[1] + dy * i / num_segments,
                z,
                0,
                0,
                -1,
            ]
            for i in range(num_segments + 1)
        ]
        hits_down = scene.cast_rays(
            open3d.core.Tensor(rays_down, dtype=open3d.core.Dtype.Float32)
        )

        extrusion_rate = self.e / self.length()

        segments = []
        p = self.p
        for i in range(num_segments + 1):
            hit_up = max(0, abs(hits_up["t_hit"][i].item()))
            hit_down = max(0, abs(hits_down["t_hit"][i].item()))
            normal_up = hits_up["primitive_normals"][i]
            normal_down = hits_down["primitive_normals"][i]
            use_up = (
                (normal_up[2].item() > 0 and normal_up[2].item() <= 0)
                or normal_down[2].item() <= 0
                or hit_up <= hit_down
            )

            if use_up and hit_up <= height / 2 + 1e-6:
                d = min(height / 2, hit_up)
            elif normal_down[2].item() > 0 and hit_down <= height / 2 + 1e-6:
                d = max(-height / 2, -hit_down)
            else:
                d = 0

            do_split = demo_split is not None and rays_up[i][1] < demo_split

            segment = Extrusion(
                p=p,
                x=rays_up[i][0],
                y=rays_up[i][1],
                z=z if do_split else z + d,
                e=None,
                f=self.f,
                relative=False,
            )
            if segment.length() == 0:
                continue
            segment.meta = f"d={d:.3g}"

            if i != 0:
                extrusion_height = height + d
                segment.meta = f"e={extrusion_height:.3g} {segment.meta}"
                segment.e = (
                    extrusion_rate * segment.length()
                    if ironing_line or do_split
                    else (
                        extrusion_rate * segment.length() * (extrusion_height / height)
                    )
                )
                segment.e = segment.e if segment.e > 0 else 0

            if (
                len(segments) > 1
                and segments[-2].z == segment.z
                and segments[-1].z == segment.z
                and segments[-2].e is not None
                and segments[-1].e is not None
                and segment.e is not None
            ):
                segment.e += segments[-1].e
                segment.meta = segments[-1].meta + " " + segment.meta
                segments[-1] = segment
            else:
                segments.append(segment)
            p = segment.pos()

        return segments
