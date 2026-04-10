#!/usr/bin/env python3
"""
Test script for enhanced GCodeZAA pipeline integration
Tests: Surface analysis, arc decomposition, extrusion compensation
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'GCodeZAA'))

import logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_surface_analysis_imports():
    """Test that surface analysis modules import correctly"""
    try:
        from GCodeZAA.gcodezaa.surface_analysis import SurfaceAnalyzer, EdgeDetector
        logger.info("✓ Surface analysis imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ Surface analysis import failed: {e}")
        return False

def test_process_line_signature():
    """Test that process_line has correct signature with surface analysis"""
    try:
        from GCodeZAA.gcodezaa.process import process_line
        import inspect
        
        sig = inspect.signature(process_line)
        params = list(sig.parameters.keys())
        
        # Should have: ctx, surface_analyzer, edge_detector
        if len(params) >= 3:
            logger.info(f"✓ process_line signature updated: {params}")
            return True
        else:
            logger.error(f"✗ process_line missing parameters: {params}")
            return False
    except Exception as e:
        logger.error(f"✗ process_line test failed: {e}")
        return False

def test_arc_decomposition():
    """Test that G2/G3 arc decomposition works"""
    try:
        from GCodeZAA.gcodezaa.process import decompose_arc
        import math
        
        # Test simple circular arc
        waypoints = decompose_arc(
            start_pos=(0, 0, 0),
            end_x=10,
            end_y=0,
            end_z=0,
            center_i=5,
            center_j=0,
            radius=None,
            is_clockwise=True,
            segment_length=1.0
        )
        
        if len(waypoints) >= 2:
            logger.info(f"✓ Arc decomposition works: {len(waypoints)} waypoints")
            return True
        else:
            logger.error("✗ Arc decomposition failed: insufficient waypoints")
            return False
    except Exception as e:
        logger.error(f"✗ Arc decomposition test failed: {e}")
        return False

def test_context_enhancements():
    """Test that ProcessorContext has surface tracking"""
    try:
        from GCodeZAA.gcodezaa.context import ProcessorContext
        import inspect
        
        # Get the source code to verify enhancements
        source = inspect.getsource(ProcessorContext)
        
        # Check for new attributes/methods in source
        has_normal_history = 'normal_history' in source
        has_z_offset_history = 'z_offset_history' in source
        has_record_surface_normal = 'record_surface_normal' in source
        
        if has_normal_history and has_z_offset_history and has_record_surface_normal:
            logger.info("✓ ProcessorContext enhancements present")
            return True
        else:
            logger.error("✗ ProcessorContext missing enhancements")
            return False
    except Exception as e:
        logger.error(f"✗ Context test failed: {e}")
        return False

def test_extrusion_enhancements():
    """Test that extrusion module has new functions"""
    try:
        from GCodeZAA.gcodezaa.extrusion import calculate_arc_radius
        import inspect
        
        # Test function exists
        source = inspect.getsource(calculate_arc_radius)
        if source:
            logger.info("✓ Extrusion enhancements present")
            return True
    except Exception as e:
        logger.error(f"✗ Extrusion test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("Testing Enhanced GCodeZAA Pipeline Integration")
    logger.info("=" * 60)
    
    tests = [
        ("Surface Analysis Imports", test_surface_analysis_imports),
        ("process_line Signature", test_process_line_signature),
        ("Arc Decomposition", test_arc_decomposition),
        ("Context Enhancements", test_context_enhancements),
        ("Extrusion Enhancements", test_extrusion_enhancements),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        result = test_func()
        results.append((test_name, result))
    
    logger.info("\n" + "=" * 60)
    logger.info("Test Results Summary:")
    logger.info("=" * 60)
    
    passing = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passing}/{total} tests passed")
    
    return all(r for _, r in results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
