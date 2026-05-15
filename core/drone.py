from dataclasses import dataclass, field
from typing import List, Tuple, Optional

@dataclass
class DroneState:
    """
    드론의 상태 정보를 담는 데이터 객체입니다.
    """
    drone_id: str
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    battery: float = 100.0
    status: str = "idle"  # idle, flying, emergency, landed
    current_path: List[Tuple[int, int, int]] = field(default_factory=list)
    speed_mps: float = 30.0
    vehicle_type: str = "passenger"

class DroneManager:
    """
    시스템 내의 여러 드론을 관리하는 매니저 클래스입니다.
    """
    def __init__(self):
        self.drones = {}

    def register_drone(self, drone_id: str, vehicle_type: str = "passenger") -> DroneState:
        drone = DroneState(drone_id=drone_id, vehicle_type=vehicle_type)
        self.drones[drone_id] = drone
        return drone

    def assign_path(self, drone_id: str, path: List[Tuple[int, int, int]]):
        if drone_id in self.drones:
            self.drones[drone_id].current_path = path
            self.drones[drone_id].status = "flying"
            if path:
                self.drones[drone_id].position = tuple(path[0])

    def update_position(self, drone_id: str, position: Tuple[float, float, float]):
        if drone_id in self.drones:
            self.drones[drone_id].position = position

    def get_status(self, drone_id: str) -> Optional[DroneState]:
        return self.drones.get(drone_id)

    def list_all_drones(self) -> List[DroneState]:
        return list(self.drones.values())
