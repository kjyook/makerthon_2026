from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import numpy as np
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from core.llm import get_risk_alpha
from core.pathfinding import find_path_astar
from core.test_physics import compute_risk_map
from core.voxel import GridSpec, create_airspace_grid

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

GRID_SPEC = GridSpec()
OCCUPANCY = create_airspace_grid(GRID_SPEC)


def _to_point3d(payload: Dict[str, Any], key: str) -> Tuple[int, int, int]:
    value = payload.get(key)
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"'{key}' must be a list of 3 integers")
    try:
        point = tuple(int(v) for v in value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"'{key}' must contain integers") from exc

    x, y, z = point
    max_x, max_y, max_z = OCCUPANCY.shape
    if not (0 <= x < max_x and 0 <= y < max_y and 0 <= z < max_z):
        raise ValueError(f"'{key}' out of grid bounds")
    return point


@app.get("/")
def index():
    # .env 파일에서 토큰을 읽어옵니다.
    # 토큰이 없을 경우를 대비해 기본값 None을 설정합니다.
    cesium_token = os.getenv('CESIUM_ION_TOKEN')
    
    # render_template에 cesium_token 변수를 추가하여 전달합니다.
    return render_template(
        "index.html", 
        grid_shape=OCCUPANCY.shape, 
        cesium_token=cesium_token
    )

@app.get("/vworld")
def vworld_map():
    return render_template("vWorldView.html")


@app.get("/api/risk-map")
def risk_map_api():
    try:
        wind_speed = float(request.args.get("wind_speed", 8.0) or 8.0)
        wind_direction = float(request.args.get("wind_direction", 90.0) or 90.0)
    except (ValueError, TypeError):
        wind_speed, wind_direction = 8.0, 90.0

    risk_map = compute_risk_map(OCCUPANCY, wind_speed=wind_speed, wind_direction=wind_direction)

    # Send only sparse high-risk voxels to keep payload lightweight.
    threshold = float(request.args.get("threshold", 0.55) or 0.55)
    idx = np.argwhere(risk_map >= threshold)

    points: List[Dict[str, Any]] = []
    for x, y, z in idx.tolist():
        points.append({"x": x, "y": y, "z": z, "risk": float(risk_map[x, y, z])})

    return jsonify(
        {
            "grid_shape": list(OCCUPANCY.shape),
            "voxel_size_m": GRID_SPEC.voxel_size_m,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "threshold": threshold,
            "points": points,
        }
    )


@app.post("/api/route")
def route_api():
    payload = request.get_json(silent=True) or {}

    try:
        start = _to_point3d(payload, "start")
        end = _to_point3d(payload, "end")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        wind_speed = float(payload.get("wind_speed") if payload.get("wind_speed") is not None else 8.0)
        wind_direction = float(payload.get("wind_direction") if payload.get("wind_direction") is not None else 90.0)
    except (ValueError, TypeError):
        wind_speed, wind_direction = 8.0, 90.0
        
    vehicle_type = str(payload.get("vehicle_type", "passenger"))

    risk_map = compute_risk_map(OCCUPANCY, wind_speed=wind_speed, wind_direction=wind_direction)
    path = find_path_astar(
        OCCUPANCY, 
        risk_map, 
        start=start, 
        end=end, 
        wind_speed=wind_speed, 
        wind_direction=wind_direction, 
        vehicle_type=vehicle_type
    )

    if path is None:
        return jsonify({"error": "No valid path found"}), 404

    risk_values = [float(risk_map[x, y, z]) for x, y, z in path]
    mean_risk = float(np.mean(risk_values)) if risk_values else 0.0

    return jsonify(
        {
            "start": list(start),
            "end": list(end),
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "vehicle_type": vehicle_type,
            "path": [list(p) for p in path],
            "path_length": len(path),
            "average_risk": mean_risk,
        }
    )


import traceback

@app.errorhandler(500)
def internal_error(error):
    print("--- 500 ERROR DETECTED ---")
    traceback.print_exc()
    return jsonify({"error": "Internal Server Error", "details": str(error)}), 500

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)
