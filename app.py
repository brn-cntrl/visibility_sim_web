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
        vis_module = get_visibility_module()
        visibility_points = vis_module.compute_visibility_polygon(
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
        vis_module = get_visibility_module()
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