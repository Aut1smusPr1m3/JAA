"""
Enhanced Surface Analysis Module for GCodeZAA with Tensor Batching
Provides optimized batch raycasting, normal analysis, vector-aligned retraction, 
and true non-planar ironing support.
"""

import math
import logging
import os
import numpy as np
from typing import Tuple, Optional, List, Dict
from gcodezaa.config import DEFAULT_MAX_SMOOTHING_ANGLE

try:
    import open3d
except ModuleNotFoundError:
    open3d = None

logger = logging.getLogger(__name__)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        logger.warning("Invalid float for %s=%r; using default=%s", name, value, default)
        return default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("Invalid int for %s=%r; using default=%s", name, value, default)
        return default

# Configuration
SURFACE_SAMPLE_DISTANCE = _env_float("GCODEZAA_SAMPLE_DISTANCE_MM", 0.2)  # mm between raycasting points
MIN_SAMPLE_DISTANCE = _env_float("GCODEZAA_MIN_SAMPLE_DISTANCE_MM", 0.08)  # mm minimum sample spacing
MAX_SAMPLE_DISTANCE = _env_float("GCODEZAA_MAX_SAMPLE_DISTANCE_MM", 0.5)   # mm maximum sample spacing for long segments
MAX_SEGMENT_SAMPLES = max(16, _env_int("GCODEZAA_MAX_SEGMENT_SAMPLES", 384))
MAX_SURFACE_FOLLOW_SEGMENT_MM = _env_float("GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM", 1000.0)
MAX_RAY_DISTANCE = 2.0  # mm maximum cast distance
MAX_Z_OFFSET = 1.8  # mm maximum surface offset allowed
HARD_MAX_SMOOTHING_ANGLE = 20.0
MAX_SMOOTHING_ANGLE = min(DEFAULT_MAX_SMOOTHING_ANGLE, HARD_MAX_SMOOTHING_ANGLE)  # degrees from vertical where full offset is allowed
NORMAL_SMOOTHING_WINDOW = 5  # samples for normal averaging
SLOPE_SMOOTHING_WINDOW = 5  # samples for z-offset smoothing
EDGE_THRESHOLD_ANGLE = 45  # degrees for edge detection
BATCH_RAY_SIZE = max(256, _env_int("GCODEZAA_BATCH_RAY_SIZE", 4096))  # Number of points to process in one batch


