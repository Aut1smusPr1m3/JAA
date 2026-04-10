#!/usr/bin/env python3
"""
Comprehensive Test Suite for GCodeZAA Tensor Batching, Physics Compensation, 
Vector-Aligned Retraction, and Non-Planar Ironing
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'GCodeZAA'))

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_batch_surface_analysis():
    """Test tensor batching in surface analysis"""
    try:
        from GCodeZAA.gcodezaa.surface_analysis import SurfaceAnalyzer
        
        sa = SurfaceAnalyzer(raycasting_scene=None)
        
        # Test with empty model (no raycasting)
        points = [(0, 0, 0), (1, 1, 1), (2, 2, 2)]
        results = sa.batch_analyze_points(points, layer_height=0.2)
        
        assert len(results) == len(points), "Batch size mismatch"
        assert all("z_offset" in r for r in results), "Missing z_offset in results"
        assert all("normal" in r for r in results), "Missing normal in results"
        assert all("confidence" in r for r in results), "Missing confidence in results"
        
        logger.info("✓ Batch surface analysis works")
        return True
    except Exception as e:
        logger.error(f"✗ Batch surface analysis failed: {e}")
        return False

def test_batch_edge_detection():
    """Test batched edge detection"""
    try:
        from GCodeZAA.gcodezaa.surface_analysis import EdgeDetector
        
        ed = EdgeDetector(threshold_angle=45)
        
        # Test sequence of normals
        normals = [
            (0, 0, 1),    # Flat top
            (0, 0.1, 0.9), # Slight tilt
            (0.5, 0, 0.87), # 30° tilt - should detect edge
            (1, 0, 0),     # Vertical wall - strong edge
        ]
        
        results = ed.batch_detect_edges(normals)
        
        assert len(results) == len(normals), "Batch detection size mismatch"
        assert all(isinstance(r, tuple) for r in results), "Results not tuples"
        assert all(len(r) == 2 for r in results), "Result tuples wrong size"
        
        logger.info(f"✓ Batch edge detection works ({len(results)} edges detected)")
        return True
    except Exception as e:
        logger.error(f"✗ Batch edge detection failed: {e}")
        return False

def test_physics_compensation():
    """Test physics-based extrusion compensation"""
    try:
        from GCodeZAA.gcodezaa.process import compensate_extrusion_physics
        
        # Test case: Z offset increases effective layer height
        base_e = 10.0
        z_offset = 0.1
        layer_height = 0.2
        line_width = 0.4
        normal = (0, 0, 1)  # Upward facing
        confidence = 0.8
        
        # Linear mode
        result_linear = compensate_extrusion_physics(
            base_e, z_offset, layer_height, line_width, normal, confidence, "linear"
        )
        
        # Physics mode
        result_physics = compensate_extrusion_physics(
            base_e, z_offset, layer_height, line_width, normal, confidence, "physics"
        )
        
        # Both should be >= base (higher Z means more material needed)
        assert result_linear >= base_e, f"Linear: {result_linear} < {base_e}"
        assert result_physics >= base_e, f"Physics: {result_physics} < {base_e}"
        
        # Physics should account for normal angle
        normal_tilted = (0.5, 0, 0.87)  # ~30° tilt
        result_tilted = compensate_extrusion_physics(
            base_e, z_offset, layer_height, line_width, normal_tilted, confidence, "physics"
        )
        
        # Tilted surface should have less compensation than vertical
        assert result_tilted < result_physics, "Tilt adjustment not working"
        
        logger.info(f"✓ Physics compensation works (base={base_e}, linear={result_linear:.2f}, physics={result_physics:.2f}, tilted={result_tilted:.2f})")
        return True
    except Exception as e:
        logger.error(f"✗ Physics compensation failed: {e}")
        return False

def test_vector_aligned_retraction():
    """Test vector-aligned retraction calculation"""
    try:
        from GCodeZAA.gcodezaa.process import create_vector_aligned_retraction
        
        current_pos = (10, 10, 5)
        
        # Test upward normal
        normal_up = (0, 0, 1)
        retract_up = create_vector_aligned_retraction(current_pos, normal_up, retraction_length=1.5, layer_height=0.2)
        
        assert isinstance(retract_up, tuple), "Not a tuple"
        assert len(retract_up) == 3, "Wrong dimensions"
        assert retract_up[2] > 0, "Z component should be positive for upward retract"
        
        # Test angled normal
        normal_angle = (0.707, 0, 0.707)  # 45° angle
        retract_angle = create_vector_aligned_retraction(current_pos, normal_angle, retraction_length=1.5, layer_height=0.2)
        
        # Both X and Z should be non-zero
        assert retract_angle[0] != 0, "X component missing"
        assert retract_angle[2] != 0, "Z component missing"
        
        logger.info(f"✓ Vector-aligned retraction works (up={retract_up}, angle={retract_angle})")
        return True
    except Exception as e:
        logger.error(f"✗ Vector-aligned retraction failed: {e}")
        return False

def test_nonplanar_ironing_path():
    """Test non-planar ironing path generation"""
    try:
        from GCodeZAA.gcodezaa.surface_analysis import SurfaceAnalyzer
        
        sa = SurfaceAnalyzer(raycasting_scene=None)
        
        # Generate ironing path along a line
        ironing_path = sa.get_nonplanar_ironing_path(
            x1=0, y1=0, z=0.2,
            x2=10, y2=0,
            layer_height=0.2,
            sample_distance=1.0
        )
        
        assert isinstance(ironing_path, list), "Should return list"
        assert len(ironing_path) > 0, "Should have waypoints"
        
        for waypoint in ironing_path:
            assert "x" in waypoint, "Missing x"
            assert "y" in waypoint, "Missing y"
            assert "adjusted_z" in waypoint, "Missing adjusted_z"
            assert "ironing_extrusion_factor" in waypoint, "Missing extrusion factor"
            assert "feedrate_factor" in waypoint, "Missing feedrate factor"
            
            # Check reduction factors
            assert 0 < waypoint["ironing_extrusion_factor"] < 1, "Extrusion should be reduced"
            assert 0 < waypoint["feedrate_factor"] < 1, "Feedrate should be reduced"
        
        logger.info(f"✓ Non-planar ironing path works ({len(ironing_path)} waypoints)")
        return True
    except Exception as e:
        logger.error(f"✗ Non-planar ironing path failed: {e}")
        return False

def test_segment_batch_analysis():
    """Test batch analysis of a segment"""
    try:
        from GCodeZAA.gcodezaa.surface_analysis import SurfaceAnalyzer
        
        sa = SurfaceAnalyzer(raycasting_scene=None)
        
        # Analyze a segment from (0,0) to (10,0)
        analysis = sa.analyze_segment_batch(
            x1=0, y1=0, z=0.2,
            x2=10, y2=0,
            layer_height=0.2,
            sample_distance=2.0
        )
        
        assert isinstance(analysis, list), "Should return list"
        assert len(analysis) >= 2, "Should have at least 2 points"
        
        for point in analysis:
            assert "x" in point and "y" in point, "Missing coordinates"
            assert "z_offset" in point, "Missing z_offset"
            assert "index" in point and "total" in point, "Missing metadata"
        
        logger.info(f"✓ Segment batch analysis works ({len(analysis)} samples)")
        return True
    except Exception as e:
        logger.error(f"✗ Segment batch analysis failed: {e}")
        return False

def test_retraction_vector_magnitude():
    """Test that retraction vectors scale properly"""
    try:
        from GCodeZAA.gcodezaa.process import create_vector_aligned_retraction
        import math
        
        normal = (0, 0, 1)
        retract1 = create_vector_aligned_retraction((0,0,0), normal, 1.5, 0.2)
        retract2 = create_vector_aligned_retraction((0,0,0), normal, 1.5, 0.4)  # Double layer height
        
        # Calculate magnitudes
        mag1 = math.sqrt(sum(x**2 for x in retract1))
        mag2 = math.sqrt(sum(x**2 for x in retract2))
        
        # Larger layer height should give larger retraction
        assert mag2 > mag1, f"Layer height scaling failed: {mag2} <= {mag1}"
        
        logger.info(f"✓ Retraction vector scaling works (0.2mm: {mag1:.3f}, 0.4mm: {mag2:.3f})")
        return True
    except Exception as e:
        logger.error(f"✗ Retraction scaling failed: {e}")
        return False

def main():
    logger.info("=" * 70)
    logger.info("Testing Enhanced GCodeZAA: Tensor Batching, Physics, Retraction, Ironing")
    logger.info("=" * 70)
    
    tests = [
        ("Batch Surface Analysis", test_batch_surface_analysis),
        ("Batch Edge Detection", test_batch_edge_detection),
        ("Physics-Based Extrusion Compensation", test_physics_compensation),
        ("Vector-Aligned Retraction", test_vector_aligned_retraction),
        ("Non-Planar Ironing Path", test_nonplanar_ironing_path),
        ("Segment Batch Analysis", test_segment_batch_analysis),
        ("Retraction Vector Scaling", test_retraction_vector_magnitude),
    ]
    
    results = []
    for name, test_func in tests:
        logger.info(f"\n{name}...")
        result = test_func()
        results.append((name, result))
    
    logger.info("\n" + "=" * 70)
    logger.info("Test Results Summary")
    logger.info("=" * 70)
    
    passing = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info(f"\nTotal: {passing}/{total} tests passed")
    logger.info("=" * 70)
    
    return all(r for _, r in results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
