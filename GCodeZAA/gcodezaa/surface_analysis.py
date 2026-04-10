"""
Enhanced Surface Analysis Module for GCodeZAA with Tensor Batching
Provides optimized batch raycasting, normal analysis, vector-aligned retraction, 
and true non-planar ironing support.
"""

import math
import logging
import open3d
import numpy as np
from typing import Tuple, Optional, List, Dict

logger = logging.getLogger(__name__)

# Configuration
SURFACE_SAMPLE_DISTANCE = 0.05  # mm between raycasting points
MIN_SAMPLE_DISTANCE = 0.05  # mm minimum sample spacing
MAX_SAMPLE_DISTANCE = 0.5   # mm maximum sample spacing for long segments
MAX_RAY_DISTANCE = 2.0  # mm maximum cast distance
MAX_Z_OFFSET = 0.35  # mm maximum surface offset allowed
MAX_SMOOTHING_ANGLE = 40.0  # degrees from vertical beyond which smoothing is reduced
NORMAL_SMOOTHING_WINDOW = 5  # samples for normal averaging
SLOPE_SMOOTHING_WINDOW = 5  # samples for z-offset smoothing
EDGE_THRESHOLD_ANGLE = 45  # degrees for edge detection
BATCH_RAY_SIZE = 1024  # Number of rays to process in one batch


class SurfaceAnalyzer:
    """Analyzes surfaces using STL raycasting with tensor batching for performance."""
    
    def __init__(self, raycasting_scene: Optional[open3d.t.geometry.RaycastingScene] = None):
        self.scene = raycasting_scene
        self.normal_history = []
        self.last_surface_z = 0.0
        self.last_normal = (0.0, 0.0, 1.0)
        self.ray_cache = {}  # Cache for repeated ray queries

    def _adaptive_sample_distance(self, distance: float, default: float) -> float:
        """Choose a sample spacing that balances detail and coherence for long paths."""
        if distance <= 1.0:
            return max(MIN_SAMPLE_DISTANCE, default * 0.5)
        if distance <= 5.0:
            return max(MIN_SAMPLE_DISTANCE, min(default, 0.1))
        if distance <= 20.0:
            return min(MAX_SAMPLE_DISTANCE, max(default, 0.15))
        return MAX_SAMPLE_DISTANCE
        
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
        if self.scene is None or not points:
            return [{"z_offset": 0, "confidence": 0, "normal": (0, 0, 1), 
                    "normal_x": 0, "normal_y": 0, "normal_z": 1} for _ in points]
        
        results = []
        max_z_dev = layer_height / 2.0
        
        # Process in batches for memory efficiency
        for batch_start in range(0, len(points), BATCH_RAY_SIZE):
            batch_end = min(batch_start + BATCH_RAY_SIZE, len(points))
            batch_points = points[batch_start:batch_end]
            
            # Create rays for upward direction (0, 0, 1)
            rays_up = []
            for x, y, z in batch_points:
                rays_up.append([x, y, z, 0, 0, 1])
            
            # Create rays for downward direction (0, 0, -1)
            rays_down = []
            for x, y, z in batch_points:
                rays_down.append([x, y, z, 0, 0, -1])
            
            # Execute batch raycasts
            try:
                rays_up_tensor = open3d.core.Tensor(rays_up, dtype=open3d.core.Dtype.Float32)
                rays_down_tensor = open3d.core.Tensor(rays_down, dtype=open3d.core.Dtype.Float32)
                
                result_up = self.scene.cast_rays(rays_up_tensor)
                result_down = self.scene.cast_rays(rays_down_tensor)
                
                # Process results
                for i in range(len(batch_points)):
                    z_offset, confidence, normal = self._select_surface_hit(
                        result_up, result_down, i, max_z_dev
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
                    for _ in batch_points
                ])
        
        return results
    
    def _select_surface_hit(self, result_up, result_down, index: int, max_z_dev: float) -> Tuple[float, float, Tuple]:
        """Select the appropriate surface based on raycasting results."""
        dist_up = float(result_up["t_hit"][index].item())
        dist_down = float(result_down["t_hit"][index].item())
        
        normal_up = (
            float(result_up["primitive_normals"][index][0].item()),
            float(result_up["primitive_normals"][index][1].item()),
            float(result_up["primitive_normals"][index][2].item())
        )
        normal_down = (
            float(result_down["primitive_normals"][index][0].item()),
            float(result_down["primitive_normals"][index][1].item()),
            float(result_down["primitive_normals"][index][2].item())
        )
        
        # Prefer upper surface if within tolerance and facing up
        if normal_up[2] > 0.1 and 0 < dist_up <= max_z_dev:
            z_offset = min(max_z_dev, dist_up)
            confidence = min(1.0, abs(normal_up[2]) * 1.5)
            z_offset = self._clamp_z_offset(z_offset, normal_up)
            return z_offset, confidence, normal_up

        # Fall back to lower surface if facing down
        if normal_down[2] < -0.1 and 0 < dist_down <= max_z_dev:
            z_offset = max(-max_z_dev, -dist_down)
            confidence = min(1.0, abs(normal_down[2]) * 1.5)
            z_offset = self._clamp_z_offset(z_offset, normal_down)
            return z_offset, confidence, normal_down

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

        if distance < MIN_SAMPLE_DISTANCE:
            return []

        sample_distance = self._adaptive_sample_distance(distance, sample_distance)
        sample_distance = max(MIN_SAMPLE_DISTANCE, min(sample_distance, MAX_SAMPLE_DISTANCE))
        num_points = max(3, int(distance / sample_distance) + 1)
        points = []

        for i in range(num_points):
            t = i / (num_points - 1)
            x = x1 + dx * t
            y = y1 + dy * t
            points.append((x, y, z))

        # Batch analyze all points
        analysis = self.batch_analyze_points(points, layer_height)
        analysis = self._smooth_analysis(analysis)

        # Enrich with position data
        for i, (x, y, z) in enumerate(points):
            if i < len(analysis):
                analysis[i].update({
                    "x": x,
                    "y": y,
                    "z": z,
                    "adjusted_z": z + analysis[i]["z_offset"],
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
        # Scale by reasonable distance (layer height is a good heuristic)
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