class SurfaceAnalyzer:
    """Analyzes surfaces using STL raycasting with tensor batching for performance."""
    
    def __init__(self, raycasting_scene: Optional[object] = None, device: Optional[object] = None):
        self.scene = raycasting_scene
        self.device = device
        self.normal_history = []
        self.last_surface_z = 0.0
        self.last_normal = (0.0, 0.0, 1.0)
        self.ray_cache = {}  # Cache for repeated ray queries

    def _adaptive_sample_distance(self, distance: float, default: float) -> float:
        """Choose a sample spacing that balances detail and coherence for long paths."""
        if distance <= 1.0:
            return max(MIN_SAMPLE_DISTANCE, default)
        if distance <= 5.0:
            return min(MAX_SAMPLE_DISTANCE, max(MIN_SAMPLE_DISTANCE, default))
        if distance <= 20.0:
            return min(MAX_SAMPLE_DISTANCE, max(default, 0.2))
        return min(MAX_SAMPLE_DISTANCE, max(default, 0.35))
        
    def batch_analyze_points(
        self, 
        points: List[Tuple[float, float, float]],
        layer_height: float = 0.2
    ) -> List[Dict]:
        """
        Batch analyze multiple points efficiently using tensor operations.
        
        Args:
            points: List of (x, y, z) tuples to analyze
            layer_height: Layer height for max Z deviation calculation
            
        Returns:
            List of analysis results with z_offset, confidence, normal, normal_x/y/z
        """
        if self.scene is None or len(points) == 0:
            return [{"z_offset": 0, "confidence": 0, "normal": (0, 0, 1), 
                    "normal_x": 0, "normal_y": 0, "normal_z": 1} for _ in points]

        points_np = np.asarray(points, dtype=np.float32)
        if points_np.ndim != 2 or points_np.shape[1] != 3:
            raise ValueError("points must be an array-like of shape (N, 3)")
        
        results = []
        max_z_dev = layer_height / 2.0
        
        # Process in batches for memory efficiency
        for batch_start in range(0, len(points_np), BATCH_RAY_SIZE):
            batch_end = min(batch_start + BATCH_RAY_SIZE, len(points_np))
            batch_points = points_np[batch_start:batch_end]
            count = batch_points.shape[0]

            # Submit up/down rays in one cast to reduce Python<->Open3D overhead.
            rays = np.empty((count * 2, 6), dtype=np.float32)
            rays[:count, :3] = batch_points
            rays[:count, 3:] = (0.0, 0.0, 1.0)
            rays[count:, :3] = batch_points
            rays[count:, 3:] = (0.0, 0.0, -1.0)
            
            # Execute batch raycasts
            try:
                if self.device is not None:
                    rays_tensor = open3d.core.Tensor(
                        rays,
                        dtype=open3d.core.Dtype.Float32,
                        device=self.device,
                    )
                else:
                    rays_tensor = open3d.core.Tensor(
                        rays,
                        dtype=open3d.core.Dtype.Float32,
                    )
                cast_result = self.scene.cast_rays(rays_tensor)

                t_hit = cast_result["t_hit"].numpy()
                normals = cast_result["primitive_normals"].numpy()
                dist_up = t_hit[:count]
                dist_down = t_hit[count:]
                normals_up = normals[:count]
                normals_down = normals[count:]
                
                # Process results
                for i in range(count):
                    z_offset, confidence, normal = self._select_surface_hit(
                        float(dist_up[i]),
                        float(dist_down[i]),
                        normals_up[i],
                        normals_down[i],
                        max_z_dev,
                    )
                    
                    # Apply normal smoothing
                    smoothed_normal = self._smooth_normal(normal)
                    
                    results.append({
                        "z_offset": z_offset,
                        "confidence": confidence,
                        "normal": smoothed_normal,
                        "normal_x": smoothed_normal[0],
                        "normal_y": smoothed_normal[1],
                        "normal_z": smoothed_normal[2],
                        "original_normal": normal
                    })
                    
                    self.normal_history.append((smoothed_normal, confidence))
                    if len(self.normal_history) > NORMAL_SMOOTHING_WINDOW:
                        self.normal_history.pop(0)
                    
                    self.last_normal = smoothed_normal
                    
            except Exception as e:
                logger.debug(f"Batch raycasting error: {e}")
                results.extend([
                    {"z_offset": 0, "confidence": 0, "normal": (0, 0, 1), 
                     "normal_x": 0, "normal_y": 0, "normal_z": 1} 
                    for _ in range(count)
                ])
        
        return results
    
    def _select_surface_hit(
        self,
        dist_up: float,
        dist_down: float,
        normal_up: np.ndarray,
        normal_down: np.ndarray,
        max_z_dev: float,
    ) -> Tuple[float, float, Tuple]:
        """Select the appropriate surface based on raycasting results."""
        normal_up_t = (float(normal_up[0]), float(normal_up[1]), float(normal_up[2]))
        normal_down_t = (float(normal_down[0]), float(normal_down[1]), float(normal_down[2]))
        
        # Prefer upper surface if within tolerance and facing up
        if math.isfinite(dist_up) and normal_up_t[2] > 0.1 and 0 < dist_up <= max_z_dev:
            z_offset = min(max_z_dev, dist_up)
            confidence = min(1.0, abs(normal_up_t[2]) * 1.5)
            z_offset = self._clamp_z_offset(z_offset, normal_up_t)
            return z_offset, confidence, normal_up_t

        # Fall back to lower surface if facing down
        if math.isfinite(dist_down) and normal_down_t[2] < -0.1 and 0 < dist_down <= max_z_dev:
            z_offset = max(-max_z_dev, -dist_down)
            confidence = min(1.0, abs(normal_down_t[2]) * 1.5)
            z_offset = self._clamp_z_offset(z_offset, normal_down_t)
            return z_offset, confidence, normal_down_t

        return 0, 0, (0, 0, 1)
    
    def _smooth_normal(self, normal: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Apply smoothing to reduce normal jitter."""
        if not self.normal_history or NORMAL_SMOOTHING_WINDOW < 1:
            return normal
        
        window_size = min(len(self.normal_history), NORMAL_SMOOTHING_WINDOW)
        recent_normals = self.normal_history[-window_size:]
        
        # Window average
        avg_x = sum(n[0] for n, _ in recent_normals) / window_size
        avg_y = sum(n[1] for n, _ in recent_normals) / window_size
        avg_z = sum(n[2] for n, _ in recent_normals) / window_size
        
        # Normalize
        mag = math.sqrt(avg_x**2 + avg_y**2 + avg_z**2)
        if mag > 0:
            return (avg_x / mag, avg_y / mag, avg_z / mag)
        return normal

    def _smooth_analysis(self, results: List[Dict]) -> List[Dict]:
        """Smooth z-offset and normal data across a small neighborhood."""
        if len(results) < 2:
            return results

        smoothed = []
        for idx in range(len(results)):
            window_start = max(0, idx - SLOPE_SMOOTHING_WINDOW // 2)
            window_end = min(len(results), idx + SLOPE_SMOOTHING_WINDOW // 2 + 1)
            window = results[window_start:window_end]

            weight_sum = sum(item["confidence"] + 0.5 for item in window)
            if weight_sum == 0:
                smoothed.append(results[idx])
                continue

            avg_z = sum(item["z_offset"] * (item["confidence"] + 0.5) for item in window) / weight_sum
            avg_x = sum(item["normal_x"] * (item["confidence"] + 0.5) for item in window) / weight_sum
            avg_y = sum(item["normal_y"] * (item["confidence"] + 0.5) for item in window) / weight_sum
            avg_z_n = sum(item["normal_z"] * (item["confidence"] + 0.5) for item in window) / weight_sum

            mag = math.sqrt(avg_x**2 + avg_y**2 + avg_z_n**2)
            if mag > 0:
                avg_normal = (avg_x / mag, avg_y / mag, avg_z_n / mag)
            else:
                avg_normal = results[idx]["normal"]

            avg_z = self._clamp_z_offset(avg_z, avg_normal)
            smoothed.append({
                **results[idx],
                "z_offset": avg_z,
                "confidence": min(1.0, max(results[idx]["confidence"], weight_sum / len(window) / 1.5)),
                "normal": avg_normal,
                "normal_x": avg_normal[0],
                "normal_y": avg_normal[1],
                "normal_z": avg_normal[2],
            })

        return smoothed

    def _clamp_z_offset(self, z_offset: float, normal: Tuple[float, float, float]) -> float:
        """Clamp Z deviations based on surface slope and safety limits."""
        if z_offset == 0.0:
            return 0.0

        vertical = max(-1.0, min(1.0, normal[2]))
        slope_angle = math.degrees(math.acos(abs(vertical)))
        if slope_angle <= 0 or slope_angle > 90:
            slope_angle = min(max(slope_angle, 0.0), 90.0)

        if slope_angle > MAX_SMOOTHING_ANGLE:
            limit = MAX_Z_OFFSET * (MAX_SMOOTHING_ANGLE / slope_angle)
        else:
            limit = MAX_Z_OFFSET

        return max(-limit, min(limit, z_offset))

    def _normalize(self, vector: Tuple[float, float, float]) -> Tuple[float, float, float]:
        mag = math.sqrt(vector[0]**2 + vector[1]**2 + vector[2]**2)
        if mag == 0:
            return vector
        return (vector[0] / mag, vector[1] / mag, vector[2] / mag)

    def analyze_segment_batch(
        self,
        x1: float, y1: float, z: float,
        x2: float, y2: float,
        layer_height: float = 0.2,
        sample_distance: float = SURFACE_SAMPLE_DISTANCE
    ) -> List[Dict]:
        """
        Batch analyze a motion segment by sampling points along the path.
        Returns detailed analysis for each waypoint.
        """
        dx = x2 - x1
        dy = y2 - y1
        distance = math.sqrt(dx * dx + dy * dy)

        # Guard against implausible jumps caused by upstream state pollution (for example
        # relative-motion macro sections leaking into absolute print-state tracking).
        if distance > MAX_SURFACE_FOLLOW_SEGMENT_MM:
            logger.warning(
                "Skipping surface-following for implausible segment: distance=%.2fmm (max=%.2fmm) start=(%.3f, %.3f) end=(%.3f, %.3f)",
                distance,
                MAX_SURFACE_FOLLOW_SEGMENT_MM,
                x1,
                y1,
                x2,
                y2,
            )
            return []

        if distance < MIN_SAMPLE_DISTANCE:
            return []

        sample_distance = self._adaptive_sample_distance(distance, sample_distance)
        sample_distance = max(MIN_SAMPLE_DISTANCE, min(sample_distance, MAX_SAMPLE_DISTANCE))
        requested_points = max(2, int(distance / sample_distance) + 1)
        num_points = min(MAX_SEGMENT_SAMPLES, requested_points)

        if num_points < requested_points:
            sample_distance = distance / max(1, num_points - 1)
            logger.debug(
                "Segment sampling capped: distance=%.2fmm requested=%d capped=%d spacing=%.3fmm",
                distance,
                requested_points,
                num_points,
                sample_distance,
            )

        t_values = np.linspace(0.0, 1.0, num_points, dtype=np.float32)
        points = np.column_stack(
            (
                x1 + dx * t_values,
                y1 + dy * t_values,
                np.full(num_points, z, dtype=np.float32),
            )
        )

        # Batch analyze all points
        analysis = self.batch_analyze_points(points, layer_height)
        analysis = self._smooth_analysis(analysis)

        # Enrich with position data
        for i, (x, y, z_value) in enumerate(points):
            if i < len(analysis):
                analysis[i].update({
                    "x": float(x),
                    "y": float(y),
                    "z": float(z_value),
                    "adjusted_z": float(z_value + analysis[i]["z_offset"]),
                    "index": i,
                    "total": num_points
                })

        return analysis
    
    def get_retraction_vector(
        self,
        surface_normal: Tuple[float, float, float],
        layer_height: float = 0.2
    ) -> Tuple[float, float, float]:
        """
        Get vector-aligned retraction direction (along surface normal away from surface).
        This reduces ooze and string formation during retractions.
        """
        # Retract along surface normal, away from surface
        # Scale by layer height for consistent non-planar behavior.
        scale = layer_height * 2.0  # Reasonable retraction distance
        return (
            surface_normal[0] * scale,
            surface_normal[1] * scale,
            surface_normal[2] * scale
        )
    
    def get_nonplanar_ironing_path(
        self,
        x1: float, y1: float, z: float,
        x2: float, y2: float,
        layer_height: float = 0.2,
        sample_distance: float = 0.5  # Coarser sampling for ironing
    ) -> List[Dict]:
        """
        Generate a non-planar ironing path that follows the actual surface contour.
        Returns waypoints with adjusted Z coordinates following the surface.
        """
        sample_distance = self._adaptive_sample_distance(
            math.hypot(x2 - x1, y2 - y1), sample_distance
        )
        analysis = self.analyze_segment_batch(
            x1, y1, z, x2, y2, layer_height, sample_distance
        )
        
        # For ironing, use the adjusted Z values directly
        for point in analysis:
            # Reduce extrusion for ironing moves
            point["ironing_extrusion_factor"] = 0.3  # Reduced extrusion for surface following
            point["feedrate_factor"] = 0.7  # Slower ironing movement
        
        return analysis


class EdgeDetector:
    """Detects edges and discontinuities with batch processing support."""
    
    def __init__(self, threshold_angle: float = EDGE_THRESHOLD_ANGLE):
        self.threshold_angle = threshold_angle
        self.previous_normal = (0.0, 0.0, 1.0)
    
    def detect_edge(self, normal: Tuple[float, float, float]) -> Tuple[bool, float]:
        """
        Detect if this is an edge based on normal change.
        Returns: (is_edge, angle_change_degrees)
        """
        angle = self.angle_between(self.previous_normal, normal)
        self.previous_normal = normal
        return angle > self.threshold_angle, angle
    
    def batch_detect_edges(self, normals: List[Tuple[float, float, float]]) -> List[Tuple[bool, float]]:
        """
        Batch detect edges in a sequence of normals.
        Returns list of (is_edge, angle_change) tuples.
        """
        results = []
        for normal in normals:
            is_edge, angle = self.detect_edge(normal)
            results.append((is_edge, angle))
        return results
    
    @staticmethod
    def angle_between(v1: Tuple[float, float, float], v2: Tuple[float, float, float]) -> float:
        """Calculate angle between two vectors in degrees."""
        dot = v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]
        mag1 = math.sqrt(v1[0]**2 + v1[1]**2 + v1[2]**2)
        mag2 = math.sqrt(v2[0]**2 + v2[1]**2 + v2[2]**2)
        
        if mag1 == 0 or mag2 == 0:
            return 0
        
        cos_angle = dot / (mag1 * mag2)
        cos_angle = max(-1, min(1, cos_angle))  # Clamp to [-1, 1]
        
        return math.degrees(math.acos(cos_angle))
