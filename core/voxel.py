from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from typing import List, Dict, Any
from shapely.geometry import Polygon, Point
from core.data_fetcher import fetch_osm_buildings

@dataclass
class GridSpec:
    width: int = 150  # 1.5km approx
    depth: int = 150  # 1.5km approx
    height: int = 40  # 400m max
    voxel_size_m: int = 10
    
    # Grid Origin (Bottom-Left)
    base_lon: float = 126.6300
    base_lat: float = 37.3850
    
    # Degree steps for ~10m resolution
    lon_step: float = 0.00012
    lat_step: float = 0.00009
    alt_base: float = 50.0
    alt_step: float = 10.0

def create_airspace_grid(spec: GridSpec) -> np.ndarray:
    """Create a realistic occupancy grid from OSM data."""
    grid = np.ones((spec.width, spec.depth, spec.height), dtype=np.int8)
    
    # Define BBox for Overpass API
    # bbox: (south, west, north, east)
    south = spec.base_lat
    west = spec.base_lon
    north = spec.base_lat + spec.depth * spec.lat_step
    east = spec.base_lon + spec.width * spec.lon_step
    
    print(f"Fetching buildings for BBox: {south, west, north, east}")
    try:
        buildings = fetch_osm_buildings((south, west, north, east))
    except Exception as e:
        print(f"Error fetching OSM data: {e}. Falling back to empty grid.")
        return grid

    for b in buildings:
        nodes = b['nodes']
        if len(nodes) < 3:
            continue
            
        # Convert Lon/Lat nodes to grid X/Y indices
        poly_points = []
        for lon, lat in nodes:
            gx = (lon - spec.base_lon) / spec.lon_step
            gy = (lat - spec.base_lat) / spec.lat_step
            poly_points.append((gx, gy))
            
        poly = Polygon(poly_points)
        min_gx, min_gy, max_gx, max_gy = poly.bounds
        
        # Determine building height in grid units
        gz_max = int((b['height']) / spec.alt_step)
        gz_max = min(gz_max, spec.height)
        
        # Iterate through the bounding box of the polygon in grid space
        ix_min, ix_max = max(0, int(min_gx)), min(spec.width, int(max_gx) + 1)
        iy_min, iy_max = max(0, int(min_gy)), min(spec.depth, int(max_gy) + 1)
        
        for ix in range(ix_min, ix_max):
            for iy in range(iy_min, iy_max):
                if poly.contains(Point(ix, iy)):
                    grid[ix, iy, :gz_max] = 0
                    
    print(f"Voxelization complete. Grid shape: {grid.shape}")
    return grid
