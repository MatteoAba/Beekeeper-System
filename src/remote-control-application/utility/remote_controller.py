from utility.event_manager import EventManager
from utility.db_manager import DBManager
from utility.coap_client import CoAPClient
from utility.entity import Node
from utility.logger import debug_error, debug_warning
import threading

class RemoteController:
    _polling_time_thread = None
    _db_manager = None
    _db_manager_lock = None

    @staticmethod
    def init(db_manager: DBManager, db_manager_lock: threading.Lock) -> None:
        RemoteController._db_manager = db_manager
        RemoteController._db_manager_lock = db_manager_lock

    @staticmethod
    def run() -> None:
        with RemoteController._db_manager_lock:
            rules = RemoteController._db_manager.get_rules()
        
        if rules:
            for rule in rules:
                if rule and rule.has_rules():
                    EventManager.add_event(hive_id=rule._hive_id, polling_time=rule._polling_time)
        
        if not EventManager.is_empty_event_queue():
            RemoteController.resume_event_queue_timer()
    
    @staticmethod
    def stop() -> None:
        if RemoteController.is_set_polling_time_thread():
            RemoteController._polling_time_thread.cancel()

    @staticmethod
    def is_set_polling_time_thread() -> bool:
        return RemoteController._polling_time_thread is not None
    
    @staticmethod
    def unset_polling_time_thread() -> None:
        RemoteController._polling_time_thread = None

    @staticmethod
    def update_event_queue(hive_id: int, polling_time: int, update_type: str, hives_to_remove: list = None) -> int:
        RemoteController._polling_time_thread.cancel()
        elapsed_seconds = EventManager.stop_waiting_time_counter()

        match update_type:
            case 'update':
                EventManager.update_event(hive_id=hive_id, new_polling_time=polling_time)
            case 'remove':
                if hives_to_remove:
                    for hive in hives_to_remove:
                        EventManager.remove_event(hive_id=hive._id)
                else:
                    EventManager.remove_event(hive_id=hive_id)
            case _:
                debug_error('Update type not valid')
        return elapsed_seconds
    
    @staticmethod
    def _get_node_type(nodes: list, node_type: str) -> Node:
        for node in nodes:
            if node._type == node_type:
                return node
        return None

    @staticmethod
    def advance_event_queue_time(elapsed_seconds: int) -> None:
        expired_events = EventManager.advance_time(elapsed_seconds=elapsed_seconds)
        for hive_id in expired_events:
            with RemoteController._db_manager_lock:
                rule = RemoteController._db_manager.get_rule(hive_id=hive_id)
                if not rule or not rule.has_rules():
                    continue
                
                nodes = RemoteController._db_manager.get_nodes(hive_id=hive_id)
                if nodes:
                    temperature_sensor = RemoteController._get_node_type(nodes=nodes, node_type='thc')
                    
                    # Check if temperature rule is defined
                    if rule.has_temperature_rule():
                        temperature_actuator = RemoteController._get_node_type(nodes=nodes, node_type='ta')
                        
                        # Check if temperature actuator and the relative sensors are available
                        if temperature_actuator and temperature_sensor:
                            # Search for the last available sensor measurements
                            measurements = RemoteController._db_manager.get_measurements(node_id=temperature_sensor._id, measurement_types=['temperature'])
                            if not measurements:
                                debug_warning(f'No measurement found for sensor {temperature_sensor._id}')
                            else:
                                # Get the actuator information to send the CoAP request
                                actuator_information = RemoteController._db_manager.get_actuator_information(node_id=temperature_actuator._id)
                                payload = {'t': None}

                                # Check if the rule is triggered
                                if measurements[0]._value < rule._rules['temperature_rule']['min_temperature']:
                                    payload['t'] = rule._rules['temperature_rule']['target_temperature']
                                elif measurements[0]._value >= rule._rules['temperature_rule']['target_temperature']:
                                    payload['t'] = 1
                                
                                if not payload['t']:
                                    debug_warning('No handled rule')
                                    payload['t'] = 1

                                # Check if the actuator must be updated
                                if actuator_information['state'] != payload['t']:
                                    debug_warning(f'Temperature actuator new state: {payload["t"]} (IP: {actuator_information["coap_ip"]})')
                                    
                                    # Create and push the CoAP message to the CoAP thread
                                    coap_message = {
                                        'actuator_node_id': temperature_actuator._id,
                                        'resource': '/temperature',
                                        'coap_ip': actuator_information['coap_ip'],
                                        'payload': payload
                                    }
                                    CoAPClient.push_coap_message(coap_message=coap_message)
                        else:
                            debug_warning('No temperature actuator or temperature sensor found')

                    # Check if a ventilation rule is defined
                    if rule.has_ventilation_rule():
                        ventilation_actuator = RemoteController._get_node_type(nodes=nodes, node_type='va')
                        
                        # Check if ventilation actuator and the relative sensors are available
                        if ventilation_actuator and temperature_sensor:
                            # Search for the last available sensor measurements
                            measurements = RemoteController._db_manager.get_measurements(node_id=temperature_sensor._id, measurement_types=['temperature', 'humidity', 'co2'])
                            if not measurements:
                                debug_warning(f'No measurement found for sensor {temperature_sensor._id}')
                            elif len(measurements) < 3:
                                debug_warning(f'Missing measurements for sensor {temperature_sensor._id}')
                            else:
                                # Get the actuator information to send the CoAP request
                                actuator_information = RemoteController._db_manager.get_actuator_information(node_id=ventilation_actuator._id)
                                payload = {'v': None}

                                # Check if one of the rules is triggered
                                for i in range(4, 0, -1):
                                    current_rule = rule._rules['ventilation_rule'][f'{i}']
                                    if current_rule:
                                        is_and = current_rule['and'] == 1

                                        if i != 1:
                                            if is_and:
                                                # AND rule
                                                if measurements[0]._value > current_rule['max_co2'] and measurements[1]._value > current_rule['max_humidity'] and \
                                                    measurements[2]._value > current_rule['max_temperature']:
                                                    payload['v'] = i
                                                    break
                                            else:
                                                # OR rule
                                                if measurements[0]._value > current_rule['max_co2'] or measurements[1]._value > current_rule['max_humidity'] or \
                                                    measurements[2]._value > current_rule['max_temperature']:
                                                    payload['v'] = i
                                                    break
                                        else:
                                            if measurements[0]._value < current_rule['max_co2'] or measurements[1]._value < current_rule['max_humidity'] or \
                                                measurements[2]._value < current_rule['max_temperature']:
                                                payload['v'] = i
                                 
                                if not payload['v']:
                                    debug_warning('No handled rule')
                                    payload['v'] = 1
                                
                                # Check if the actuator must be updated
                                if actuator_information['state'] != payload['v']:
                                    # Create and push the CoAP message to the CoAP thread
                                    coap_message = {
                                        'actuator_node_id': ventilation_actuator._id,
                                        'resource': '/ventilation',
                                        'coap_ip': actuator_information['coap_ip'],
                                        'payload': payload
                                    }
                                    CoAPClient.push_coap_message(coap_message=coap_message)                                                 
                        else:
                            debug_warning('No ventilation actuator or temperature sensor found')

                EventManager.add_event(hive_id=rule._hive_id, polling_time=rule._polling_time)
                
    @staticmethod
    def start_event_queue_timer(hive_id: int, polling_time: int) -> None:
        EventManager.add_event(hive_id=hive_id, polling_time=polling_time)
        next_remaining_time = EventManager.get_next_remaining_time()
        RemoteController._polling_time_thread = threading.Timer(interval=next_remaining_time, function=RemoteController.callback, args=(next_remaining_time,))
        EventManager.start_waiting_time_counter()
        RemoteController._polling_time_thread.start()

    @staticmethod
    def resume_event_queue_timer():
        next_remaining_time = EventManager.get_next_remaining_time()
        RemoteController._polling_time_thread = threading.Timer(interval=next_remaining_time, function=RemoteController.callback, args=(next_remaining_time,))
        EventManager.start_waiting_time_counter()
        RemoteController._polling_time_thread.start()

    @staticmethod
    def callback(next_remaining_time: int) -> None:
        RemoteController.advance_event_queue_time(elapsed_seconds=next_remaining_time)
        RemoteController.resume_event_queue_timer()