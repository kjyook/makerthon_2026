# UAM 3D Risk Visualization System (Prototype)

인천 송도 지역을 대상으로 한 UAM(Urban Air Mobility) 3D 위험도 시각화 및 경로 최적화 프로토타입입니다.

## 🚀 시작하기

### 1. 환경 설정

Python 3.8 이상의 환경이 필요합니다. 가상환경 사용을 권장합니다.

```bash
# 가상환경 생성 및 활성화
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 필요한 설정을 입력하세요.

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

- `CESIUM_ION_TOKEN`: Cesium Ion 데이터를 사용할 경우 필요합니다.

### 3. 애플리케이션 실행

```bash
python app.py
```

서버가 실행되면 브라우저에서 `http://127.0.0.1:5000`에 접속하세요.

## 🛠 기술 스택

- **Backend:** Flask, NumPy, Pandas (Voxel 연산 및 A\* 알고리즘)
- **Frontend:** Vanilla JS, CesiumJS (3D Visualization)
- **Data:** V-World 3D 건물 데이터 및 커스텀 위험도 모델

## 📂 프로젝트 구조

- `app.py`: Flask 엔트리포인트 및 API 엔드포인트
- `core/`: 핵심 알고리즘 (Voxel 생성, 물리 모델, 경로 탐색 등)
- `static/`: 프론트엔드 자산 (JS, CSS)
- `templates/`: HTML 템플릿
- `GEMINI.md`: AI 에이전트용 상세 프로젝트 컨텍스트

## 📡 주요 API

- `GET /api/risk-map`: 풍속/풍향에 따른 위험도 격자 데이터 반환
- `POST /api/route`: 출발/도착지 기반 최적 경로 계산

## 🤝 협업 가이드

- 3D 맵 데이터 통합은 `core/` 모듈의 인터페이스를 활용하세요.
- 프론트엔드 수정 시 `static/js/map.js`를 수정하세요.
- 새로운 기능 추가 전 `TODO.md`를 확인해 주세요.
- AI 에이전트는 `GEMINI.md`의 행동 규칙을 준수해야 합니다.
- AI 에이컨트는 plan-before-action 원칙에 따라 주요 변경 전에 항상 계획을 제안해야 합니다.
