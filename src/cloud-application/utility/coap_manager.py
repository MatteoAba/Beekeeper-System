from coapthon.server.coap import CoAP, defines
from coapthon.resources.resource import Resource
from utility.db_manager import DBManager, DBOperationError
from utility.entity import Node
from utility.logger import info, info_debug, success, error
from datetime import datetime
import json

class ResRegistration(Resource):
    def __init__(self, name='registration', coap_server=None):
        super(ResRegistration, self).__init__(name, coap_server, visible=True, observable=True, allow_children=True)

        self.payload = 'Registration Resource'
        self.resource_type = 'registration'
        self.content_type = 'application/json'
        self.interface_type = 'write-only'
    
    def render_POST_advanced(self, request, response):
        payload = json.loads(request.payload)
        info_debug(payload)

        try:
            node = Node(node_id=payload["i"], node_type=payload["t"], communication_time=payload["k"], last_communication=datetime.now())

            if CoAPManager._db_manager.get_node(node_id=node._id) is not None:
                CoAPManager._db_manager.update_node(new_node=node, coap_ip=payload["ip"])
                response.code = defines.Codes.CHANGED.number
                success(f'Node \'{node._id}\' updated successfully')
            else:
                CoAPManager._db_manager.add_node(node=node, coap_ip=payload["ip"])
                response.code = defines.Codes.CREATED.number
                success(f'Node \'{node._id}\' registered successfully')
        except DBOperationError:
            response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
            error('Node registration failed')

        return self, response
    
class ResKeepalive(Resource):
    def __init__(self, name='keepalive', coap_server=None):
        super(ResKeepalive, self).__init__(name, coap_server, visible=True, observable=True, allow_children=True)

        self.payload = 'Keepalive Resource'
        self.resource_type = 'keepalive'
        self.content_type = 'application/json'
        self.interface_type = 'write-only'
    
    def render_POST_advanced(self, request, response):
        payload = json.loads(request.payload)
        info_debug(payload)

        try:
            node_id = payload["i"]
            if CoAPManager._db_manager.get_node(node_id=node_id) is not None:
                CoAPManager._db_manager.update_node_last_communication(node_id=node_id)
                response.code = defines.Codes.CHANGED.number
                success(f'Node \'{node_id}\' is still alive')
            else:
                response.code = defines.Codes.NOT_FOUND.number
                error(f'Node \'{node_id}\' not registered')
        except DBOperationError:
            response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
            error('Node last communication update failed')

        return self, response

class CoAPServer(CoAP):
    def __init__(self, host, port):
        CoAP.__init__(self, (host, port), False)
        self.add_resource('registration/', ResRegistration())
        self.add_resource('keepalive/', ResKeepalive())

class CoAPManager:
    _coap_server = None
    _db_manager = None

    @staticmethod
    def run(db_manager: DBManager, coap_server_ip: str, coap_server_port: int, coap_server_timeout: int) -> None:
        CoAPManager._coap_server = CoAPServer(coap_server_ip, coap_server_port)
        CoAPManager._db_manager = db_manager

        try:
            info(f'CoAP server listening on {coap_server_ip}:{coap_server_port}')
            CoAPManager._coap_server.listen(timeout=coap_server_timeout)
        except KeyboardInterrupt:
            CoAPManager._coap_server.close()
            info('Closing CoAP Server...')