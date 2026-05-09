from __future__ import annotations
import numpy as np
import math

def simple_3d_blur(arr: np.ndarray, iterations: int = 2) -> np.ndarray:
    """A simple 3D moving average to simulate diffusion/blur without requiring scipy."""
    result = arr.copy()
    for _ in range(iterations):
        padded = np.pad(result, pad_width=1, mode='constant', constant_values=0)
        # 7-point stencil (center + 6 directions)
        result = (
            padded[1:-1, 1:-1, 1:-1] * 2.0 +  # Center weight
            padded[:-2, 1:-1, 1:-1] + padded[2:, 1:-1, 1:-1] +
            padded[1:-1, :-2, 1:-1] + padded[1:-1, 2:, 1:-1] +
            padded[1:-1, 1:-1, :-2] + padded[1:-1, 1:-1, 2:]
        ) / 8.0
    return result

def compute_risk_map(occupancy: np.ndarray, wind_speed: float, wind_direction: float) -> np.ndarray:
    """
    Advanced Risk Model (Test Version)
    1. Base building density with blur (spatial diffusion)
    2. Directional Wake: Shifting the density in the direction of the wind to simulate tails.
    3. Updraft: Extra risk directly above buildings.
    """
    free = occupancy.astype(np.float32)
    blocked = 1.0 - free

    # 1. Spatial Diffusion (Blur)
    # Make buildings 'emit' risk that spreads outwards
    diffused_blocked = simple_3d_blur(blocked, iterations=6)
    
    # 2. Directional Wake (Tails)
    # Calculate wind vector (X, Y)
    theta = math.radians(wind_direction)
    dx = math.cos(theta)
    dy = math.sin(theta)
    
    # Shift the diffused blocked array in the direction of the wind to simulate a wake
    # We do a simple roll. If wind is strong, we shift more.
    shift_amount = max(1, int(wind_speed / 4.0)) # Up to ~7 voxels (70m)
    wake = np.zeros_like(diffused_blocked)
    
    for step in range(1, shift_amount + 1):
        # We use negative shift because wind pushes risk 'away' from buildings
        # Actually dx, dy are wind directions, so risk should move with wind.
        sx = int(round(dx * step))
        sy = int(round(dy * step))
        # np.roll is a circular shift, but for small shifts in large grid it's okay-ish.
        # Ideally we'd use a non-circular shift.
        shifted = np.roll(diffused_blocked, shift=(sx, sy, 0), axis=(0, 1, 2))
        wake += shifted * (0.9 ** step) # Slower exponential decay

    # 3. Updraft (Rising air over buildings)
    # Shift blocked array upwards (Z direction)
    updraft = np.zeros_like(diffused_blocked)
    for z_step in range(1, 4): # Up to 30m above
        updraft += np.roll(blocked, shift=z_step, axis=2) * (0.6 ** z_step)

    # Combine terms
    speed_scale = min(max(wind_speed / 12.0, 0.3), 2.5)
    
    # Weights: Diffusion(30%), Wake(50%), Updraft(20%)
    raw_risk = (diffused_blocked * 0.3 + wake * 0.5 + updraft * 0.2) * speed_scale
    
    # Only apply risk to 'free' airspace
    raw_risk *= free

    max_v = raw_risk.max()
    if max_v <= 1e-8:
        return raw_risk

    # Normalize and clip
    normalized = np.clip(raw_risk / max_v, 0.0, 1.0)
    
    # Gamma correction to make the 'cloud' more visible at 0.6 threshold
    normalized = np.power(normalized, 0.6) 
    
    return normalized
