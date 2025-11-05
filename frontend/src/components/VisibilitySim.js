import React, { useState, useRef, useEffect } from 'react';
import './VisibilitySim.css';

function VisibilitySim() {
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const [apiResponse, setApiResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [floorplanData, setFloorplanData] = useState(null);
  const [geometries, setGeometries] = useState([]);

  // Initialize canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      // Set canvas size to match display size
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;

      drawInitialCanvas(ctx, canvas);
    }
  }, []);

  // Redraw canvas when floorplan data changes
  useEffect(() => {
    if (floorplanData && canvasRef.current) {
      drawFloorplan(floorplanData);
    }
  }, [floorplanData]);

  const drawInitialCanvas = (ctx, canvas) => {
    // Draw initial placeholder
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#cccccc';
    ctx.lineWidth = 2;
    ctx.strokeRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#666666';
    ctx.font = '20px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Floor Plan Canvas', canvas.width / 2, canvas.height / 2);
    ctx.fillText('Click Import to load an SVG file', canvas.width / 2, canvas.height / 2 + 30);
  };

  const drawFloorplan = (data) => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Clear canvas with white background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    const { geometries, viewbox } = data;
    
    // Calculate scale to fit canvas
    const scaleX = canvas.width / viewbox.width;
    const scaleY = canvas.height / viewbox.height;
    const scale = Math.min(scaleX, scaleY) * 0.9; // 90% to add padding
    
    // Calculate offset to center the drawing
    const offsetX = (canvas.width - viewbox.width * scale) / 2;
    const offsetY = (canvas.height - viewbox.height * scale) / 2;
    
    // Draw each geometry
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;
    ctx.fillStyle = 'none';
    
    geometries.forEach((geom) => {
      if (geom.points.length < 2) return;
      
      ctx.beginPath();
      
      // Move to first point
      const firstPoint = geom.points[0];
      ctx.moveTo(
        offsetX + firstPoint[0] * scale,
        offsetY + firstPoint[1] * scale
      );
      
      // Draw lines to subsequent points
      for (let i = 1; i < geom.points.length; i++) {
        const point = geom.points[i];
        ctx.lineTo(
          offsetX + point[0] * scale,
          offsetY + point[1] * scale
        );
      }
      
      // Close the path
      ctx.closePath();
      ctx.stroke();
    });
    
    // Draw info text
    ctx.fillStyle = '#333333';
    ctx.font = '14px Arial';
    ctx.textAlign = 'left';
    ctx.fillText(
      `Obstacles: ${geometries.length} | Canvas: ${viewbox.width.toFixed(0)}x${viewbox.height.toFixed(0)}`,
      10,
      canvas.height - 10
    );
  };

  // Handle import button click
  const handleImport = () => {
    fileInputRef.current.click();
  };

  // Handle file selection
  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    
    if (!file) {
      return;
    }

    // Validate file type
    if (!file.name.toLowerCase().endsWith('.svg')) {
      setApiResponse({
        status: 'error',
        message: 'Please select an SVG file'
      });
      return;
    }

    setLoading(true);
    setApiResponse(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:5001/api/import', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.status === 'success') {
        setApiResponse(data);
        setFloorplanData(data.data);
        setGeometries(data.data.geometries); // Store geometries array for later use
      } else {
        setApiResponse(data);
      }
    } catch (error) {
      setApiResponse({
        status: 'error',
        message: 'Failed to upload file: ' + error.message
      });
    } finally {
      setLoading(false);
      // Reset file input
      event.target.value = '';
    }
  };

  return (
    <div className="visibility-sim">
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept=".svg"
        style={{ display: 'none' }}
      />

      {/* Side Menu */}
      <div className="side-menu">
        <h2>Floor Plan Viewer</h2>
        
        <div className="menu-section">
          <h3>File Operations</h3>
          <button onClick={handleImport} disabled={loading}>
            {loading ? 'Processing...' : 'Import SVG'}
          </button>
          
          {floorplanData && (
            <div className="file-info">
              <p><strong>Obstacles:</strong> {floorplanData.obstacleCount}</p>
              <p><strong>Canvas Size:</strong> {floorplanData.viewbox.width.toFixed(0)} x {floorplanData.viewbox.height.toFixed(0)}</p>
            </div>
          )}
        </div>

        {/* Loading indicator */}
        {loading && (
          <div className="status-message loading">
            <div className="spinner"></div>
            Processing SVG file...
          </div>
        )}

        {/* API Response Display */}
        {apiResponse && (
          <div className={`api-response ${apiResponse.status}`}>
            <h4>Response:</h4>
            <div className="response-status">
              Status: <span className={apiResponse.status}>{apiResponse.status}</span>
            </div>
            <div className="response-message">
              {apiResponse.message}
            </div>
            {apiResponse.status === 'error' && (
              <p className="error-hint">Make sure you selected a valid SVG file.</p>
            )}
          </div>
        )}

        {/* Geometry Data Info */}
        {geometries.length > 0 && (
          <div className="menu-section">
            <h3>Geometry Data</h3>
            <p className="info-text">
              {geometries.length} obstacles loaded and ready for visibility calculations
            </p>
            <details>
              <summary>View Coordinates</summary>
              <div className="geometry-list">
                {geometries.slice(0, 3).map((geom, idx) => (
                  <div key={idx} className="geometry-item">
                    <strong>Obstacle {idx}:</strong> {geom.points.length} points
                  </div>
                ))}
                {geometries.length > 3 && (
                  <p>... and {geometries.length - 3} more</p>
                )}
              </div>
            </details>
          </div>
        )}
      </div>

      {/* Canvas Area */}
      <div className="canvas-container">
        <canvas ref={canvasRef}></canvas>
      </div>
    </div>
  );
}

export default VisibilitySim;