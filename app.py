from flask import Flask, jsonify, send_from_directory, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import tempfile
from SVGFloorplanProcessor import SVGFloorplanProcessor
from visibility_module import get_visibility_module

app = Flask(__name__, static_folder='frontend/build', static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
CORS(app)

VIS_MODULE = get_visibility_module()

# Allowed file extensions
ALLOWED_EXTENSIONS = {'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/import', methods=['POST'])
def import_floorplan():
    """
    Import and process SVG floorplan file
    Returns cleaned geometry data for canvas rendering
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'message': 'Invalid file type. Only .svg files are allowed'
            }), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_input_path = os.path.join(app.config['UPLOAD_FOLDER'], f'input_{filename}')
        file.save(temp_input_path)
        
        # Process the SVG
        processor = SVGFloorplanProcessor()
        processor.import_svg(temp_input_path)
        processor.clean_svg()
        
        # Extract geometry data
        geometries = []
        for geom in processor.geometries:
            geometries.append({
                'points': geom['points'],
                'group': geom['parent_group']
            })
        
        # Get viewbox info
        viewbox = processor.viewbox
        
        # Clean up temp file
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully processed {len(geometries)} obstacles',
            'data': {
                'geometries': geometries,
                'viewbox': viewbox,
                'obstacleCount': len(geometries)
            }
        })
    
    except Exception as e:
        # Clean up temp file on error
        if 'temp_input_path' in locals() and os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        
        return jsonify({
            'status': 'error',
            'message': f'Error processing file: {str(e)}'
        }), 500

@app.route('/api/visibility-polygon', methods=['POST', 'OPTIONS'])
def compute_visibility_polygon():
    """
    Compute visibility polygon from a point of view
    Expects JSON with:
    - viewpoint: {x, y}
    - obstacles: array of geometry objects with points
    - canvasWidth: number
    - canvasHeight: number
    """
    global VIS_MODULE
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        # Validate input
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        viewpoint = data.get('viewpoint')
        obstacles = data.get('obstacles', [])
        canvas_width = data.get('canvasWidth', 1000)
        canvas_height = data.get('canvasHeight', 800)
        
        if not viewpoint or 'x' not in viewpoint or 'y' not in viewpoint:
            return jsonify({
                'status': 'error',
                'message': 'Invalid viewpoint data'
            }), 400
        
        # Convert obstacles to the format expected by C++ module
        obstacle_polygons = []
        for obstacle in obstacles:
            points = obstacle.get('points', [])
            if len(points) >= 3:  # Valid polygon needs at least 3 points
                obstacle_polygons.append(points)
        
        # Get visibility module and compute
        visibility_points = VIS_MODULE.compute_visibility_polygon(
            viewpoint=(viewpoint['x'], viewpoint['y']),
            obstacles=obstacle_polygons,
            screen_width=int(canvas_width),
            screen_height=int(canvas_height),
            ray_length=3000.0
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'visibilityPolygon': visibility_points,
                'viewpoint': viewpoint,
                'obstacleCount': len(obstacle_polygons)
            }
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error computing visibility polygon: {error_details}")
        
        return jsonify({
            'status': 'error',
            'message': f'Error computing visibility polygon: {str(e)}'
        }), 500

@app.route('/api/get-clipping-circles', methods=['POST', 'OPTIONS'])
def get_clipping_circles():
    """
    Get clipping circles for obstacles from a point of view
    Expects JSON with:
    - viewpoint: {x, y}
    - obstacles: array of geometry objects with points
    - canvasWidth: number
    - canvasHeight: number
    """
    global VIS_MODULE
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        # Validate input
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        viewpoint = data.get('viewpoint')
        obstacles = data.get('obstacles', [])
        canvas_width = data.get('canvasWidth', 1000)
        canvas_height = data.get('canvasHeight', 800)
        
        if not viewpoint or 'x' not in viewpoint or 'y' not in viewpoint:
            return jsonify({
                'status': 'error',
                'message': 'Invalid viewpoint data'
            }), 400
        
        # Convert obstacles to the format expected by C++ module
        obstacle_polygons = []
        for obstacle in obstacles:
            points = obstacle.get('points', [])
            if len(points) >= 3:  # Valid polygon needs at least 3 points
                obstacle_polygons.append(points)
        
        # Get visibility module and compute clipping circles
        clipping_circles = VIS_MODULE.get_clipping_circles(
            viewpoint=(viewpoint['x'], viewpoint['y']),
            obstacles=obstacle_polygons,
            screen_width=int(canvas_width),
            screen_height=int(canvas_height)
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'clippingCircles': clipping_circles,
                'viewpoint': viewpoint,
                'obstacleCount': len(obstacle_polygons)
            }
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error getting clipping circles: {error_details}")
        
        return jsonify({
            'status': 'error',
            'message': f'Error getting clipping circles: {str(e)}'
        }), 500

@app.route('/api/allocentric-visibility', methods=['POST', 'OPTIONS'])
def compute_allocentric_visibility():
    """
    Compute allocentric visibility polygon from a feature's center,
    excluding its containing obstacle, with optional circle clipping
    """
    global VIS_MODULE
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        feature_center = data.get('featureCenter')
        obstacles = data.get('obstacles', [])
        canvas_width = data.get('canvasWidth', 1000)
        canvas_height = data.get('canvasHeight', 800)
        ray_length = data.get('rayLength', 3000.0)
        sensitivity1 = data.get('sensitivity1', 0.5)
        sensitivity2 = data.get('sensitivity2', 0.3)
        show_sensitivity = data.get('showSensitivity', False)
        exclude_obstacle_index = data.get('excludeObstacleIndex')
        
        # Constants from openFrameworks code
        VISIBILITY_VALUE_MULTIPLIER = 200.0
        DETAIL_VISIBILITY_MULTIPLIER = 100.0
        SQUARE_VISIBILITY_SCALE = 5.0
        
        if not feature_center or 'x' not in feature_center or 'y' not in feature_center:
            return jsonify({'status': 'error', 'message': 'Invalid feature center'}), 400
        
        if exclude_obstacle_index is None:
            return jsonify({'status': 'error', 'message': 'No obstacle index provided'}), 400
        
        # Convert obstacles to polygon format
        obstacle_polygons = []
        for obstacle in obstacles:
            points = obstacle.get('points', [])
            if len(points) >= 3:
                obstacle_polygons.append(points)
        
        # Create modified obstacles list (excluding the specified obstacle)
        modified_obstacles = [
            obstacle_polygons[i] for i in range(len(obstacle_polygons))
            if i != exclude_obstacle_index
        ]
        
        print(f"Computing with {len(modified_obstacles)} obstacles (excluded {exclude_obstacle_index})")
        
        # Create Point for viewpoint
        pov = VIS_MODULE.module.Point(float(feature_center['x']), float(feature_center['y']))
        
        # Create obstacle polygons
        obstacle_list = []
        for obstacle_points in modified_obstacles:
            poly = VIS_MODULE.module.Polygon2()
            for point in obstacle_points:
                x, y = float(point[0]), float(point[1])
                poly.add_vertex(x, y)
            obstacle_list.append(poly)
        
        # Compute visibility polygon - KEEP AS Point OBJECTS
        visibility_polygon_points = VIS_MODULE.module.compute_visibility_polygon(
            pov,
            obstacle_list,
            int(canvas_width),
            int(canvas_height),
            float(ray_length)
        )
        
        # Convert to tuples for JSON response
        visibility_points = [(p.x, p.y) for p in visibility_polygon_points]
        
        response_data = {
            'allocentricPolygon': visibility_points,
            'featureCenter': feature_center,
            'excludedObstacleIndex': exclude_obstacle_index
        }
        
        # If sensitivity mode is enabled, clip with circles
        if show_sensitivity:
            radius1 = sensitivity1 * VISIBILITY_VALUE_MULTIPLIER * SQUARE_VISIBILITY_SCALE
            radius2 = sensitivity2 * DETAIL_VISIBILITY_MULTIPLIER * SQUARE_VISIBILITY_SCALE
            
            print(f"Clipping - Radius1: {radius1:.1f}, Radius2: {radius2:.1f}")
            
            # Pass Point objects (not tuples!) to clipping function
            clipped1 = VIS_MODULE.module.clip_circle_with_visibility_polygon(
                visibility_polygon_points,  # Point objects
                pov,                        # Point object
                float(radius1),
                128
            )
            
            clipped2 = VIS_MODULE.module.clip_circle_with_visibility_polygon(
                visibility_polygon_points,  # Point objects
                pov,                        # Point object
                float(radius2),
                128
            )
            
            # Convert clipped results to tuples
            clipped1_points = [(p.x, p.y) for p in clipped1]
            clipped2_points = [(p.x, p.y) for p in clipped2]
            
            print(f"✓ Clipped1: {len(clipped1_points)} points, Clipped2: {len(clipped2_points)} points")
            
            response_data['clippedPolygon1'] = clipped1_points
            response_data['clippedPolygon2'] = clipped2_points
            response_data['radius1'] = radius1
            response_data['radius2'] = radius2
        
        return jsonify({'status': 'success', 'data': response_data})
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error: {error_details}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@app.route('/api/visibility-heatmap', methods=['POST', 'OPTIONS'])
def compute_visibility_heatmap():
    """
    Compute visibility heatmap from all obstacle centers
    Expects JSON with:
    - obstacles: array of geometry objects with points
    - canvasWidth: number
    - canvasHeight: number
    - gridResolution: number (grid square size in pixels)
    - rayLength: number
    """
    global VIS_MODULE
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        obstacles = data.get('obstacles', [])
        canvas_width = data.get('canvasWidth', 1000)
        canvas_height = data.get('canvasHeight', 800)
        grid_resolution = data.get('gridResolution', 10)
        ray_length = data.get('rayLength', 3000.0)
        
        if len(obstacles) < 2:  # Need boundary + at least one object
            return jsonify({
                'status': 'error',
                'message': 'Need at least 2 obstacles (boundary + objects)'
            }), 400
        
        # Convert obstacles to polygon format
        obstacle_polygons = []
        for obstacle in obstacles:
            points = obstacle.get('points', [])
            if len(points) >= 3:
                obstacle_polygons.append(points)
        
        # Calculate object centers (excluding boundary at index 0)
        object_centers = []
        object_indices = []
        
        for i in range(1, len(obstacle_polygons)):  # Skip boundary
            points = obstacle_polygons[i]
            center_x = sum(p[0] for p in points) / len(points)
            center_y = sum(p[1] for p in points) / len(points)
            object_centers.append((center_x, center_y))
            object_indices.append(i)
        
        print(f"Computing heatmap from {len(object_centers)} object centers")
        
        # Create grid
        square_size = float(grid_resolution)
        num_squares_x = int(canvas_width / square_size)
        num_squares_y = int(canvas_height / square_size)
        
        # Initialize grid scores
        grid_scores = [[0 for _ in range(num_squares_x)] for _ in range(num_squares_y)]
        
        # For each object center, compute visibility
        for center_idx, (center_x, center_y) in enumerate(object_centers):
            obstacle_idx = object_indices[center_idx]
            
            # Create modified obstacles list excluding current object
            modified_obstacles = [
                obstacle_polygons[i] for i in range(len(obstacle_polygons))
                if i != obstacle_idx
            ]
            
            # Compute visibility polygon from this center
            pov = VIS_MODULE.module.Point(float(center_x), float(center_y))
            
            obstacle_list = []
            for obstacle_points in modified_obstacles:
                poly = VIS_MODULE.module.Polygon2()
                for point in obstacle_points:
                    x, y = float(point[0]), float(point[1])
                    poly.add_vertex(x, y)
                obstacle_list.append(poly)
            
            visibility_polygon = VIS_MODULE.module.compute_visibility_polygon(
                pov,
                obstacle_list,
                int(canvas_width),
                int(canvas_height),
                float(ray_length)
            )
            
            visibility_points = [(p.x, p.y) for p in visibility_polygon]
            
            # Check each grid point
            for gy in range(num_squares_y):
                for gx in range(num_squares_x):
                    # Calculate grid center
                    center_x_grid = (gx * square_size) + (square_size / 2.0)
                    center_y_grid = (gy * square_size) + (square_size / 2.0)
                    
                    # Check if inside visibility polygon
                    if is_point_in_polygon((center_x_grid, center_y_grid), visibility_points):
                        grid_scores[gy][gx] += 1
            
            if (center_idx + 1) % 10 == 0:
                print(f"Processed {center_idx + 1}/{len(object_centers)} object centers")
        
        # Find max score for normalization
        max_score = max(max(row) for row in grid_scores)
        
        # Create colored pixels
        heatmap_pixels = []
        for gy in range(num_squares_y):
            for gx in range(num_squares_x):
                score = grid_scores[gy][gx]
                
                if score > 0:
                    # Calculate grid square bounds
                    start_x = gx * square_size
                    start_y = gy * square_size
                    end_x = start_x + square_size
                    end_y = start_y + square_size
                    
                    # Normalize and get color
                    normalized = score / max_score if max_score > 0 else 0
                    color = get_heatmap_color(normalized)
                    
                    heatmap_pixels.append({
                        'points': [
                            [start_x, start_y],
                            [end_x, start_y],
                            [end_x, end_y],
                            [start_x, end_y]
                        ],
                        'score': score,
                        'normalized': normalized,
                        'color': color
                    })
        
        print(f"✓ Computed heatmap: {len(heatmap_pixels)} colored pixels, max score: {max_score}")
        
        return jsonify({
            'status': 'success',
            'data': {
                'pixels': heatmap_pixels,
                'maxScore': max_score,
                'gridResolution': grid_resolution,
                'objectCenterCount': len(object_centers)
            }
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error computing visibility heatmap: {error_details}")
        
        return jsonify({
            'status': 'error',
            'message': f'Error computing heatmap: {str(e)}'
        }), 500

def is_point_in_polygon(point, vertices):
    """Check if point is inside polygon using ray casting"""
    x, y = point
    inside = False
    j = len(vertices) - 1
    
    for i in range(len(vertices)):
        xi, yi = vertices[i]
        xj, yj = vertices[j]
        
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    
    return inside

def get_heatmap_color(normalized_value):
    """
    Convert normalized value (0-1) to heatmap color
    Blue (low) -> Cyan -> Green -> Yellow -> Red (high)
    Returns rgba string
    """
    if normalized_value <= 0.0:
        return 'rgba(0, 0, 0, 0)'
    elif normalized_value <= 0.25:
        t = normalized_value / 0.25
        return f'rgba(0, {int(t * 128)}, 255, 150)'
    elif normalized_value <= 0.5:
        t = (normalized_value - 0.25) / 0.25
        return f'rgba(0, {128 + int(t * 127)}, {255 - int(t * 255)}, 150)'
    elif normalized_value <= 0.75:
        t = (normalized_value - 0.5) / 0.25
        return f'rgba({int(t * 255)}, 255, 0, 150)'
    else:
        t = (normalized_value - 0.75) / 0.25
        return f'rgba(255, {255 - int(t * 255)}, 0, 150)'
        
@app.route('/api/greeting', methods=['GET'])
def get_greeting():
    return jsonify({
        'message': 'Hello from Flask!',
        'timestamp': '2025-10-19',
        'status': 'success'
    })

@app.route('/api/echo', methods=['POST'])
def echo_message():
    data = request.get_json()
    user_message = data.get('message', '')
    return jsonify({
        'echo': f"You said: {user_message}",
        'length': len(user_message),
        'status': 'success'
    })

@app.route('/health', methods=['GET'])
def health():
    """Check if module loaded correctly"""
    try:
        vis_module = VIS_MODULE
        module_loaded = True
    except Exception as e:
        module_loaded = False
        print(f"Visibility module error: {e}")
    
    return jsonify({
        'status': 'ok',
        'module_loaded': module_loaded
    })

@app.errorhandler(404)
def not_found(e):
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)