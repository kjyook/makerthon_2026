from __future__ import annotations
import numpy as np
import math

def safe_shift_3d(arr: np.ndarray, sx: int, sy: int, sz: int) -> np.ndarray:
    """Shift 3D array without wrap-around (filling with 0)."""
    shifted = np.roll(arr, shift=(sx, sy, sz), axis=(0, 1, 2))
    
    if sx > 0: shifted[:sx, :, :] = 0
    elif sx < 0: shifted[sx:, :, :] = 0
        
    if sy > 0: shifted[:, :sy, :] = 0
    elif sy < 0: shifted[:, sy:, :] = 0
        
    if sz > 0: shifted[:, :, :sz] = 0
    elif sz < 0: shifted[:, :, sz:] = 0
        
    return shifted

def simple_3d_blur(arr: np.ndarray, iterations: int = 2) -> np.ndarray:
    """A simple 3D moving average to simulate diffusion/blur."""
    result = arr.copy()
    for _ in range(iterations):
        padded = np.pad(result, pad_width=1, mode='constant', constant_values=0)
        result = (
            padded[1:-1, 1:-1, 1:-1] * 2.0 +
            padded[:-2, 1:-1, 1:-1] + padded[2:, 1:-1, 1:-1] +
            padded[1:-1, :-2, 1:-1] + padded[1:-1, 2:, 1:-1] +
            padded[1:-1, 1:-1, :-2] + padded[1:-1, 1:-1, 2:]
        ) / 8.0
    return result

def compute_risk_map(occupancy: np.ndarray, wind_speed: float, wind_direction: float) -> np.ndarray:
    """
    Advanced Wake & Vortex Risk Model.
    Calculates risk based on obstacle proximity, windward pressure, building wake, 
    and edge vortex effects.
    """
    free = occupancy.astype(np.float32)
    blocked = 1.0 - free
    
    # Grid resolution (assumed 10m from GridSpec)
    voxel_size = 10.0
    
    theta = math.radians(wind_direction)
    dx = math.cos(theta)
    dy = math.sin(theta)
    
    # 1. Physical Obstacle Proximity (Safety Buffer)
    # Buildings themselves are 100% risk, and immediate vicinity is high risk.
    proximity = simple_3d_blur(blocked, iterations=3)

    # 2. Windward Pressure Zone
    # High pressure zone where wind hits the building surface.
    sx_wind = int(round(dx))
    sy_wind = int(round(dy))
    windward_faces = np.logical_and(free, safe_shift_3d(blocked, sx_wind, sy_wind, 0)).astype(np.float32)
    pressure_zone = simple_3d_blur(windward_faces, iterations=2) * 1.5

    # 3. Advanced Building Wake (Leeward Turbulence)
    # The wake length is roughly proportional to building height and width.
    # We simulate this by accumulating shifted building "shadows" with decay.
    # Higher buildings cast longer wakes.
    
    # Calculate building height map to weight wake
    # Each voxel's 'height weight' is its Z-index + 1
    z_indices = np.arange(occupancy.shape[2], dtype=np.float32).reshape(1, 1, -1)
    building_height_weight = blocked * (z_indices + 1.0)
    
    # Wake length scales with wind speed and building height
    max_wake_steps = max(2, int(wind_speed / 2.0)) 
    wake = np.zeros_like(free)
    
    # Accumulate shifted "height-weighted" blocked voxels in the leeward direction
    for step in range(1, max_wake_steps + 1):
        sx = int(round(dx * -step)) # Negative because wind blows FROM (dx, dy)
        sy = int(round(dy * -step))
        decay = 0.85 ** step
        # Shift the building weight to simulate the wake region
        shifted_wake = safe_shift_3d(building_height_weight, sx, sy, 0)
        # Higher voxels contribute more to the wake intensity
        wake += (shifted_wake / (z_indices + 1.0 + 1e-6)) * decay

    # 4. Edge Vortex (Tip & Corner Turbulence)
    # Vortexes form at the corners and top edges where wind separates.
    perp_dx = -dy
    perp_dy = dx
    
    # Top edge vortex (voxels just above buildings)
    top_edge = np.logical_and(free, safe_shift_3d(blocked, 0, 0, 1)).astype(np.float32)
    
    # Side edge vortex (voxels to the sides relative to wind direction)
    side_edge_1 = np.logical_and(free, safe_shift_3d(blocked, int(round(perp_dx)), int(round(perp_dy)), 0))
    side_edge_2 = np.logical_and(free, safe_shift_3d(blocked, int(round(-perp_dx)), int(round(-perp_dy)), 0))
    side_edges = np.logical_or(side_edge_1, side_edge_2).astype(np.float32)
    
    vortex_zones = simple_3d_blur(top_edge + side_edges, iterations=2) * 2.0

    # 5. Updraft and Downdraft
    # Simplified vertical flow near windward/leeward faces.
    updraft = np.zeros_like(free)
    downdraft = np.zeros_like(free)
    leeward_faces = np.logical_and(free, safe_shift_3d(blocked, -sx_wind, -sy_wind, 0)).astype(np.float32)
    
    for z_step in range(1, 6):
        decay = (0.6 ** z_step)
        updraft += safe_shift_3d(windward_faces, 0, 0, z_step) * decay
        downdraft += safe_shift_3d(leeward_faces, 0, 0, z_step) * decay

    # --- Combine All Factors ---
    # Coefficients adjusted for visual impact and physical reasoning
    speed_factor = min(max(wind_speed / 10.0, 0.5), 3.0)
    
    raw_risk = (
        proximity * 0.3 +       # Physical buffer
        pressure_zone * 0.2 +   # Windward impact
        wake * 0.4 +            # Leeward turbulence
        vortex_zones * 0.3 +    # Corner vortex
        (updraft * 0.15 + downdraft * 0.1) # Vertical flows
    ) * speed_factor
    
    # Apply occupancy mask (risk inside building is always 1, but pathfinding avoids it)
    raw_risk = np.where(blocked > 0.5, 1.0, raw_risk)
    raw_risk *= free # Outside buildings only for the "fluid" risk

    # Normalize to [0, 1]
    max_v = raw_risk.max()
    if max_v > 1e-8:
        raw_risk /= max_v
    
    # Non-linear scaling to emphasize high-risk areas
    normalized = np.clip(raw_risk, 0.0, 1.0)
    normalized = np.power(normalized, 0.7) 
    
    return normalized
