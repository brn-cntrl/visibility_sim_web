from SVGFloorplanProcessor import SVGFloorplanProcessor

# Example usage
if __name__ == '__main__':
    # Create processor instance
    processor = SVGFloorplanProcessor()
    
    # Full pipeline with visualization
    processor \
        .import_svg('static/lacma.svg') \
        .clean_svg() \
        .inspect_geometries(limit=3) \
        .create_preview_svg('floorplan_preview.svg') \
        .save_svg('floorplan_cleaned.svg') \
        .convert_to_geojson() \
        .export_to_geojson('floorplan.geojson') \
        .print_summary()
    
    # Optional: Create matplotlib visualization
    # processor.create_matplotlib_preview('floorplan_plot.png')