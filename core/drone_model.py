import pyvista as pv
import numpy as np

class Drone3DModel:
    """
    PyVista를 사용하여 드론(UAM) 기체를 3D로 모델링하고 시각화하는 클래스입니다.
    """
    def __init__(self):
        self.plotter = pv.Plotter()
        self.meshes = []

    def create_body(self, length=1.0, width=0.4, height=0.2):
        """중심 본체(Fuselage)를 생성합니다."""
        body = pv.Cube(center=(0, 0, 0), x_length=length, y_length=width, z_length=height)
        self.meshes.append({'mesh': body, 'color': 'grey', 'label': 'Body'})
        return body

    def create_arm(self, arm_length=0.8, angle_deg=45):
        """프로펠러를 지지하는 암(Arm)을 생성합니다."""
        angle_rad = np.radians(angle_deg)
        x = np.cos(angle_rad) * arm_length / 2
        y = np.sin(angle_rad) * arm_length / 2
        
        arm = pv.Cylinder(center=(x, y, 0), direction=(np.cos(angle_rad), np.sin(angle_rad), 0), 
                          radius=0.03, height=arm_length)
        return arm

    def create_rotor(self, center, radius=0.3):
        """프로펠러(Rotor)를 생성합니다."""
        rotor = pv.Disc(center=center, inner=0, outer=radius, normal=(0, 0, 1))
        self.meshes.append({'mesh': rotor, 'color': 'blue', 'label': 'Rotor'})
        return rotor

    def build_quadcopter(self):
        """4개의 로터를 가진 쿼드코프터 모델을 조립합니다."""
        self.meshes = [] # 초기화
        
        # 1. 본체
        self.create_body()

        # 2. 암 및 로터 4개 배치
        arm_angles = [45, 135, 225, 315]
        arm_length = 0.8
        
        for angle in arm_angles:
            # 암 생성 및 추가
            arm = self.create_arm(arm_length=arm_length, angle_deg=angle)
            self.meshes.append({'mesh': arm, 'color': 'black', 'label': 'Arm'})
            
            # 로터 위치 계산 (암의 끝부분)
            rad = np.radians(angle)
            rotor_pos = (np.cos(rad) * arm_length, np.sin(rad) * arm_length, 0.05)
            self.create_rotor(center=rotor_pos)

    def show(self):
        """모델을 화면에 출력합니다."""
        for item in self.meshes:
            self.plotter.add_mesh(item['mesh'], color=item['color'], show_edges=True)
        
        self.plotter.add_axes()
        self.plotter.set_background("white")
        self.plotter.show(title="UAM Drone 3D Model (PyVista)")

    def export_gltf(self, filename="static/models/drone_model.gltf"):
        """모델을 GLTF 파일로 내보냅니다 (CesiumJS 호환)."""
        # Plotter에 모든 메시 추가
        self.plotter.clear()
        for item in self.meshes:
            self.plotter.add_mesh(item['mesh'], color=item['color'])
        
        # GLTF 내보내기
        self.plotter.export_gltf(filename)
        print(f"Model exported to {filename}")

if __name__ == "__main__":
    # 실행 예시
    drone_model = Drone3DModel()
    drone_model.build_quadcopter()
    
    import os
    os.makedirs("static/models", exist_ok=True)
    
    print("3D 모델을 생성 중...")
    drone_model.export_gltf("static/models/drone_model.gltf")
