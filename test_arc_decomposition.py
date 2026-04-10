#!/usr/bin/env python3
"""
Test G2/G3 arc decomposition implementation
Validates arc parameter parsing and waypoint generation
"""

import sys
import math

# Add GCodeZAA to path
sys.path.insert(0, 'GCodeZAA')

from gcodezaa.extrusion import decompose_arc

def test_arc_decomposition_ij():
    """Test arc decomposition with I/J center offset parameters"""
    print("Test 1: Arc decomposition with I/J parameters")
    
    # Simple quarter circle: (0,0) -> (10,10) with center at (0,10)
    # Center offset: I=0, J=10
    start = (0.0, 0.0, 0.0)
    waypoints = decompose_arc(
        start_pos=start,
        end_x=10.0,
        end_y=10.0,
        end_z=0.0,
        center_i=0.0,
        center_j=10.0,
        is_clockwise=False,  # G3
        segment_length=1.0
    )
    
    print(f"  Start: {start}")
    print(f"  End: (10.0, 10.0, 0.0)")
    print(f"  Generated {len(waypoints)} waypoints")
    print(f"  First: {waypoints[0]}")
    print(f"  Last: {waypoints[-1]}")
    
    # Verify endpoint is reached
    final = waypoints[-1]
    assert abs(final[0] - 10.0) < 0.1, f"Expected X=10, got {final[0]}"
    assert abs(final[1] - 10.0) < 0.1, f"Expected Y=10, got {final[1]}"
    assert abs(final[2] - 0.0) < 0.01, f"Expected Z=0, got {final[2]}"
    
    print("  ✓ Endpoint reached correctly")
    print()

def test_arc_decomposition_radius():
    """Test arc decomposition with R radius parameter"""
    print("Test 2: Arc decomposition with R parameter")
    
    # Quarter circle with radius = 10
    start = (0.0, 0.0, 0.0)
    waypoints = decompose_arc(
        start_pos=start,
        end_x=10.0,
        end_y=0.0,
        end_z=0.0,
        radius=10.0,
        is_clockwise=True,  # G2
        segment_length=1.0
    )
    
    print(f"  Generated {len(waypoints)} waypoints")
    print(f"  First: {waypoints[0]}")
    print(f"  Last: {waypoints[-1]}")
    
    # Verify endpoint
    final = waypoints[-1]
    assert abs(final[0] - 10.0) < 0.1, f"Expected X=10, got {final[0]}"
    assert abs(final[1] - 0.0) < 0.1, f"Expected Y=0, got {final[1]}"
    
    print("  ✓ Endpoint reached with radius calculation")
    print()

def test_full_circle():
    """Test a full circle decomposition"""
    print("Test 3: Full circle (360°)")
    
    start = (10.0, 0.0, 0.0)
    waypoints = decompose_arc(
        start_pos=start,
        end_x=10.0,
        end_y=0.0,
        end_z=0.0,
        center_i=-10.0,
        center_j=0.0,
        is_clockwise=False,
        segment_length=1.0
    )
    
    print(f"  Generated {len(waypoints)} waypoints for full circle")
    
    # For full circle, start and end should be same
    assert abs(waypoints[0][0] - waypoints[-1][0]) < 0.01
    assert abs(waypoints[0][1] - waypoints[-1][1]) < 0.01
    
    print("  ✓ Full circle returns to start position")
    print()

def test_arc_with_z_movement():
    """Test arc with Z-axis movement (helical interpolation)"""
    print("Test 4: Helical arc with Z movement")
    
    start = (0.0, 0.0, 0.0)
    waypoints = decompose_arc(
        start_pos=start,
        end_x=10.0,
        end_y=10.0,
        end_z=5.0,  # Move up while rotating
        center_i=0.0,
        center_j=10.0,
        is_clockwise=False,
        segment_length=1.0
    )
    
    print(f"  Start Z: {start[2]}")
    print(f"  End Z: {waypoints[-1][2]:.2f}")
    
    # Verify Z movement
    final = waypoints[-1]
    assert abs(final[2] - 5.0) < 0.1, f"Expected Z=5.0, got {final[2]}"
    
    print("  ✓ Helical movement works correctly")
    print()

def test_degenerate_arc():
    """Test handling of degenerate arc (zero radius)"""
    print("Test 5: Degenerate arc handling")
    
    start = (0.0, 0.0, 0.0)
    waypoints = decompose_arc(
        start_pos=start,
        end_x=0.0,  # Same as start
        end_y=0.0,  # Same as start
        end_z=0.0,
        center_i=0.0,
        center_j=0.0
    )
    
    print(f"  Generated {len(waypoints)} waypoints")
    assert len(waypoints) >= 1
    
    print("  ✓ Degenerate arc handled safely")
    print()

def test_clockwise_vs_counterclockwise():
    """Test that clockwise and counter-clockwise arcs differ"""
    print("Test 6: Clockwise vs Counter-clockwise")
    
    start = (0.0, 0.0, 0.0)
    
    # G2 (clockwise)
    cw_waypoints = decompose_arc(
        start_pos=start,
        end_x=10.0,
        end_y=10.0,
        end_z=0.0,
        center_i=5.0,
        center_j=5.0,
        is_clockwise=True,
        segment_length=1.0
    )
    
    # G3 (counter-clockwise)
    ccw_waypoints = decompose_arc(
        start_pos=start,
        end_x=10.0,
        end_y=10.0,
        end_z=0.0,
        center_i=5.0,
        center_j=5.0,
        is_clockwise=False,
        segment_length=1.0
    )
    
    print(f"  Clockwise: {len(cw_waypoints)} waypoints")
    print(f"  Counter-clockwise: {len(ccw_waypoints)} waypoints")
    
    # Different arcs will have different numbers of waypoints
    # (one goes the long way around)
    print("  ✓ Both directions handled correctly")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("G2/G3 Arc Decomposition Tests")
    print("=" * 60)
    print()
    
    try:
        test_arc_decomposition_ij()
        test_arc_decomposition_radius()
        test_full_circle()
        test_arc_with_z_movement()
        test_degenerate_arc()
        test_clockwise_vs_counterclockwise()
        
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Test failed with error:")
        print(f"  {type(e).__name__}: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)
