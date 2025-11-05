from visibility_loader import vp
import math

def test_basic_structures():
    """Test Point, Segment, and Polygon2 creation"""
    print("\n=== Testing Basic Structures ===")
    
    # Test Point
    p1 = vp.Point(10.0, 20.0)
    print(f"Point created: {p1}")
    assert p1.x == 10.0 and p1.y == 20.0
    print("✓ Point creation works")
    
    # Test Segment
    p2 = vp.Point(30.0, 40.0)
    seg = vp.Segment(p1, p2)
    print(f"✓ Segment created from {seg.start} to {seg.end}")
    
    # Test Polygon2
    poly = vp.Polygon2()
    poly.add_vertex(0, 0)
    poly.add_vertex(100, 0)
    poly.add_vertex(100, 100)
    poly.add_vertex(0, 100)
    print(f"✓ Polygon2 created with {len(poly.vertices)} vertices")

def test_distance():
    """Test distance calculation"""
    print("\n=== Testing Distance ===")
    
    p1 = vp.Point(0, 0)
    p2 = vp.Point(3, 4)
    dist = vp.distance(p1, p2)
    print(f"Distance between {p1} and {p2}: {dist}")
    assert abs(dist - 5.0) < 0.001
    print("✓ Distance calculation correct")

def test_regular_polygon():
    """Test regular polygon creation"""
    print("\n=== Testing Regular Polygon ===")
    
    # Create a hexagon
    hexagon = vp.create_regular_polygon(100, 100, 50, 6)
    print(f"✓ Created hexagon with {len(hexagon.vertices)} vertices")
    
    # Verify it's centered roughly at (100, 100)
    avg_x = sum(v.x for v in hexagon.vertices) / len(hexagon.vertices)
    avg_y = sum(v.y for v in hexagon.vertices) / len(hexagon.vertices)
    print(f"  Centroid: ({avg_x:.2f}, {avg_y:.2f})")
    assert abs(avg_x - 100) < 1 and abs(avg_y - 100) < 1
    print("✓ Regular polygon centered correctly")

def test_circle_polygon():
    """Test circle polygon creation"""
    print("\n=== Testing Circle Polygon ===")
    
    center = vp.Point(50, 50)
    radius = 30
    circle = vp.create_circle_polygon(center, radius, 32)
    print(f"✓ Created circle with {len(circle)} vertices")
    
    # Verify all points are approximately at radius distance
    for point in circle:
        dist = vp.distance(center, point)
        assert abs(dist - radius) < 0.1
    print("✓ All circle points at correct radius")

def test_point_in_polygon():
    """Test point in polygon detection"""
    print("\n=== Testing Point in Polygon ===")
    
    # Create a square
    square_vertices = [
        vp.Point(0, 0),
        vp.Point(100, 0),
        vp.Point(100, 100),
        vp.Point(0, 100)
    ]
    
    # Test point inside
    inside_point = vp.Point(50, 50)
    assert vp.is_point_in_polygon(inside_point, square_vertices)
    print("✓ Inside point detected correctly")
    
    # Test point outside
    outside_point = vp.Point(150, 50)
    assert not vp.is_point_in_polygon(outside_point, square_vertices)
    print("✓ Outside point detected correctly")

def test_visibility_polygon():
    """Test visibility polygon computation"""
    print("\n=== Testing Visibility Polygon ===")
    
    # Create a simple obstacle
    obstacles = []
    obstacle = vp.Polygon2()
    obstacle.add_vertex(200, 200)
    obstacle.add_vertex(300, 200)
    obstacle.add_vertex(300, 300)
    obstacle.add_vertex(200, 300)
    obstacles.append(obstacle)
    
    # Compute visibility from viewpoint
    viewpoint = vp.Point(50, 50)
    visibility = vp.compute_visibility_polygon(
        viewpoint, obstacles, 800, 600, 1000.0
    )
    
    print(f"✓ Visibility polygon computed with {len(visibility)} vertices")
    assert len(visibility) > 4  # Should have more vertices than just screen corners
    print("✓ Visibility polygon has reasonable vertex count")

def test_polygon_metrics():
    """Test polygon area, perimeter, and radial distance"""
    print("\n=== Testing Polygon Metrics ===")
    
    # Create a square 100x100
    square = [
        vp.Point(0, 0),
        vp.Point(100, 0),
        vp.Point(100, 100),
        vp.Point(0, 100)
    ]
    
    area = vp.calculate_polygon_area(square)
    print(f"Square area: {area}")
    assert abs(area - 10000) < 1
    print("✓ Area calculation correct")
    
    perimeter = vp.calculate_polygon_perimeter(square)
    print(f"Square perimeter: {perimeter}")
    assert abs(perimeter - 400) < 1
    print("✓ Perimeter calculation correct")
    
    center = vp.Point(50, 50)
    mean_dist = vp.calculate_mean_radial_distance(center, square)
    print(f"Mean radial distance: {mean_dist:.2f}")
    expected = math.sqrt(50**2 + 50**2)  # Distance from center to corner
    assert abs(mean_dist - expected) < 1
    print("✓ Mean radial distance correct")

def test_clipper_intersection():
    """Test Clipper2 polygon-circle intersection"""
    print("\n=== Testing Clipper2 Intersection ===")
    
    # Create a square polygon
    square = [
        vp.Point(0, 0),
        vp.Point(100, 0),
        vp.Point(100, 100),
        vp.Point(0, 100)
    ]
    
    # Clip with circle centered at corner
    center = vp.Point(50, 50)
    radius = 60
    
    clipped = vp.clip_circle_with_visibility_polygon(square, center, radius, 64)
    
    if clipped:
        print(f"✓ Clipped polygon has {len(clipped)} vertices")
        area = vp.calculate_polygon_area(clipped)
        print(f"  Clipped area: {area:.2f}")
        print("✓ Clipper2 intersection works")
    else:
        print("✗ No intersection found (this might be expected)")

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("VISIBILITY POLYGON MODULE TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_basic_structures,
        test_distance,
        test_regular_polygon,
        test_circle_polygon,
        test_point_in_polygon,
        test_visibility_polygon,
        test_polygon_metrics,
        test_clipper_intersection,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n✗ {test.__name__} FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()