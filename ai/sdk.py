import json
from tabnanny import check
from typing import Callable, Dict, List, Optional, Tuple
from math import sqrt

def complex_from_json(info: Dict) -> complex:
    return info["re"] + 1j * info["im"]

def complex_to_json(z: complex) -> Dict:
    return {"re": z.real, "im": z.imag}

class Circle:

    @staticmethod
    def from_json(info: Dict):
        return Circle(info["radius"])

    def __init__(self, radius: float):
        self.radius = radius

class CheckpointInfo:

    @staticmethod
    def from_json(info: Dict):
        return CheckpointInfo(info["checkpointIndex"], info["time"])

    def __init__(self, index: int, time: int):
        self.index = index
        self.time = time

class Car:

    @staticmethod
    def from_json(info: Dict):
        return Car(
            info["id"],
            info["time"],
            info["teamId"],
            complex_from_json(info["pos"]),
            complex_from_json(info["speed"]),
            info["rotation"],
            info["mass"],
            Circle.from_json(info["shape"]),
            [CheckpointInfo.from_json(checkpoint_info_info) for checkpoint_info_info in info["passedCheckpoints"]],
            info["boostUsed"]
        )

    def __init__(
            self,
            car_id: int, time: int, team_id: int, pos: complex,
            speed: complex, rotation: float, mass: float,
            shape: Circle,
            passed_checkpoints: List[CheckpointInfo],
            boost_used: bool
    ):
        self.id = car_id
        self.time = time
        self.team_id = team_id
        self.pos = pos
        self.speed = speed
        self.rotation = rotation
        self.mass = mass
        self.shape = shape
        self.passed_checkpoints: List["CheckpointInfo"] = passed_checkpoints
        self.boost_used = boost_used

    def next_checkpoint_index(self, number_of_checkpoints: int) -> int:
        return (self.passed_checkpoints[0].index + 1) % number_of_checkpoints

    def next_next_checkpoint_index(self, number_of_checkpoints: int) -> int:
        return (self.passed_checkpoints[0].index + 2) % number_of_checkpoints

    def next_checkpoint(self, game_state: "GameState") -> "Checkpoint":
        index = self.next_checkpoint_index(game_state.number_of_checkpoints)
        return next(checkpoint for checkpoint in game_state.checkpoints if checkpoint.checkpoint_index == index)

    def next_next_checkpoint(self, game_state: "GameState") -> "Checkpoint":
        index = self.next_next_checkpoint_index(game_state.number_of_checkpoints)
        return next(checkpoint for checkpoint in game_state.checkpoints if checkpoint.checkpoint_index == index)

    def distance_to_next_checkpoint(self, game_state: "GameState") -> int:
        final_pos = self.next_checkpoint(game_state).pos
        current_pos = self.pos
        return game_state.distance(current_pos, final_pos)

    def get_closest_next_checkpoint(self, game_state: "GameState") -> "Checkpoint":
        closest_checkpoint = self.next_next_checkpoint(game_state)
        current_pos = self.pos
        for checkpoint in game_state.checkpoints:
            if checkpoint.checkpoint_index != self.next_checkpoint_index(game_state.number_of_checkpoints) and game_state.distance(current_pos,closest_checkpoint.pos) > game_state.distance(current_pos, checkpoint.pos):
                closest_checkpoint = checkpoint
        return checkpoint


class Checkpoint:

    @staticmethod
    def from_json(info: Dict):
        return Checkpoint(info["id"], info["time"], complex_from_json(info["pos"]), Circle.from_json(info["shape"]), info["checkpointIndex"])

    def __init__(self, checkpoint_id: int, time: int, pos: complex, shape: Circle, index: int):
        self.id = checkpoint_id
        self.time = time
        self.pos = pos
        self.shape = shape
        self.checkpoint_index = index

class GameState:

    @staticmethod
    def from_json(info: Dict):
        return GameState(info["time"], info.get("maybeStartedTime"),
                         info.get("maybeEndedTime"),
                         [Car.from_json(car_info) for car_info in info.get("cars", [])],
                         [Checkpoint.from_json(checkpoint_info) for checkpoint_info in info.get("checkpoints", [])],
                         info.get("crashedTeams"), info["totalNumberOfLaps"])

    def __init__(
            self,
            time: int,
            start_time: Optional[int],
            end_time: Optional[int],
            cars: List[Car],
            checkpoints: List[Checkpoint],
            crashed_teams: List[Tuple[int, bool]],
            total_number_of_laps: int
    ):
        self.time = time
        self.start_time = start_time
        self.end_time = end_time
        self.cars = cars
        self.checkpoints = checkpoints
        self.crashed_teams = crashed_teams
        self.total_number_of_laps = total_number_of_laps

    @property
    def is_started(self) -> bool:
        return self.start_time is not None

    @property
    def number_of_checkpoints(self) -> int:
        return len(self.checkpoints)

    def get_opponent_cars(self, team_id : int) -> List[Car]:
        return [car for car in self.cars if car.team_id != team_id]

    def get_lightest_car(self, team_id : int) -> Car:
        opponent_car = self.get_opponent_cars(1 - team_id)
        return opponent_car[1] if opponent_car[0].mass > opponent_car[1].mass else opponent_car[0]

    def get_heaviest_car(self, team_id : int) -> Car:
        opponent_car = self.get_opponent_cars(1 - team_id)
        return opponent_car[0] if opponent_car[0].mass > opponent_car[1].mass else opponent_car[1]
    
    def distance(self, source_pos : int, target_pos : int) -> int:
        return int(sqrt((source_pos.real - target_pos.real)**2 + (source_pos.imag - target_pos.imag)**2))


