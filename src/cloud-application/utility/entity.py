from datetime import datetime

class Node:
    def __init__(self, node_id: str, node_type: str, communication_time: int, last_communication: datetime, hive_id: int = None) -> None:
        self._id = node_id
        self._type = node_type
        self._communication_time = communication_time
        self._last_communication = last_communication
        self._hive_id = hive_id

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Node):
            if self._id == other._id and self._type == other._type and \
            self._communication_time == other._communication_time and self._last_communication == other._last_communication and \
                self._hive_id == other._hive_id:
                return True
            else:
                return False
        else:
            return False

    def __str__(self) -> str:
        return f'({self._id}, {self._type}, {self._communication_time}, {self._last_communication}, {self._hive_id})'

class Measurement:
    def __init__(self, measurement_type: str, value: int, timestamp: datetime, node_id: str) -> None:
        self._type = measurement_type
        self._value = value
        self._timestamp = timestamp
        self._node_id = node_id

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Measurement):
            if self._type == other._type and self._value == other._value and \
                self._timestamp == other._timestamp and self._node_id == other._node_id:
                return True
            else:
                return False
        else:
            return False

    def __str__(self) -> str:
        return f'({self._type}, {self._value}, {self._timestamp}, {self._node_id})'