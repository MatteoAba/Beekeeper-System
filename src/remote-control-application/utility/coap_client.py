from coapthon.client.helperclient import HelperClient
from coapthon.utils import parse_uri
from coapthon import defines
from utility.db_manager import DBManager
from utility.logger import debug_error, debug_warning
import threading
import queue
import json
from datetime import datetime

COAP_PORT = 5683
COAP_REQUEST_TIMEOUT = 5
MAX_FAILED_KEEPALIVE = 3

class CoAPClient:
    _coap_message_queue = None
    _db_manager = None
    _db_manager_lock = None

    @staticmethod
    def init(db_manager: DBManager, db_manager_lock: threading.Lock) -> None:
        CoAPClient._coap_message_queue = queue.Queue()
        CoAPClient._db_manager = db_manager
        CoAPClient._db_manager_lock = db_manager_lock

    @staticmethod
    def run() -> None:
        while(True):
            # Read CoAP message from the queue
            coap_message = CoAPClient._coap_message_queue.get(block=True)
            
            # Send message to the actuator
            client = HelperClient(server=(coap_message['coap_ip'], COAP_PORT))
            content_type = {'content_type': defines.Content_types["application/json"]}
            response = client.put(coap_message['resource'], json.dumps(coap_message['payload']), None, COAP_REQUEST_TIMEOUT, **content_type)
            
            if response:
                if response.code == defines.Codes.CONTENT.number:
                    if 't' in coap_message['payload'].keys():
                        state = coap_message['payload']['t']
                    else:
                        state = coap_message['payload']['v']

                    debug_warning(f'Actuator new state: {state} (IP: {coap_message["coap_ip"]})')
                    print(response.pretty_print())
                    
                    with CoAPClient._db_manager_lock:
                        CoAPClient._db_manager.update_actuator_information(node_id=coap_message['actuator_node_id'], new_state=state)
                else:
                    debug_error(f'Request failed with error code: {response.code}')
            else:
                # Request timed out
                with CoAPClient._db_manager_lock:
                    node = CoAPClient._db_manager.get_node(node_id=coap_message['actuator_node_id'])

                if (datetime.now() - node._last_communication).seconds > node._communication_time * MAX_FAILED_KEEPALIVE:
                    debug_warning(f'Actuator is no more reachable')
                    with CoAPClient._db_manager_lock:
                        CoAPClient._db_manager.update_actuator_information(node_id=coap_message['actuator_node_id'], new_state=1)
                else:
                    debug_warning(f'Actuator may have become unreachable')

    @staticmethod
    def push_coap_message(coap_message: dict) -> bool:
        try:
            CoAPClient._coap_message_queue.put(coap_message, timeout=None)
        except queue.Full:
            debug_error('Full queue exception')
            return False
        return True
    