class PlayerOrder:

    def __init__(self, type_name: str):
        self.type_name = "com.b12.gamerunning.PlayerOrder$" + type_name

    def to_json(self):
        raise NotImplementedError()

    @property
    def full_json(self):
        return {
            "type": self.type_name,
            "info": self.to_json()
        }

class LoggingOrder(PlayerOrder):

    def __init__(self, message: str, level: str, order: PlayerOrder):
        super().__init__("LoggingOrder")
        self.message = message
        self.level = level
        self.order = order

    def to_json(self):
        return {
            "message": self.message,
            "logLevel": self.level,
            "order": self.order.full_json
        }

class Pass(PlayerOrder):

    def __init__(self, team_id: int):
        super().__init__("Pass")
        self.team_id = team_id

    def to_json(self):
        return {
            "teamId": self.team_id
        }

class ApplyForce(PlayerOrder):

    def __init__(self, car_id: int, team_id: int, angle: float, power: int):
        super().__init__("ApplyForce")
        self.car_id = car_id
        self.team_id = team_id
        self.angle = angle
        self.power = power
        if not type(self.power) == int:
            raise ValueError(f"Power must be integer, got {self.power} ({type(self.power)})")

    def to_json(self):
        return {
            "carId": self.car_id,
            "teamId": self.team_id,
            "forceAngle": self.angle,
            "power": self.power
        }

class ForceTowards(PlayerOrder):

    def __init__(self, car_id: int, team_id: int, target_position: complex, power: int):
        super().__init__("ForceTowards")
        self.car_id = car_id
        self.team_id = team_id
        self.target_position = target_position
        self.power = power
        if not type(self.power) == int:
            raise ValueError(f"Power must be integer, got {self.power} ({type(self.power)})")

    def to_json(self):
        return {
            "carId": self.car_id,
            "teamId": self.team_id,
            "targetPosition": complex_to_json(self.target_position),
            "power": self.power
        }

class UseBoost(PlayerOrder):

    def __init__(self, car_id: int, team_id: int):
        super().__init__("UseBoost")
        self.car_id = car_id
        self.team_id = team_id

    def to_json(self):
        return {
            "carId": self.car_id,
            "teamId": self.team_id
        }

class Crash(PlayerOrder):
    def __init__(self, team_id: int, reason: str):
        super().__init__("Crash")
        self.team_id = team_id
        self.reason = reason

    def to_json(self):
        return {
            "teamId": self.team_id,
            "reason": self.reason
        }

class OrderForEachCar(PlayerOrder):

    def __init__(self, order_1: PlayerOrder, order_2: PlayerOrder):
        super().__init__("OrderForEachCar")
        self.order_1 = order_1
        self.order_2 = order_2

    def to_json(self):
        return {
            "car1Order": self.order_1.full_json,
            "car2Order": self.order_2.full_json
        }

class SetCarMasses(PlayerOrder):

    def __init__(self, team_id: int, car1_id: int, car2_id: int, car1_mass: int, car2_mass: int):
        self.team_id = team_id
        self.car1_id = car1_id
        self.car2_id = car2_id
        self.car1_mass = car1_mass
        self.car2_mass = car2_mass
        super().__init__("SetCarMasses")

    def to_json(self):
        return {
            "teamId": self.team_id,
            "car1Id": self.car1_id,
            "car1Mass": self.car1_mass,
            "car2Id": self.car2_id,
            "car2Mass": self.car2_mass
        }

class Logger:

    def __init__(self):
        self.lines = []

    def info(self, message: str):
        self.lines.append({"message": message, "level": "Info"})

    def error(self, message: str):
        self.lines.append({"message": message, "level": "Error"})

    def order(self, order: PlayerOrder) -> LoggingOrder:
        final_order = order
        for message_info in self.lines:
            final_order = LoggingOrder(message_info["message"], message_info["level"], final_order)
        return final_order

def _send_order(log: Logger, order: PlayerOrder):
    print(json.dumps(log.order(order).full_json))


class Runner:

    def __init__(self, team_id: int, game_loop: Callable[[GameState, int, Logger], PlayerOrder]):
        self.team_id = team_id

        self.game_loop = game_loop

    def run(self):
        while True:
            raw_input = json.loads(input())
            log = Logger()
            game_state = GameState.from_json(raw_input["gameState"])
            time = raw_input["time"]

            order = self.game_loop(game_state, time, log)

            _send_order(log, order)
