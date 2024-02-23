import paho.mqtt.client as mqtt
from utility.db_manager import *
from utility.entity import Node, Measurement
from utility.logger import error, info
from datetime import datetime
import json

TOPICS = ['configuration', 'temperature_humidity_co2', 'frequency_noise', 'weight', 'counter']

class MQTTManager:
    _db_manager = None

    @staticmethod
    def run(db_manager: DBManager, mqtt_broker_ip: str, mqtt_broker_port: int, mqtt_keepalive: int) -> None:
        MQTTManager._db_manager = db_manager

        try:
            client = mqtt.Client()
            client.on_connect = MQTTManager._connect_callback
            client.on_message = MQTTManager._message_callback
            client.connect(host=mqtt_broker_ip, port=mqtt_broker_port, keepalive=mqtt_keepalive)
            client.loop_forever()

            if MQTTManager._db_manager is not None:
                MQTTManager._db_manager.close_connection()
        except OSError:
            error('MQTT broker is unreachable')

    @staticmethod
    def _connect_callback(client, userdata, flags, response_code):
        print(f'Connected with result code {str(response_code)}')
        
        for topic in TOPICS:
            client.subscribe(topic)

    @staticmethod
    def _message_callback(client, userdata, message):
        payload = json.loads(message.payload)

        try:
            if message.topic == 'configuration':
                info(f'Received new configuration from node {payload["i"]}')

                node = MQTTManager._db_manager.get_node(node_id=payload['i'])
                if node is not None:
                    info('Updating node')
                    node._communication_time = payload['s']
                    node._last_communication = datetime.now()
                    MQTTManager._db_manager.update_node(node)
                else:
                    info('Adding new node')
                    node = Node(node_id=payload['i'], node_type=payload['t'], communication_time=payload['s'], last_communication=datetime.now())
                    MQTTManager._db_manager.add_node(node=node)

            elif message.topic == 'temperature_humidity_co2':
                info(f'Received new \'{message.topic}\' measurement from node {payload["i"]}')

                timestamp = datetime.now()
                temperature = Measurement(measurement_type='temperature', value=MQTTManager._convert_to_signed(value=payload['t']), timestamp=timestamp, node_id=payload['i'])
                humidity = Measurement(measurement_type='humidity', value=payload['h'], timestamp=timestamp, node_id=payload['i'])
                co2 = Measurement(measurement_type='co2', value=payload['c'], timestamp=timestamp, node_id=payload['i'])
                MQTTManager._db_manager.add_measurements(measurements=[temperature, humidity, co2])
                MQTTManager._db_manager.update_node_last_communication(node_id=payload['i'])

            elif message.topic == 'frequency_noise':
                info(f'Received new \'{message.topic}\' measurement from node {payload["i"]}')
                    
                timestamp = datetime.now()
                frequency = Measurement(measurement_type='frequency', value=payload['f'], timestamp=timestamp, node_id=payload['i'])
                noise = Measurement(measurement_type='noise', value=payload['n'], timestamp=timestamp, node_id=payload['i'])
                MQTTManager._db_manager.add_measurements(measurements=[frequency, noise])
                MQTTManager._db_manager.update_node_last_communication(node_id=payload['i'])

            elif message.topic == 'weight':
                info(f'Received new \'{message.topic}\' measurement from node {payload["i"]}')

                timestamp = datetime.now() 
                weight = Measurement(measurement_type='weight', value=payload['w'], timestamp=timestamp, node_id=payload['i'])
                MQTTManager._db_manager.add_measurements(measurements=[weight])
                MQTTManager._db_manager.update_node_last_communication(node_id=payload['i'])

            elif message.topic == 'counter':
                info(f'Received new \'{message.topic}\' measurement from node {payload["i"]}')
                    
                timestamp = datetime.now()
                counter_in = Measurement(measurement_type='counter_in', value=payload['in'], timestamp=timestamp, node_id=payload['i'])
                counter_out = Measurement(measurement_type='counter_out', value=payload['o'], timestamp=timestamp, node_id=payload['i'])
                MQTTManager._db_manager.add_measurements(measurements=[counter_in, counter_out])
                MQTTManager._db_manager.update_node_last_communication(node_id=payload['i'])
                
        except DBOperationError as err:
            error(err)

    @staticmethod
    def _convert_to_signed(value: int) -> int:
        if value >= 128:
            value -= 256
        return value