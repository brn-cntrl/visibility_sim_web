import React, { useState, useRef, useEffect, useCallback } from 'react';
import './VisibilitySim.css';

function VisibilitySim() {
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const [apiResponse, setApiResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [floorplanData, setFloorplanData] = useState(null);
  const [geometries, setGeometries] = useState([]);
  
  // New state for visibility polygon
  const [pointOfView, setPointOfView] = useState(null);
  const [visibilityPolygon, setVisibilityPolygon] = useState(null);
  const [showVisibilityPolygon, setShowVisibilityPolygon] = useState(true);
  const [computingVisibility, setComputingVisibility] = useState(false);
  
  // Store canvas transform parameters for coordinate conversion
  const [canvasTransform, setCanvasTransform] = useState({
    scale: 1,
    offsetX: 0,
    offsetY: 0
  });

  const [features, setFeatures] = useState({});  // Map: obstacleIndex -> featureData
  const [selectedObstacleIndex, setSelectedObstacleIndex] = useState(null);

  // Collapsible menu sections state
  const [expandedSections, setExpandedSections] = useState({
    fileOperations: true,
    visibilityControls: true,
    selectedObstacle: true,
    geometryData: false
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };
  
  // Initialize canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
      drawInitialCanvas(ctx, canvas);
    }
  }, []);

  const getClickedObstacleIndex = (canvasX, canvasY) => {
    if (!floorplanData || !geometries) return null;
    
    const { scale, offsetX, offsetY } = canvasTransform;
    const viewboxX = (canvasX - offsetX) / scale;
    const viewboxY = (canvasY - offsetY) / scale;
    
    for (let i = geometries.length - 1; i >= 1; i--) {
      const obstacle = geometries[i];
      if (isPointInPolygon({ x: viewboxX, y: viewboxY }, obstacle.points)) {
        return i;
      }
    }
    
    return null;
  };

  const isPointInPolygon = (point, vertices) => {
    let inside = false;
    for (let i = 0, j = vertices.length - 1; i < vertices.length; j = i++) {
      const xi = vertices[i][0], yi = vertices[i][1];
      const xj = vertices[j][0], yj = vertices[j][1];
      
      const intersect = ((yi > point.y) !== (yj > point.y))
          && (point.x < (xj - xi) * (point.y - yi) / (yj - yi) + xi);
      if (intersect) inside = !inside;
    }
    return inside;
  };

  const drawFloorplan = useCallback((data) => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Clear canvas with white background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    const { geometries, viewbox } = data;
    
    // Calculate scale to fit canvas
    const scaleX = canvas.width / viewbox.width;
    const scaleY = canvas.height / viewbox.height;
    const scale = Math.min(scaleX, scaleY) * 0.9;
    
    // Calculate offset to center the drawing
    const offsetX = (canvas.width - viewbox.width * scale) / 2;
    const offsetY = (canvas.height - viewbox.height * scale) / 2;
    
    // Store transform for coordinate conversion
    setCanvasTransform({ scale, offsetX, offsetY });
    
    // Draw visibility polygon first (if exists and visible)
    if (showVisibilityPolygon && visibilityPolygon && visibilityPolygon.length > 0) {
      ctx.fillStyle = 'rgba(80, 140, 200, 0.85)';
      ctx.strokeStyle = 'rgba(80, 140, 200, 1.0)';
      ctx.lineWidth = 3;
      
      ctx.beginPath();
      const firstPoint = visibilityPolygon[0];
      ctx.moveTo(firstPoint[0], firstPoint[1]);
      
      for (let i = 1; i < visibilityPolygon.length; i++) {
        const point = visibilityPolygon[i];
        ctx.lineTo(point[0], point[1]);
      }
      
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }
    
    geometries.forEach((geom, index) => {
      if (geom.points.length < 2) return;
      
      const isSelected = index === selectedObstacleIndex && index !== 0;
      const hasFeature = features[index] !== undefined;
      
      ctx.beginPath();
      const firstPoint = geom.points[0];
      ctx.moveTo(
        offsetX + firstPoint[0] * scale,
        offsetY + firstPoint[1] * scale
      );
      
      for (let i = 1; i < geom.points.length; i++) {
        const point = geom.points[i];
        ctx.lineTo(
          offsetX + point[0] * scale,
          offsetY + point[1] * scale
        );
      }
      
      ctx.closePath();
      
      // Stroke styling based on state
      if (isSelected) {
        ctx.strokeStyle = '#FFA500'; // Orange highlight
        ctx.lineWidth = 4;
      } else if (hasFeature) {
        ctx.strokeStyle = '#FF6B6B'; // Red outline for features
        ctx.lineWidth = 2.5;
      } else {
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 2;
      }
      ctx.stroke();
    });

    // Draw features as circles
    Object.values(features).forEach(feature => {      
      // Recalculate position based on viewbox coordinates
      const canvasX = offsetX + feature.viewboxPosition.x * scale;
      const canvasY = offsetY + feature.viewboxPosition.y * scale;
      
      // Outer circle (white)
      ctx.fillStyle = '#ffffff';
      ctx.strokeStyle = '#333333';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(canvasX, canvasY, feature.size, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
      
      // Inner circle (color coded)
      ctx.fillStyle = '#FF6B6B';
      ctx.beginPath();
      ctx.arc(canvasX, canvasY, feature.size * 0.6, 0, 2 * Math.PI);
      ctx.fill();
    });

    // Draw point of view (if exists)
    if (pointOfView) {
      // Draw outer circle (white outline)
      ctx.fillStyle = '#ffffff';
      ctx.strokeStyle = '#333333';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(pointOfView.x, pointOfView.y, 8, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
      
      // Draw inner circle (blue)
      ctx.fillStyle = '#3498db';
      ctx.beginPath();
      ctx.arc(pointOfView.x, pointOfView.y, 5, 0, 2 * Math.PI);
      ctx.fill();
    }
    
    // Draw info text
    ctx.fillStyle = '#333333';
    ctx.font = '14px Arial';
    ctx.textAlign = 'left';
    let infoText = `Obstacles: ${geometries.length} | Canvas: ${viewbox.width.toFixed(0)}x${viewbox.height.toFixed(0)}`;
    if (pointOfView) {
      infoText += ` | POV: (${Math.round(pointOfView.canvasX)}, ${Math.round(pointOfView.canvasY)})`;
    }
    ctx.fillText(infoText, 10, canvas.height - 10);
  }, [pointOfView, visibilityPolygon, showVisibilityPolygon, features, selectedObstacleIndex]);
  // Redraw canvas when any visualization data changes
  useEffect(() => {
    if (floorplanData && canvasRef.current) {
      drawFloorplan(floorplanData);
    }
  }, [floorplanData, pointOfView, visibilityPolygon, showVisibilityPolygon, drawFloorplan]);

  const drawInitialCanvas = (ctx, canvas) => {
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

  const handleImport = () => {
    fileInputRef.current.click();
  };

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    
    if (!file) {
      return;
    }

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
        setGeometries(data.data.geometries);
        // Reset POV and visibility when loading new floorplan
        setPointOfView(null);
        setVisibilityPolygon(null);
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
      event.target.value = '';
    }
  };

  const handleCanvasRightClick = async (event) => {
    event.preventDefault(); // Prevent context menu
    
    if (!floorplanData) {
      return; // No floorplan loaded
    }
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    
    // Get click position relative to canvas
    const canvasX = event.clientX - rect.left;
    const canvasY = event.clientY - rect.top;
    
    // Convert canvas coordinates to viewbox coordinates
    const { scale, offsetX, offsetY } = canvasTransform;
    const viewboxX = (canvasX - offsetX) / scale;
    const viewboxY = (canvasY - offsetY) / scale;
    
    // Set point of view
    const newPOV = {
      x: canvasX,
      y: canvasY,
      canvasX: canvasX,
      canvasY: canvasY,
      viewboxX: viewboxX,
      viewboxY: viewboxY
    };
    
    setPointOfView(newPOV);
    
    // Compute visibility polygon
    await computeVisibilityPolygon(newPOV);
  };

  const handleCanvasLeftClick = (event) => {
    if (!floorplanData) return;
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    
    const canvasX = event.clientX - rect.left;
    const canvasY = event.clientY - rect.top;
    
    const clickedIndex = getClickedObstacleIndex(canvasX, canvasY);
    setSelectedObstacleIndex(clickedIndex);
  };

  const computeVisibilityPolygon = async (pov) => {
    setComputingVisibility(true);
    
    try {
      // Prepare obstacles in viewbox coordinates
      const obstaclesData = geometries.map(geom => ({
        points: geom.points
      }));
      
      const response = await fetch('http://localhost:5001/api/visibility-polygon', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          viewpoint: {
            x: pov.viewboxX,
            y: pov.viewboxY
          },
          obstacles: obstaclesData,
          canvasWidth: floorplanData.viewbox.width,
          canvasHeight: floorplanData.viewbox.height
        }),
      });

      const data = await response.json();

      if (data.status === 'success') {
        // Convert visibility polygon points from viewbox to canvas coordinates
        const { scale, offsetX, offsetY } = canvasTransform;
        const canvasPolygon = data.data.visibilityPolygon.map(point => [
          offsetX + point[0] * scale,
          offsetY + point[1] * scale
        ]);
        
        setVisibilityPolygon(canvasPolygon);
      } else {
        console.error('Failed to compute visibility polygon:', data.message);
        setApiResponse({
          status: 'error',
          message: 'Failed to compute visibility: ' + data.message
        });
      }
    } catch (error) {
      console.error('Error computing visibility polygon:', error);
      setApiResponse({
        status: 'error',
        message: 'Error computing visibility: ' + error.message
      });
    } finally {
      setComputingVisibility(false);
    }
  };

  const handleToggleVisibility = () => {
    setShowVisibilityPolygon(!showVisibilityPolygon);
  };

  const handleClearPOV = () => {
    setPointOfView(null);
    setVisibilityPolygon(null);
  };

  const handleAssignFeature = () => {
    if (selectedObstacleIndex === null) return;
    
    // Calculate obstacle center in canvas coordinates
    const obstacle = geometries[selectedObstacleIndex];
    const { scale, offsetX, offsetY } = canvasTransform;
    
    // Calculate center in viewbox coordinates
    const points = obstacle.points;
    let centerX = 0, centerY = 0;
    
    // Check if first and last points are the same (closed polygon)
    let pointsToAverage = points.length;
    const firstPoint = points[0];
    const lastPoint = points[points.length - 1];
    if (Math.abs(firstPoint[0] - lastPoint[0]) < 0.01 && 
        Math.abs(firstPoint[1] - lastPoint[1]) < 0.01) {
      pointsToAverage = points.length - 1; // Exclude duplicate closing point
    }
    
    for (let i = 0; i < pointsToAverage; i++) {
      centerX += points[i][0];
      centerY += points[i][1];
    }
    centerX /= pointsToAverage;
    centerY /= pointsToAverage;
    
    // Convert to canvas coordinates
    const canvasCenterX = offsetX + centerX * scale;
    const canvasCenterY = offsetY + centerY * scale;
    
    // Create feature with default values (matching C++ struct)
    const newFeature = {
      obstacleIndex: selectedObstacleIndex,
      position: { x: canvasCenterX, y: canvasCenterY },
      viewboxPosition: { x: centerX, y: centerY },
      size: 10, // Default radius in pixels
      visibilityValue: 0.5,
      detailVisibilityValue: 0.5,
      feature1Contrast: 0.5,
      feature1SpatialFreq: 100.0,
      feature2Contrast: 0.3,
      feature2SpatialFreq: 200.0
    };
    
    setFeatures(prev => ({
      ...prev,
      [selectedObstacleIndex]: newFeature
    }));
  };

  const handleRemoveFeature = () => {
    if (selectedObstacleIndex === null) return;
    
    setFeatures(prev => {
      const updated = { ...prev };
      delete updated[selectedObstacleIndex];
      return updated;
    });
  };

  const handleUpdateFeature = (property, value) => {
    if (selectedObstacleIndex === null || !features[selectedObstacleIndex]) return;
    
    setFeatures(prev => ({
      ...prev,
      [selectedObstacleIndex]: {
        ...prev[selectedObstacleIndex],
        [property]: value
      }
    }));
  };

  return (
    <div className="visibility-sim">
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
          <h3 onClick={() => toggleSection('fileOperations')} className="collapsible-header">
            <span className={`arrow ${expandedSections.fileOperations ? 'expanded' : ''}`}>▶</span>
            File Operations
          </h3>
          {expandedSections.fileOperations && (
            <>
              <button onClick={handleImport} disabled={loading}>
                {loading ? 'Processing...' : 'Import SVG'}
              </button>
              
              {floorplanData && (
                <div className="file-info">
                  <p><strong>Obstacles:</strong> {floorplanData.obstacleCount}</p>
                  <p><strong>Canvas Size:</strong> {floorplanData.viewbox.width.toFixed(0)} x {floorplanData.viewbox.height.toFixed(0)}</p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Visibility Controls */}
        {floorplanData && (
          <div className="menu-section">
            <h3 onClick={() => toggleSection('visibilityControls')} className="collapsible-header">
              <span className={`arrow ${expandedSections.visibilityControls ? 'expanded' : ''}`}>▶</span>
              Visibility Controls
            </h3>
            {expandedSections.visibilityControls && (
              <>
                <div className="control-info">
                  <p className="instruction">
                    <strong>Right-click</strong> on canvas to place point of view
                  </p>
                </div>
                
                {pointOfView && (
                  <>
                    <div className="pov-info">
                      <p><strong>Point of View:</strong></p>
                      <p>Canvas: ({Math.round(pointOfView.canvasX)}, {Math.round(pointOfView.canvasY)})</p>
                      <p>Viewbox: ({pointOfView.viewboxX.toFixed(1)}, {pointOfView.viewboxY.toFixed(1)})</p>
                    </div>
                    
                    <label className="toggle-container">
                      <input
                        type="checkbox"
                        checked={showVisibilityPolygon}
                        onChange={handleToggleVisibility}
                      />
                      <span className="toggle-label">Show Visibility Polygon</span>
                    </label>
                    
                    <button onClick={handleClearPOV} className="secondary-button">
                      Clear Point of View
                    </button>
                    
                    {computingVisibility && (
                      <div className="computing-status">
                        <div className="spinner"></div>
                        Computing visibility...
                      </div>
                    )}
                  </>
                )}
              </>
            )}
          </div>
        )}

        {selectedObstacleIndex !== null && (
          <div className="menu-section">
            <h3 onClick={() => toggleSection('selectedObstacle')} className="collapsible-header">
              <span className={`arrow ${expandedSections.selectedObstacle ? 'expanded' : ''}`}>▶</span>
              Selected Obstacle
            </h3>
            {expandedSections.selectedObstacle && (
              <>
                <div className="obstacle-info">
                  <p><strong>Obstacle Index:</strong> {selectedObstacleIndex}</p>
                  
                  {!features[selectedObstacleIndex] ? (
                    <button onClick={handleAssignFeature} className="primary-button">
                      Assign Feature
                    </button>
                  ) : (
                    <>
                      <button onClick={handleRemoveFeature} className="secondary-button">
                        Remove Feature
                      </button>
                      
                      <div className="feature-parameters">
                        <h4>Feature Parameters</h4>
                        
                        <label className="param-label">
                          <span>Visibility Value (0-1):</span>
                          <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.01"
                            value={features[selectedObstacleIndex].visibilityValue}
                            onChange={(e) => handleUpdateFeature('visibilityValue', parseFloat(e.target.value))}
                          />
                          <span className="param-value">{features[selectedObstacleIndex].visibilityValue.toFixed(2)}</span>
                        </label>
                        
                        <label className="param-label">
                          <span>Detail Visibility (0-1):</span>
                          <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.01"
                            value={features[selectedObstacleIndex].detailVisibilityValue}
                            onChange={(e) => handleUpdateFeature('detailVisibilityValue', parseFloat(e.target.value))}
                          />
                          <span className="param-value">{features[selectedObstacleIndex].detailVisibilityValue.toFixed(2)}</span>
                        </label>
                        
                        <h5>Feature 1</h5>
                        <label className="param-label">
                          <span>Contrast (0-1):</span>
                          <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.01"
                            value={features[selectedObstacleIndex].feature1Contrast}
                            onChange={(e) => handleUpdateFeature('feature1Contrast', parseFloat(e.target.value))}
                          />
                          <span className="param-value">{features[selectedObstacleIndex].feature1Contrast.toFixed(2)}</span>
                        </label>
                        
                        <label className="param-label">
                          <span>Spatial Freq (c/m):</span>
                          <input
                            type="number"
                            min="1"
                            max="500"
                            step="1"
                            value={features[selectedObstacleIndex].feature1SpatialFreq}
                            onChange={(e) => handleUpdateFeature('feature1SpatialFreq', parseFloat(e.target.value))}
                          />
                        </label>
                        
                        <h5>Feature 2</h5>
                        <label className="param-label">
                          <span>Contrast (0-1):</span>
                          <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.01"
                            value={features[selectedObstacleIndex].feature2Contrast}
                            onChange={(e) => handleUpdateFeature('feature2Contrast', parseFloat(e.target.value))}
                          />
                          <span className="param-value">{features[selectedObstacleIndex].feature2Contrast.toFixed(2)}</span>
                        </label>
                        
                        <label className="param-label">
                          <span>Spatial Freq (c/m):</span>
                          <input
                            type="number"
                            min="1"
                            max="500"
                            step="1"
                            value={features[selectedObstacleIndex].feature2SpatialFreq}
                            onChange={(e) => handleUpdateFeature('feature2SpatialFreq', parseFloat(e.target.value))}
                          />
                        </label>
                      </div>
                    </>
                  )}
                  
                  <button 
                    onClick={() => setSelectedObstacleIndex(null)} 
                    className="secondary-button"
                    style={{ marginTop: '10px' }}
                  >
                    Deselect Obstacle
                  </button>
                </div>
              </>
            )}
          </div>
        )}
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
            <h3 onClick={() => toggleSection('geometryData')} className="collapsible-header">
              <span className={`arrow ${expandedSections.geometryData ? 'expanded' : ''}`}>▶</span>
              Geometry Data
            </h3>
            {expandedSections.geometryData && (
              <>
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
              </>
            )}
          </div>
        )}
      </div>

      {/* Canvas Area */}
      <div className="canvas-container">
        <canvas 
          ref={canvasRef}
          onContextMenu={handleCanvasRightClick}
          onClick={handleCanvasLeftClick}
        ></canvas>
      </div>
    </div>
  );
}

export default VisibilitySim;