import xml.etree.ElementTree as ET
import json
import re
from typing import List, Dict, Tuple, Optional
import os

class SVGFloorplanProcessor:
    """
    Process SVG floorplans for visibility polygon calculations.
    Handles doubled geometry from stroke widths and converts to GeoJSON.
    Uses only standard library - no external dependencies.
    """
    
    def __init__(self):
        self.tree = None
        self.root = None
        self.ns = {'svg': 'http://www.w3.org/2000/svg'}
        self.geometries = []
        self.geojson_data = None
        self.viewbox = None
        self.parent_map = {}
        
    def import_svg(self, filepath: str) -> 'SVGFloorplanProcessor':
        """
        Import an SVG file.
        
        Args:
            filepath: Path to the SVG file
            
        Returns:
            self for method chaining
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"SVG file not found: {filepath}")
        
        self.tree = ET.parse(filepath)
        self.root = self.tree.getroot()
        
        # Build parent map for finding parent groups
        self.parent_map = {c: p for p in self.root.iter() for c in p}
        
        # Extract viewBox dimensions
        viewbox = self.root.get('viewBox')
        if viewbox:
            parts = viewbox.split()
            self.viewbox = {
                'x': float(parts[0]),
                'y': float(parts[1]),
                'width': float(parts[2]),
                'height': float(parts[3])
            }
        else:
            # Fallback to width/height attributes
            width = self.root.get('width', '0')
            height = self.root.get('height', '0')
            # Remove units if present
            width = re.sub(r'[^\d.]', '', width)
            height = re.sub(r'[^\d.]', '', height)
            
            self.viewbox = {
                'x': 0,
                'y': 0,
                'width': float(width) if width else 0,
                'height': float(height) if height else 0
            }
        
        print(f"✓ Imported SVG: {filepath}")
        print(f"  ViewBox: {self.viewbox['width']} x {self.viewbox['height']}")
        
        return self
    
    def clean_svg(self, keep_groups: bool = True) -> 'SVGFloorplanProcessor':
        """
        Clean SVG by extracting only outer path boundaries.
        Removes doubled geometry caused by stroke widths.
        
        Args:
            keep_groups: Whether to preserve group structure
            
        Returns:
            self for method chaining
        """
        if self.tree is None:
            raise ValueError("No SVG loaded. Call import_svg() first.")
        
        paths = self.root.findall('.//svg:path', self.ns)
        self.geometries = []
        cleaned_count = 0
        
        for path_elem in paths:
            d = path_elem.get('d')
            if not d:
                continue
            
            # Split by 'M' to identify subpaths (doubled geometry)
            # The pattern matches 'M' followed by coordinates
            subpaths = re.split(r'(?=[Mm])', d)
            subpaths = [sp.strip() for sp in subpaths if sp.strip()]
            
            if not subpaths:
                continue
            
            # Extract only the first (outer) subpath
            outer_path = subpaths[0]
            
            # Parse and extract coordinates
            try:
                points = self._parse_path_to_points(outer_path)
                
                if len(points) >= 3:  # Valid polygon
                    # Get parent group ID using parent_map
                    parent = self.parent_map.get(path_elem)
                    parent_id = None
                    if parent is not None:
                        parent_id = parent.get('id')
                    
                    self.geometries.append({
                        'points': points,
                        'original_path': d,
                        'cleaned_path': outer_path,
                        'parent_group': parent_id
                    })
                    
                    # Update the path element with cleaned data
                    path_elem.set('d', outer_path)
                    cleaned_count += 1
                    
            except Exception as e:
                print(f"⚠ Warning: Could not parse path: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"✓ Cleaned {cleaned_count} paths (removed doubled geometry)")
        return self
    
    def _parse_path_to_points(self, path_string: str) -> List[Tuple[float, float]]:
        """
        Parse SVG path string to extract coordinate points.
        Handles M, L, H, V, Z commands (common in architectural drawings).
        """
        points = []
        current_x, current_y = 0.0, 0.0
        
        # Remove the command letter and split by command
        commands = re.findall(r'[MmLlHhVvZz][^MmLlHhVvZz]*', path_string)
        
        for cmd in commands:
            cmd_type = cmd[0]
            coords = cmd[1:].strip()
            
            # Extract numbers (including negative and decimals)
            numbers = re.findall(r'-?\d+\.?\d*', coords)
            numbers = [float(n) for n in numbers]
            
            if cmd_type in 'Mm':  # Move to
                if len(numbers) >= 2:
                    if cmd_type == 'M':  # Absolute
                        current_x, current_y = numbers[0], numbers[1]
                    else:  # Relative
                        current_x += numbers[0]
                        current_y += numbers[1]
                    points.append((current_x, current_y))
                    
                    # Remaining pairs are treated as line-to commands
                    for i in range(2, len(numbers), 2):
                        if i + 1 < len(numbers):
                            if cmd_type == 'M':
                                current_x, current_y = numbers[i], numbers[i+1]
                            else:
                                current_x += numbers[i]
                                current_y += numbers[i+1]
                            points.append((current_x, current_y))
            
            elif cmd_type in 'Ll':  # Line to
                for i in range(0, len(numbers), 2):
                    if i + 1 < len(numbers):
                        if cmd_type == 'L':  # Absolute
                            current_x, current_y = numbers[i], numbers[i+1]
                        else:  # Relative
                            current_x += numbers[i]
                            current_y += numbers[i+1]
                        points.append((current_x, current_y))
            
            elif cmd_type in 'Hh':  # Horizontal line
                for num in numbers:
                    if cmd_type == 'H':  # Absolute
                        current_x = num
                    else:  # Relative
                        current_x += num
                    points.append((current_x, current_y))
            
            elif cmd_type in 'Vv':  # Vertical line
                for num in numbers:
                    if cmd_type == 'V':  # Absolute
                        current_y = num
                    else:  # Relative
                        current_y += num
                    points.append((current_x, current_y))
            
            elif cmd_type in 'Zz':  # Close path
                # Don't add the closing point (we'll add it in GeoJSON conversion)
                pass
        
        # Remove duplicate consecutive points
        cleaned_points = []
        for point in points:
            if not cleaned_points or point != cleaned_points[-1]:
                cleaned_points.append(point)
        
        # Remove closing point if it duplicates the first
        if len(cleaned_points) > 1 and cleaned_points[0] == cleaned_points[-1]:
            cleaned_points = cleaned_points[:-1]
        
        return cleaned_points
    
    def save_svg(self, output_path: str) -> 'SVGFloorplanProcessor':
        """
        Save the cleaned SVG to a file.
        
        Args:
            output_path: Path where cleaned SVG will be saved
            
        Returns:
            self for method chaining
        """
        if self.tree is None:
            raise ValueError("No SVG loaded. Call import_svg() and clean_svg() first.")
        
        # Register namespace to avoid ns0 prefixes
        ET.register_namespace('', 'http://www.w3.org/2000/svg')
        
        self.tree.write(output_path, encoding='utf-8', xml_declaration=True)
        print(f"✓ Saved cleaned SVG to: {output_path}")
        
        return self
    
    def create_preview_svg(self, output_path: str, 
                          stroke_color: str = "#000000",
                          stroke_width: float = 2,
                          fill: str = "none",
                          background: str = "#ffffff") -> 'SVGFloorplanProcessor':
        """
        Create a visual preview SVG with strokes (not fills) for easy inspection.
        
        Args:
            output_path: Path where preview SVG will be saved
            stroke_color: Color for the obstacle outlines
            stroke_width: Width of the stroke
            fill: Fill color (default: "none" for transparent)
            background: Background color
            
        Returns:
            self for method chaining
        """
        if not self.geometries:
            raise ValueError("No geometries to preview. Call clean_svg() first.")
        
        # Create new SVG
        svg = ET.Element('svg', {
            'xmlns': 'http://www.w3.org/2000/svg',
            'width': str(self.viewbox['width']),
            'height': str(self.viewbox['height']),
            'viewBox': f"{self.viewbox['x']} {self.viewbox['y']} {self.viewbox['width']} {self.viewbox['height']}"
        })
        
        # Add background
        bg = ET.SubElement(svg, 'rect', {
            'x': str(self.viewbox['x']),
            'y': str(self.viewbox['y']),
            'width': str(self.viewbox['width']),
            'height': str(self.viewbox['height']),
            'fill': background
        })
        
        # Add each geometry as a polygon
        for i, geom in enumerate(self.geometries):
            points_str = ' '.join([f"{x},{y}" for x, y in geom['points']])
            
            polygon = ET.SubElement(svg, 'polygon', {
                'points': points_str,
                'fill': fill,
                'stroke': stroke_color,
                'stroke-width': str(stroke_width),
                'data-id': str(i),
                'data-group': geom['parent_group'] or 'none'
            })
        
        # Write to file
        tree = ET.ElementTree(svg)
        ET.register_namespace('', 'http://www.w3.org/2000/svg')
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        
        print(f"✓ Created preview SVG: {output_path}")
        print(f"  Open this file to visually verify the extracted geometry")
        
        return self
    
    def inspect_geometries(self, limit: int = 5):
        """
        Print detailed information about the extracted geometries.
        
        Args:
            limit: Maximum number of geometries to display in detail
        """
        if not self.geometries:
            print("No geometries to inspect. Call clean_svg() first.")
            return
        
        print("\n" + "="*60)
        print("GEOMETRY INSPECTION")
        print("="*60)
        
        for i, geom in enumerate(self.geometries[:limit]):
            print(f"\nObstacle {i}:")
            print(f"  Group: {geom['parent_group']}")
            print(f"  Points: {len(geom['points'])}")
            print(f"  Coordinates:")
            for j, (x, y) in enumerate(geom['points']):
                print(f"    [{j}] ({x:.2f}, {y:.2f})")
            
            # Calculate bounding box
            xs = [p[0] for p in geom['points']]
            ys = [p[1] for p in geom['points']]
            print(f"  BBox: ({min(xs):.2f}, {min(ys):.2f}) to ({max(xs):.2f}, {max(ys):.2f})")
            print(f"  Size: {max(xs)-min(xs):.2f} x {max(ys)-min(ys):.2f}")
        
        if len(self.geometries) > limit:
            print(f"\n... and {len(self.geometries) - limit} more obstacles")
        
        print("="*60 + "\n")
        return self
    
    def create_matplotlib_preview(self, output_path: Optional[str] = None):
        """
        Create a matplotlib visualization of the geometries.
        Requires matplotlib to be installed (optional).
        
        Args:
            output_path: If provided, saves the plot to this path. Otherwise displays it.
        """
        try:
            import matplotlib.pyplot as plt
            from matplotlib.patches import Polygon as MplPolygon
            from matplotlib.collections import PatchCollection
        except ImportError:
            print("⚠ Matplotlib not installed. Install with: pip install matplotlib")
            return
        
        if not self.geometries:
            print("No geometries to visualize. Call clean_svg() first.")
            return
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        patches = []
        colors = []
        
        # Color by group
        groups = list(set(g['parent_group'] for g in self.geometries if g['parent_group']))
        color_map = {group: i for i, group in enumerate(groups)}
        
        for geom in self.geometries:
            polygon = MplPolygon(geom['points'], closed=True)
            patches.append(polygon)
            
            # Color by group
            if geom['parent_group']:
                colors.append(color_map.get(geom['parent_group'], 0))
            else:
                colors.append(0)
        
        p = PatchCollection(patches, alpha=0.4, edgecolors='black', linewidths=2)
        p.set_array(colors)
        ax.add_collection(p)
        
        # Set limits
        ax.set_xlim(self.viewbox['x'], self.viewbox['x'] + self.viewbox['width'])
        ax.set_ylim(self.viewbox['y'], self.viewbox['y'] + self.viewbox['height'])
        ax.set_aspect('equal')
        ax.invert_yaxis()  # SVG has Y axis pointing down
        
        ax.set_xlabel('X (pixels)')
        ax.set_ylabel('Y (pixels)')
        ax.set_title(f'Extracted Geometries ({len(self.geometries)} obstacles)')
        ax.grid(True, alpha=0.3)
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"✓ Saved matplotlib preview: {output_path}")
        else:
            plt.show()
    
    def convert_to_geojson(self, feature_properties: Optional[Dict] = None) -> 'SVGFloorplanProcessor':
        """
        Convert cleaned geometries to GeoJSON format.
        Uses a custom CRS for pixel coordinates.
        
        Args:
            feature_properties: Optional properties to add to each feature
            
        Returns:
            self for method chaining
        """
        if not self.geometries:
            raise ValueError("No geometries to convert. Call clean_svg() first.")
        
        features = []
        
        for i, geom in enumerate(self.geometries):
            # GeoJSON expects [lon, lat] which we map to [x, y]
            # Close the polygon by repeating first point
            coordinates = [geom['points'] + [geom['points'][0]]]
            
            feature = {
                "type": "Feature",
                "id": i,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": coordinates
                },
                "properties": {
                    "obstacle_id": i,
                    "group": geom['parent_group'],
                    "point_count": len(geom['points']),
                    **(feature_properties or {})
                }
            }
            
            features.append(feature)
        
        self.geojson_data = {
            "type": "FeatureCollection",
            "crs": {
                "type": "name",
                "properties": {
                    "name": "urn:ogc:def:crs:EPSG::0"  # Custom pixel-based CRS
                }
            },
            "metadata": {
                "viewBox": self.viewbox,
                "units": "pixels",
                "coordinate_system": "top-left origin, +x right, +y down"
            },
            "features": features
        }
        
        print(f"✓ Converted {len(features)} geometries to GeoJSON")
        return self
    
    def export_to_geojson(self, output_path: str, indent: int = 2) -> 'SVGFloorplanProcessor':
        """
        Export GeoJSON data to a file.
        
        Args:
            output_path: Path where GeoJSON will be saved
            indent: JSON indentation level (default: 2)
            
        Returns:
            self for method chaining
        """
        if self.geojson_data is None:
            raise ValueError("No GeoJSON data to export. Call convert_to_geojson() first.")
        
        with open(output_path, 'w') as f:
            json.dump(self.geojson_data, f, indent=indent)
        
        print(f"✓ Exported GeoJSON to: {output_path}")
        return self
    
    def get_statistics(self) -> Dict:
        """Get statistics about the processed geometries."""
        if not self.geometries:
            return {"status": "No geometries loaded"}
        
        point_counts = [len(g['points']) for g in self.geometries]
        
        # Calculate bounding boxes
        all_x = []
        all_y = []
        for geom in self.geometries:
            for x, y in geom['points']:
                all_x.append(x)
                all_y.append(y)
        
        bbox = {
            "min_x": min(all_x) if all_x else 0,
            "max_x": max(all_x) if all_x else 0,
            "min_y": min(all_y) if all_y else 0,
            "max_y": max(all_y) if all_y else 0
        }
        
        return {
            "total_obstacles": len(self.geometries),
            "viewbox": self.viewbox,
            "bounding_box": bbox,
            "points_per_obstacle": {
                "min": min(point_counts),
                "max": max(point_counts),
                "avg": sum(point_counts) / len(point_counts)
            },
            "groups": list(set(g['parent_group'] for g in self.geometries if g['parent_group']))
        }
    
    def print_summary(self):
        """Print a summary of the processed data."""
        stats = self.get_statistics()
        
        print("\n" + "="*50)
        print("SVG PROCESSING SUMMARY")
        print("="*50)
        
        if "status" in stats:
            print(stats["status"])
            return
        
        print(f"Total Obstacles: {stats['total_obstacles']}")
        print(f"Canvas Size: {stats['viewbox']['width']:.2f} x {stats['viewbox']['height']:.2f}")
        print(f"Bounding Box: ({stats['bounding_box']['min_x']:.2f}, {stats['bounding_box']['min_y']:.2f}) to ({stats['bounding_box']['max_x']:.2f}, {stats['bounding_box']['max_y']:.2f})")
        print(f"Points per obstacle: {stats['points_per_obstacle']['min']}-{stats['points_per_obstacle']['max']} (avg: {stats['points_per_obstacle']['avg']:.1f})")
        
        if stats['groups']:
            print(f"Groups found: {', '.join(stats['groups'])}")
        
        print("="*50 + "\n")


