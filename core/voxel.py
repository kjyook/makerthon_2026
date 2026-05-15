from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from typing import List, Dict, Any
from core.data_fetcher import fetch_osm_buildings

@dataclass
class GridSpec:
    width: int = 300  # 1.5km approx
    depth: int = 300  # 1.5km approx
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

def _inflate_obstacles(grid: np.ndarray) -> np.ndarray:
    """
    Inflate blocked cells (0) by 1 voxel (10m) in all 3D directions to create a safety buffer.
    Since grid uses 1 for air and 0 for building, we want to expand the 0s.
    """
    inflated = grid.copy()
    
    # 26-way expansion (full 3D Moore neighborhood)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dy == 0 and dz == 0:
                    continue
                # Shift the grid. True (1) becomes False (0) if the shifted neighbor is False (0)
                shifted = np.roll(grid, shift=(dx, dy, dz), axis=(0, 1, 2))
                inflated = np.logical_and(inflated, shifted)
                
    return inflated.astype(np.int8)


def _point_in_polygon(x: float, y: float, polygon: List[tuple[float, float]]) -> bool:
    """Return True when a 2D point is inside a polygon using ray casting."""
    inside = False
    count = len(polygon)
    if count < 3:
        return False

    previous_x, previous_y = polygon[-1]
    for current_x, current_y in polygon:
        intersects = ((current_y > y) != (previous_y > y)) and (
            x < (previous_x - current_x) * (y - current_y) / ((previous_y - current_y) or 1e-12) + current_x
        )
        if intersects:
            inside = not inside
        previous_x, previous_y = current_x, current_y

    return inside

def create_airspace_grid(spec: GridSpec) -> np.ndarray:
    """Create a realistic occupancy grid from OSM data with a safety buffer."""
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

        # Convert Lon/Lat nodes to grid X/Y indices.
        poly_points = []
        for lon, lat in nodes:
            gx = (lon - spec.base_lon) / spec.lon_step
            gy = (lat - spec.base_lat) / spec.lat_step
            poly_points.append((gx, gy))

        xs = [p[0] for p in poly_points]
        ys = [p[1] for p in poly_points]
        min_gx, max_gx = min(xs), max(xs)
        min_gy, max_gy = min(ys), max(ys)
        
        # Determine building height in grid units
        # Add a 20m (2 voxels) explicit vertical safety margin because visual 
        # building models often have roofs/structures taller than OSM metadata.
        gz_max = int((b['height'] + 20.0) / spec.alt_step)
        gz_max = min(gz_max, spec.height)
        
        # Iterate through the bounding box of the polygon in grid space
        ix_min, ix_max = max(0, int(min_gx)), min(spec.width, int(max_gx) + 1)
        iy_min, iy_max = max(0, int(min_gy)), min(spec.depth, int(max_gy) + 1)
        
        for ix in range(ix_min, ix_max):
            for iy in range(iy_min, iy_max):
                # Use the cell center for a stable, dependency-free intersection test.
                if _point_in_polygon(ix + 0.5, iy + 0.5, poly_points):
                    grid[ix, iy, :gz_max] = 0
                    
    # Apply 10m safety buffer (inflation)
    grid = _inflate_obstacles(grid)
                    
    print(f"Voxelization complete. Grid shape: {grid.shape}")
    return grid
