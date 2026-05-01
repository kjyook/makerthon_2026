from __future__ import annotations

import numpy as np


def compute_risk_map(occupancy: np.ndarray, wind_speed: float, wind_direction: float) -> np.ndarray:
    """Compute normalized risk in [0, 1] using a simple Venturi/vortex-inspired heuristic."""
    free = occupancy.astype(np.float32)
    blocked = 1.0 - free

    # Approximate proximity to buildings by checking local neighborhood density.
    local_blocked = np.zeros_like(free)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                shifted = np.roll(blocked, shift=(dx, dy, dz), axis=(0, 1, 2))
                local_blocked += shifted

    # Venturi-like term: higher around narrow passages near blocked cells.
    venturi = local_blocked / 27.0

    # Directional term: project XY location onto wind heading to emulate wake asymmetry.
    nx, ny, nz = occupancy.shape
    xs = np.linspace(-1.0, 1.0, nx, dtype=np.float32)
    ys = np.linspace(-1.0, 1.0, ny, dtype=np.float32)
    xg, yg = np.meshgrid(xs, ys, indexing="ij")

    theta = np.deg2rad(wind_direction)
    dir_field = (xg * np.cos(theta) + yg * np.sin(theta))
    dir_field = (dir_field - dir_field.min()) / (dir_field.max() - dir_field.min() + 1e-6)
    dir_field = np.repeat(dir_field[:, :, None], nz, axis=2)

    speed_scale = min(max(wind_speed / 20.0, 0.0), 2.0)

    raw_risk = (0.65 * venturi + 0.35 * dir_field) * speed_scale
    raw_risk *= free

    max_v = raw_risk.max()
    if max_v <= 1e-8:
        return raw_risk

    return np.clip(raw_risk / max_v, 0.0, 1.0)
