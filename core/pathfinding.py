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
    wind_speed: float,
    wind_direction: float,
    vehicle_type: str = "passenger",
) -> Optional[List[Point3D]]:
    """
    3D A* with Dynamic Cost Function:
    - Distance: Euclidean distance between nodes.
    - Risk: Local environment risk multiplied by vehicle sensitivity.
    - Wind: Movement into headwind adds cost (energy consumption).
    - Altitude: Slight penalty for flying too high unnecessarily.
    """
    if occupancy[start] == 0 or occupancy[end] == 0:
        return None

    # Configuration
    vehicle_sensitivity = {
        "passenger": 2.0,    # High safety priority
        "delivery": 1.0,     # Balanced
        "emergency": 0.5,    # Speed priority, high risk tolerance
    }.get(vehicle_type, 1.0)
    
    altitude_penalty = 0.05  # Energy cost per altitude level
    
    # Wind vector
    theta = np.deg2rad(wind_direction)
    wind_vec = np.array([np.cos(theta), np.sin(theta), 0], dtype=np.float32)

    frontier: List[Tuple[float, Point3D]] = []
    heapq.heappush(frontier, (0.0, start))

    came_from: Dict[Point3D, Optional[Point3D]] = {start: None}
    cost_so_far: Dict[Point3D, float] = {start: 0.0}
    closed_set: set[Point3D] = set()

    while frontier:
        _, current = heapq.heappop(frontier)

        if current == end:
            break

        if current in closed_set:
            continue
        closed_set.add(current)

        for nxt in _neighbors_26(current, occupancy.shape):
            if occupancy[nxt] == 0:
                continue

            # 1. Base Distance Cost
            dist = _distance(current, nxt)
            
            # 2. Risk Cost
            # Sensitivity * Local Risk
            risk_cost = vehicle_sensitivity * float(risk_map[nxt]) * 15.0 # Scale for impact
            
            # 3. Wind Dynamic Cost
            # If moving AGAINST wind direction, increase cost
            move_vec = np.array(nxt, dtype=np.float32) - np.array(current, dtype=np.float32)
            # Dot product: negative if moving against wind, positive if with wind
            # We want to PENALIZE moving AGAINST wind (negative dot product)
            wind_impact = -np.dot(move_vec, wind_vec) * (wind_speed / 5.0)
            wind_cost = max(0, wind_impact)
            
            # 4. Altitude Cost
            # Penalty for vertical changes (climbing or diving)
            alt_diff = abs(nxt[2] - current[2])
            alt_cost = alt_diff * 2.0

            move_cost = dist + risk_cost + wind_cost + alt_cost
            new_cost = cost_so_far[current] + move_cost

            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                cost_so_far[nxt] = new_cost
                # Weighted A* for extreme performance on large grids
                # SACRIFICE: Shortest path vs speed
                heuristic_weight = 5.0
                priority = new_cost + heuristic_weight * _distance(nxt, end)
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

