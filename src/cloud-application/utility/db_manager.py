import mysql.connector
from mysql.connector import errorcode
from utility.entity import Node, Measurement
from utility.exception import DBConnectionError, DBOperationError
from utility.logger import error, warning
from datetime import datetime

class DBManager:
    def __init__(self, name: str, host: str, port: int, user: str, password: str) -> None:
        self._connection = None
        self._db_name = name
        self._db_host = host
        self._db_port = port
        self._db_user = user
        self._db_password = password

    def open_connection(self) -> None:

        if self._connection is not None:
            return

        try:
            self._connection = mysql.connector.connect(
                host=self._db_host, 
                port=self._db_port,
                user=self._db_user,
                password=self._db_password,
                database=self._db_name
            )
        except mysql.connector.Error as err:
            self._connection = None

            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                error('Database username or password incorrect')
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                error('Database does not exist')
            else:
                error(err)
            
            raise DBConnectionError('Connection to the database failed')

    def close_connection(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def add_node(self, node: Node, coap_ip: str = None) -> None:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'INSERT INTO node (id, type, communication_time, last_communication) VALUES (%s, %s, %s, %s)'
            values = (node._id, node._type, node._communication_time, node._last_communication)

            cursor.execute(query, values)
            self._connection.commit()

            # If the node is an actuator, populate the actuator information table
            if coap_ip:
                query = 'INSERT INTO actuator_information (node_id, coap_ip, state) VALUES (%s, %s, %s)'
                values = (node._id, coap_ip, 1)

                cursor.execute(query, values)
                self._connection.commit()                

            cursor.close()
        except (mysql.connector.Error, DBConnectionError) as err:
            error(err)
            raise DBOperationError('Adding new node operation failed')

    def update_node(self, new_node: Node, coap_ip: str = None) -> None:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'UPDATE node SET type = %s, communication_time = %s, last_communication = %s WHERE (id = %s)'
            values = (new_node._type, new_node._communication_time, new_node._last_communication, new_node._id)

            cursor.execute(query, values)
            self._connection.commit()
            
            # If the node is an actuator, update the actuator information table
            if coap_ip:
                query = 'UPDATE actuator_information SET coap_ip = %s, state = %s WHERE (node_id = %s)'
                values = (coap_ip, 1, new_node._id)

                cursor.execute(query, values)
                self._connection.commit()  
            
            cursor.close()
        except (mysql.connector.Error, DBConnectionError) as err:
            error(err)
            raise DBOperationError('Updating node operation failed')
        
    def update_node_last_communication(self, node_id: str) -> None:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'UPDATE node SET last_communication = %s WHERE (id = %s)'
            values = (datetime.now(), node_id)

            cursor.execute(query, values)
            self._connection.commit()
            cursor.close()
        except (mysql.connector.Error, DBConnectionError) as err:
            error(err)
            raise DBOperationError('Updating node last communication operation failed')
    
    def get_node(self, node_id: str) -> Node:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'SELECT * FROM node WHERE (id = %s)'
            values = (node_id,)

            cursor.execute(query, values)
            row = cursor.fetchone()
            cursor.close()

            if row:
                node = Node(row[0], row[1], row[2], row[3])
                return node
            else:
                warning(f'No node with node_id {node_id} found')

        except (mysql.connector.Error, DBConnectionError) as err:
            error(err)
            return None

        return None
    
    def add_measurements(self, measurements: list) -> None:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'INSERT INTO measurement (type, value, timestamp, node_id) VALUES (%s, %s, %s, %s)'
            values_list = [(m._type, m._value, m._timestamp, m._node_id) for m in measurements]

            cursor.executemany(query, values_list)
            self._connection.commit()
            cursor.close()
        except (mysql.connector.Error, DBConnectionError) as err:
            error(err)
            raise DBOperationError('Adding new measurement operation failed')