const statusEl = document.getElementById('status');
const startInput = document.getElementById('start');
const endInput = document.getElementById('end');
const windSpeedInput = document.getElementById('windSpeed');
const windDirectionInput = document.getElementById('windDirection');

const viewer = new Cesium.Viewer('viewer', {
  animation: false,
  timeline: false,
  geocoder: false,
  sceneModePicker: false,
  baseLayerPicker: false,
});

viewer.scene.globe.depthTestAgainstTerrain = false;
viewer.camera.flyTo({
  destination: Cesium.Cartesian3.fromDegrees(126.64, 37.39, 6000),
  duration: 0,
});

let routeEntity = null;
let riskEntities = [];

function parsePoint(text) {
  const parts = text.split(',').map((v) => Number(v.trim()));
  if (parts.length !== 3 || parts.some((n) => Number.isNaN(n))) {
    throw new Error('좌표 형식은 x,y,z 입니다.');
  }
  return parts;
}

function voxelToLonLatAlt([x, y, z]) {
  const baseLon = 126.62;
  const baseLat = 37.37;
  const step = 0.0012;
  return [baseLon + x * step, baseLat + y * step, 40 + z * 60];
}

function clearRisk() {
  riskEntities.forEach((e) => viewer.entities.remove(e));
  riskEntities = [];
}

async function loadRiskMap() {
  const wind_speed = Number(windSpeedInput.value);
  const wind_direction = Number(windDirectionInput.value);
  
  const url = `/api/risk-map?wind_speed=${wind_speed}&wind_direction=${wind_direction}&threshold=0.7`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error('Risk map API 요청 실패');
  }

  const data = await res.json();
  clearRisk();

  for (const p of data.points) {
    const [lon, lat, alt] = voxelToLonLatAlt([p.x, p.y, p.z]);
    const entity = viewer.entities.add({
      position: Cesium.Cartesian3.fromDegrees(lon, lat, alt),
      box: {
        dimensions: new Cesium.Cartesian3(40, 40, 40),
        material: Cesium.Color.fromCssColorString('#d06f2f').withAlpha(
          Math.min(0.95, p.risk),
        ),
        outline: false,
      },
    });
    riskEntities.push(entity);
  }

  statusEl.textContent = `Risk voxels: ${data.points.length}, wind=${wind_speed}, dir=${wind_direction}`;
}

async function findRoute() {
  const payload = {
    start: parsePoint(startInput.value),
    end: parsePoint(endInput.value),
    wind_speed: Number(windSpeedInput.value),
    wind_direction: Number(windDirectionInput.value),
    vehicle_type: 'passenger',
  };

  const res = await fetch('/api/route', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || 'Route API 요청 실패');
  }

  if (routeEntity) {
    viewer.entities.remove(routeEntity);
    routeEntity = null;
  }

  const positions = [];
  for (const point of data.path) {
    const [lon, lat, alt] = voxelToLonLatAlt(point);
    positions.push(Cesium.Cartesian3.fromDegrees(lon, lat, alt));
  }

  routeEntity = viewer.entities.add({
    polyline: {
      positions,
      width: 5,
      material: Cesium.Color.fromCssColorString('#2d6a4f'),
    },
  });

  viewer.zoomTo(routeEntity);
  statusEl.textContent = `Path length=${data.path_length}, avg risk=${data.average_risk.toFixed(3)}, alpha=${data.alpha.toFixed(2)}`;
}

document.getElementById('btnRisk').addEventListener('click', async () => {
  try {
    await loadRiskMap();
  } catch (err) {
    statusEl.textContent = err.message;
  }
});

document.getElementById('btnRoute').addEventListener('click', async () => {
  try {
    await findRoute();
  } catch (err) {
    statusEl.textContent = err.message;
  }
});

loadRiskMap().catch((err) => {
  statusEl.textContent = err.message;
});
