from __future__ import annotations

import heapq
from typing import Dict, List, Optional, Tuple

import numpy as np

Point3D = Tuple[int, int, int]


def _neighbors_26(node: Point3D, shape: Tuple[int, int, int]):
    x, y, z = node
    max_x, max_y, max_z = shape
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dy == 0 and dz == 0:
                    continue
                nx, ny, nz = x + dx, y + dy, z + dz
                if 0 <= nx < max_x and 0 <= ny < max_y and 0 <= nz < max_z:
                    yield (nx, ny, nz)


def _distance(a: Point3D, b: Point3D) -> float:
    return float(np.linalg.norm(np.array(a, dtype=np.float32) - np.array(b, dtype=np.float32)))


def find_path_astar(
    occupancy: np.ndarray,
    risk_map: np.ndarray,
    start: Point3D,
    end: Point3D,
    alpha: float,
) -> Optional[List[Point3D]]:
    """3D A* with 26-direction moves and risk-weighted traversal cost."""
    if occupancy[start] == 0 or occupancy[end] == 0:
        return None

    frontier: List[Tuple[float, Point3D]] = []
    heapq.heappush(frontier, (0.0, start))

    came_from: Dict[Point3D, Optional[Point3D]] = {start: None}
    cost_so_far: Dict[Point3D, float] = {start: 0.0}

    while frontier:
        _, current = heapq.heappop(frontier)

        if current == end:
            break

        for nxt in _neighbors_26(current, occupancy.shape):
            if occupancy[nxt] == 0:
                continue

            step_cost = _distance(current, nxt)
            move_cost = step_cost + float(risk_map[nxt]) * alpha
            new_cost = cost_so_far[current] + move_cost

            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                cost_so_far[nxt] = new_cost
                priority = new_cost + _distance(nxt, end)
                heapq.heappush(frontier, (priority, nxt))
                came_from[nxt] = current

    if end not in came_from:
        return None

    path: List[Point3D] = []
    cur: Optional[Point3D] = end
    while cur is not None:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()
    return path
