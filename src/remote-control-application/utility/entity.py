from utility.logger import CYAN_COLOR, RED_COLOR, DEFAULT_COLOR
from datetime import datetime

class Area:
    def __init__(self, name: str, city: str, region: str) -> None:
        self._name = name
        self._city = city
        self._region = region

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Area):
            if self._name == other._name and self._city == other._city and self._region == other._region:
                return True
            else:
                return False
        else:
            return False

    def __str__(self) -> str:
        return f'{CYAN_COLOR}name{DEFAULT_COLOR}: {self._name}\t\t{CYAN_COLOR}city{DEFAULT_COLOR}: {self._city}\t\t{CYAN_COLOR}region{DEFAULT_COLOR}: {self._region}'

class Hive:
    def __init__(self, hive_id: int, area_name: str) -> None:
        self._id = hive_id
        self._area_name = area_name

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Hive):
            if self._id == other._id and self._area_name == other._area_name:
                return True
            else:
                return False
        else:
            return False

    def __str__(self) -> str:
        return f'{CYAN_COLOR}hive id{DEFAULT_COLOR}: {self._id}\t\t{CYAN_COLOR}area name{DEFAULT_COLOR}: {self._area_name}'

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
        return '{cyan}node id{default}: {:<15}{cyan}type{default}: {:<10}{cyan}communication time{default}: {:<10}{cyan}last communication{default}: {}'.format(
        self._id, self._type, self._communication_time, self._last_communication,
        cyan=CYAN_COLOR, default=DEFAULT_COLOR
    )
    
class Measurement:
    def __init__(self, measurement_type: str, value: int, timestamp: datetime) -> None:
        self._type = measurement_type
        self._value = value
        self._timestamp = timestamp

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Measurement):
            if self._type == other._type and self._value == other._value and self._timestamp == other._timestamp:
                return True
            else:
                return False
        else:
            return False

    def __str__(self) -> str:
        return f'({self._type}, {self._value}, {self._timestamp})'

class Rule:
    def __init__(self, hive_id: int, polling_time: int, rules: dict = None) -> None:
        self._hive_id = hive_id
        self._polling_time = polling_time

        if rules is None:
            rules = { 
                'temperature_rule': None, 
                'ventilation_rule': { '1': None, '2': None, '3': None, '4': None } 
            }
        self._rules = rules

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Node):
            if self._hive_id == other._hive_id and self._polling_time == other._polling_time and self._rules == other._rules:
                return True
            else:
                return False
        else:
            return False

    def __str__(self) -> str:
        hive_information = f'{CYAN_COLOR}hive id{DEFAULT_COLOR}: {self._hive_id}\t{CYAN_COLOR}polling time (minutes){DEFAULT_COLOR}: {self._polling_time}\n'
        
        if self._rules['temperature_rule'] is None:
            temperature_rule = f'1. {CYAN_COLOR}temperature target{DEFAULT_COLOR}: {RED_COLOR}not defined{DEFAULT_COLOR}\t{CYAN_COLOR}minimum temperature{DEFAULT_COLOR}: {RED_COLOR}not defined{DEFAULT_COLOR}'
        else:
            temperature_rule = f'1. {CYAN_COLOR}temperature target{DEFAULT_COLOR}: {self._rules["temperature_rule"]["target_temperature"]}°C\t\t{CYAN_COLOR}minimum temperature{DEFAULT_COLOR}: {self._rules["temperature_rule"]["min_temperature"]}°C'

        ventilation_rule = ''
        for i in range(1, 5):

            match i:
                case 1:
                    level = 'off'
                case 2:
                    level = 'low'
                case 3:
                    level = 'medium'
                case 4:
                    level = 'high'
            
            if self._rules['ventilation_rule'][f'{i}'] is None:
                ventilation_rule += f'\n{i + 1}. {CYAN_COLOR}ventilation level{DEFAULT_COLOR}: {level}\t\t{CYAN_COLOR}max temperature{DEFAULT_COLOR}: {RED_COLOR}not defined{DEFAULT_COLOR}\t{CYAN_COLOR}max humidity{DEFAULT_COLOR}: {RED_COLOR}not defined{DEFAULT_COLOR}\t{CYAN_COLOR}max co2{DEFAULT_COLOR}: {RED_COLOR}not defined{DEFAULT_COLOR}\t{CYAN_COLOR}and{DEFAULT_COLOR}: {RED_COLOR}not defined{DEFAULT_COLOR}'
            else:
                ventilation_rule += f'\n{i + 1}. {CYAN_COLOR}ventilation level{DEFAULT_COLOR}: {level}\t\t{CYAN_COLOR}max temperature{DEFAULT_COLOR}: {self._rules["ventilation_rule"][f"{i}"]["max_temperature"]}°C\t\t{CYAN_COLOR}max humidity{DEFAULT_COLOR}: {self._rules["ventilation_rule"][f"{i}"]["max_humidity"]}%\t\t{CYAN_COLOR}max co2{DEFAULT_COLOR}: {self._rules["ventilation_rule"][f"{i}"]["max_co2"]}ppm\t{CYAN_COLOR}and{DEFAULT_COLOR}: {self._rules["ventilation_rule"][f"{i}"]["and"]}'

        return hive_information + temperature_rule + ventilation_rule
    
    def has_temperature_rule(self) -> bool:
        return self._rules['temperature_rule'] is not None
    
    def has_ventilation_rule(self) -> bool:
        return self._rules['ventilation_rule']['1'] is not None or self._rules['ventilation_rule']['2'] is not None or \
            self._rules['ventilation_rule']['3'] is not None or self._rules['ventilation_rule']['4'] is not None

    def has_rules(self) -> bool:
        if self.has_temperature_rule() or self.has_ventilation_rule():
            return True
        return False