# Project: UAM 3D Risk Visualization System (Prototype)

## 1. Project Overview
This project is a 3D visualization system for Urban Air Mobility (UAM) risk assessment. It uses a Flask-based backend to compute 3D risk maps and find optimal flight paths using A* search, and a Cesium.js frontend for 3D visualization.

- **Goal:** 2주 내 시연 가능한 프로토타입 완성 (완성도 < 동작 우선)
- **Target Region:** 인천 송도동 (V-World 3D 건물 데이터 활용 예정)
- **Core Tech Stack:**
  - **Backend:** Python (Flask, NumPy, Pandas)
  - **Frontend:** Vanilla JS, CesiumJS (via CDN), HTML (Jinja2)
  - **Data Integration:** 3D Map API (Teammate provided)

## 2. Getting Started

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Installation
1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Mac/Linux:
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration (e.g., CESIUM_ION_TOKEN)
   ```

### Running the Application
```bash
python app.py
```
Access the dashboard at `http://127.0.0.1:5000`.

## 3. Directory Structure
- `app.py`: Flask entry point and API definitions.
- `core/`: Core logic modules.
  - `voxel.py`: 3D grid/voxelization logic.
  - `physics.py`: Risk map computation (Venturi/Vortex models).
  - `pathfinding.py`: A* 3D pathfinding algorithm.
  - `llm.py`: Placeholder for LLM-based weight adjustment.
- `static/`: Frontend assets.
  - `js/map.js`: CesiumJS logic for map rendering and API interaction.
- `templates/`: HTML templates.
  - `index.html`: Main dashboard layout.

## 4. AI Agent Directives (행동 규칙)
- **Rule 1 (Mock Data First):** Prioritize using mock or random data for demonstration purposes if real sensors/APIs are unavailable.
- **Rule 2 (No Build Pipeline):** Keep frontend simple with CDNs and Vanilla JS. Avoid complex build tools (Webpack, Vite, etc.).
- **Rule 3 (Prioritize Speed):** Focus on MUST-HAVE features. Avoid over-engineering.
- **Rule 4 (Plan Before Action):** Always propose a plan in a `.md` file before making significant code changes.

## 5. Core Architecture & Logic
- **Voxel Grid:** 10m unit 3D grid division.
- **Risk Model:** Normalizes risk (0-1) based on distance from obstacles and wind factors.
- **Pathfinding:** 3D A* search across 26 directions. Cost function: `Distance + (Risk * Alpha)`.
- **LLM Role:** Dynamically adjusts the `Alpha` weight based on flight conditions (wind, vehicle type).

## 6. APIs
- `GET /`: Serves the main dashboard.
- `GET /api/risk-map`: Returns sparse high-risk voxel data for visualization.
- `POST /api/route`: Returns the optimal path between start and end points.
