/**
 * Drone class for CesiumJS visualization.
 * Handles drone animation along a given path.
 */
class Drone {
    constructor(viewer, options = {}) {
        this.viewer = viewer;
        this.id = options.id || 'uam-drone-' + Math.random().toString(36).substr(2, 9);
        this.entity = null;
        this.path = [];
        this.speed = options.speed || 30.0;
        this.modelUri = options.modelUri || '/static/models/drone_model.gltf';
        
        // 드론 상태 정보
        this.battery = 100.0;
        this.modelName = options.modelName || 'PyVista-UAM';
        this.status = 'Ready'; // Ready, Flying, Returning, Landed
        
        this.isFlying = false;
        this.originalPositions = [];
    }

    /**
     * Set path but don't start animation yet.
     * Place drone at the start position.
     */
    setPath(positions) {
        if (!positions || positions.length < 2) return;
        this.originalPositions = positions;
        this.path = positions;
        this.status = 'Ready';
        this.isFlying = false;
        this._updateEntityAtPosition(positions[0]);
    }

    /**
     * Update or create entity at a specific static position.
     */
    _updateEntityAtPosition(position) {
        this.clear();
        this.entity = this.viewer.entities.add({
            id: this.id,
            position: position,
            model: {
                uri: this.modelUri,
                minimumPixelSize: 128, // 크기 상향
                maximumScale: 20000
            },
            description: this._generateDescription(),
            // 모델 로드 실패 시에도 보일 수 있도록 포인트와 레이블 추가
            point: {
                pixelSize: 20,
                color: Cesium.Color.YELLOW,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 2,
                disableDepthTestDistance: Number.POSITIVE_INFINITY
            },
            label: {
                text: this.modelName,
                font: '14pt sans-serif',
                verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                pixelOffset: new Cesium.Cartesian2(0, -20),
                disableDepthTestDistance: Number.POSITIVE_INFINITY
            }
        });
    }

    _generateDescription() {
        return `
            <div style="padding: 10px; background: rgba(0,0,0,0.8); color: white; border-radius: 5px;">
                <h3 style="margin: 0 0 5px 0;">${this.modelName}</h3>
                <p><b>Status:</b> ${this.status}</p>
                <p><b>Battery:</b> ${this.battery.toFixed(1)}%</p>
                <p><b>Speed:</b> ${this.speed} m/s</p>
            </div>
        `;
    }

    /**
     * Start the actual flight animation.
     */
    startFlight() {
        if (!this.path || this.path.length < 2) return;
        this.isFlying = true;
        this.status = 'Flying';
        this._createAnimation(this.path);
    }

    _createAnimation(positions) {
        // 기존 리스너가 있다면 제거
        if (this._arrivalListener) {
            this.viewer.clock.onTick.removeEventListener(this._arrivalListener);
            this._arrivalListener = null;
        }

        const start = Cesium.JulianDate.fromDate(new Date());
        const property = new Cesium.SampledPositionProperty();
        
        // 보간 설정 (부드러운 이동)
        property.setInterpolationOptions({
            interpolationDegree: 2,
            interpolationAlgorithm: Cesium.HermitePolynomialApproximation
        });

        let totalTimeSeconds = 0;
        for (let i = 0; i < positions.length; i++) {
            if (i > 0) {
                const distance = Cesium.Cartesian3.distance(positions[i - 1], positions[i]);
                totalTimeSeconds += distance / this.speed;
            }
            const time = Cesium.JulianDate.addSeconds(start, totalTimeSeconds, new Cesium.JulianDate());
            property.addSample(time, positions[i]);
        }

        const stop = Cesium.JulianDate.addSeconds(start, totalTimeSeconds, new Cesium.JulianDate());

        // 클락 설정 강제 동기화
        this.viewer.clock.startTime = start.clone();
        this.viewer.clock.stopTime = stop.clone();
        this.viewer.clock.currentTime = start.clone();
        this.viewer.clock.multiplier = 1.0;
        this.viewer.clock.clockRange = Cesium.ClockRange.CLAMPED;
        this.viewer.clock.shouldAnimate = true;

        this.clear();
        this.entity = this.viewer.entities.add({
            id: this.id,
            availability: new Cesium.TimeIntervalCollection([
                new Cesium.TimeInterval({ start: start, stop: stop })
            ]),
            position: property,
            orientation: new Cesium.VelocityOrientationProperty(property),
            model: { 
                uri: this.modelUri, 
                minimumPixelSize: 128,
                maximumScale: 20000
            },
            description: this._generateDescription(),
            point: {
                pixelSize: 20,
                color: Cesium.Color.YELLOW,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 2,
                disableDepthTestDistance: Number.POSITIVE_INFINITY
            },
            label: {
                text: this.modelName,
                font: '14pt sans-serif',
                verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                pixelOffset: new Cesium.Cartesian2(0, -20),
                disableDepthTestDistance: Number.POSITIVE_INFINITY
            },
            path: {
                resolution: 1,
                material: new Cesium.PolylineGlowMaterialProperty({ color: Cesium.Color.YELLOW }),
                width: 10
            }
        });

        // 도착 리스너 등록
        this._arrivalListener = () => {
            if (Cesium.JulianDate.compare(this.viewer.clock.currentTime, stop) >= 0) {
                this.viewer.clock.onTick.removeEventListener(this._arrivalListener);
                this._arrivalListener = null;
                this.onArrival();
            }
        };
        this.viewer.clock.onTick.addEventListener(this._arrivalListener);
    }

    onArrival() {
        const isReturning = this.status === 'Returning';
        
        if (isReturning) {
            this.status = 'Ready (At Origin)';
            this._updateEntityAtPosition(this.originalPositions[0]);
        } else {
            this.status = 'Arrived';
            const lastPosition = this.path[this.path.length - 1];
            this._updateEntityAtPosition(lastPosition);
        }

        this.battery -= 5.0;
        if (this.battery < 0) this.battery = 0;
        this.isFlying = false;

        // 도착 이벤트 알림
        if (typeof window.onDroneArrived === 'function') {
            window.onDroneArrived();
        }
    }

    /**
     * Return to the origin point instantly without animation.
     */
    returnToOrigin() {
        if (!this.originalPositions || this.originalPositions.length < 2) return;
        
        // 진행 중인 애니메이션 및 리스너 중단
        if (this._arrivalListener) {
            this.viewer.clock.onTick.removeEventListener(this._arrivalListener);
            this._arrivalListener = null;
        }
        this.viewer.clock.shouldAnimate = false;

        this.status = 'Ready (At Origin)';
        this.isFlying = false;
        
        // 즉시 출발지 위치로 엔티티 업데이트
        this._updateEntityAtPosition(this.originalPositions[0]);

        // UI 업데이트 알림
        if (typeof window.onDroneArrived === 'function') {
            window.onDroneArrived();
        }
    }

    clear() {
        if (this.entity) {
            this.viewer.entities.remove(this.entity);
            this.entity = null;
        }
    }
}
