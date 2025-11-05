import platform
import sys
import os

def load_visibility_module():
    """
    Load the appropriate visibility_polygon binary based on OS.
    Returns the imported module.
    
    Expected files:
    - macOS: visibility_polygon.cpython-311-darwin.so
    - Windows: visibility_polygon.cp311-win_amd64.pyd
    - Linux: visibility_polygon.cpython-311-x86_64-linux-gnu.so
    """
    system = platform.system()
    python_version = f"{sys.version_info.major}{sys.version_info.minor}"
    
    module_dir = os.path.dirname(os.path.abspath(__file__))
    
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)
    
    try:
        import visibility_polygon
        print(f"✓ Successfully loaded visibility_polygon for {system} (Python {sys.version_info.major}.{sys.version_info.minor})")
        return visibility_polygon
    
    except ImportError as e:
        print(f"✗ Failed to load visibility_polygon on {system}")
        print(f"  Python version: {sys.version_info.major}.{sys.version_info.minor}")
        print(f"  Expected file in '{module_dir}':")
        
        if system == "Windows":
            print(f"    - visibility_polygon.cp{python_version}-win_amd64.pyd")
        elif system == "Darwin":  # macOS
            print(f"    - visibility_polygon.cpython-{python_version}-darwin.so")
        elif system == "Linux":
            print(f"    - visibility_polygon.cpython-{python_version}-x86_64-linux-gnu.so")
        
        try:
            files = [f for f in os.listdir(module_dir) if f.startswith('visibility_polygon')]
            if files:
                print(f"  Found files: {files}")
            else:
                print(f"  No visibility_polygon files found in directory")
        except:
            pass
        
        print(f"  Error: {e}")
        raise

vp = load_visibility_module()