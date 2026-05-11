from __future__ import annotations
import numpy as np
import math

# 🌟 1. 새로 추가할 함수 (np.roll의 팩맨 현상 방지)
def safe_shift_3d(arr: np.ndarray, sx: int, sy: int, sz: int) -> np.ndarray:
    shifted = np.roll(arr, shift=(sx, sy, sz), axis=(0, 1, 2))
    
    # 넘어온(Wrap-around) 데이터를 0으로 초기화
    if sx > 0: shifted[:sx, :, :] = 0
    elif sx < 0: shifted[sx:, :, :] = 0
        
    if sy > 0: shifted[:, :sy, :] = 0
    elif sy < 0: shifted[:, sy:, :] = 0
        
    if sz > 0: shifted[:, :, :sz] = 0
    elif sz < 0: shifted[:, :, sz:] = 0
        
    return shifted

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
    free = occupancy.astype(np.float32)
    blocked = 1.0 - free
    diffused_blocked = simple_3d_blur(blocked, iterations=6)
    
    theta = math.radians(wind_direction)
    dx = math.cos(theta)
    dy = math.sin(theta)
    
    shift_amount = max(1, int(wind_speed / 4.0)) 
    wake = np.zeros_like(diffused_blocked)
    
    for step in range(1, shift_amount + 1):
        sx = int(round(dx * step))
        sy = int(round(dy * step))
        # 🌟 2. 기존 np.roll 대신 safe_shift_3d 사용
        shifted = safe_shift_3d(diffused_blocked, sx, sy, 0)
        wake += shifted * (0.9 ** step)

    height_map = np.sum(blocked, axis=2) 
    sx_wind = int(round(dx))
    sy_wind = int(round(dy))
    
    # 🌟 3. 여기서도 safe_shift_3d 사용
    windward_faces = np.logical_and(free, safe_shift_3d(blocked, sx_wind, sy_wind, 0))
    leeward_faces = np.logical_and(free, safe_shift_3d(blocked, -sx_wind, -sy_wind, 0))
    
    updraft = np.zeros_like(free)
    downdraft = np.zeros_like(free)
    
    for z_step in range(0, 8):
        decay = (0.7 ** z_step)
        # 🌟 4. 수직(Z축) 이동도 safe_shift_3d 사용
        updraft += safe_shift_3d(windward_faces.astype(np.float32), 0, 0, z_step) * decay * 1.5
        downdraft += safe_shift_3d(leeward_faces.astype(np.float32), 0, 0, z_step) * decay * 1.0

    speed_scale = min(max(wind_speed / 12.0, 0.3), 2.5)
    raw_risk = (diffused_blocked * 0.2 + wake * 0.4 + (updraft + downdraft) * 0.4) * speed_scale
    raw_risk *= free

    max_v = raw_risk.max()
    if max_v <= 1e-8:
        return raw_risk

    normalized = np.clip(raw_risk / max_v, 0.0, 1.0)
    normalized = np.power(normalized, 0.6) 
    return normalized