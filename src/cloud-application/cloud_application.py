from utility.db_manager import *
from utility.coap_manager import CoAPManager
from utility.mqtt_manager import MQTTManager
from utility.logger import info
from threading import Thread

DATABASE_NAME = 'beekeeper'
DATABASE_HOST = 'localhost'
DATABASE_PORT = 3306
DATABASE_USER = 'root'
DATABASE_PASSWORD = 'password'

MQTT_BROKER_IP = 'fd00::1'
MQTT_BROKER_PORT = 1883
MQTT_KEEPALIVE = 60

COAP_SERVER_IP = 'fd00::1'
COAP_SERVER_PORT = 5683
COAP_SERVER_TIMEOUT = 10

if __name__ == '__main__':
    try:
        db = DBManager(name=DATABASE_NAME, host=DATABASE_HOST, port=DATABASE_PORT, user=DATABASE_USER, password=DATABASE_PASSWORD)
        coap_server_worker = Thread(target=CoAPManager.run, args=(db, COAP_SERVER_IP, COAP_SERVER_PORT, COAP_SERVER_TIMEOUT), daemon=False)
        coap_server_worker.start()

        db = DBManager(name=DATABASE_NAME, host=DATABASE_HOST, port=DATABASE_PORT, user=DATABASE_USER, password=DATABASE_PASSWORD)
        mqtt_client_worker = Thread(target=MQTTManager.run, args=(db, MQTT_BROKER_IP, MQTT_BROKER_PORT, MQTT_KEEPALIVE), daemon=False)
        mqtt_client_worker.start()
    except KeyboardInterrupt:
        info('Closing application...')
        exit(0)