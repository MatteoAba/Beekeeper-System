import mysql.connector
from mysql.connector import errorcode
from utility.entity import Area, Hive, Node, Measurement, Rule
from utility.exception import DBConnectionError, DBOperationError
from utility.logger import debug_error, debug_warning
import json

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
            self._connection.close()
            self._connection = None

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
                debug_error('Database username or password incorrect')
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                debug_error('Database does not exist')
            else:
                debug_error(err)
            
            raise DBConnectionError('Connection to the database failed')

    def close_connection(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    # ---------------------- Node Queries ---------------------- #

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
                node = Node(node_id=row[0], node_type=row[1], communication_time=row[2], last_communication=row[3])
                return node
            else:
                debug_error(f'No node with id {node_id} found')

        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            return None

        return None

    def get_nodes(self, hive_id: int = None) -> list:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            
            # If no hive_id is given, get the unlinked nodes
            if hive_id is not None:
                query = 'SELECT * FROM node WHERE (hive_id = %s)'
                values = (hive_id,)
                cursor.execute(query, values)
            else:
                query = 'SELECT * FROM node WHERE (hive_id IS NULL)'
                cursor.execute(query)

            rows = cursor.fetchall()
            cursor.close()

            if isinstance(rows, list) and len(rows) > 0:
                nodes = [Node(node_id=row[0], node_type=row[1], communication_time=row[2], last_communication=row[3], hive_id=row[4]) for row in rows]
                return nodes
            else:
                debug_warning(f'No node associated with hive {hive_id} found')

        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            return None

        return None

    def link_node(self, node_id: str, hive_id: int) -> None:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'UPDATE node SET hive_id = %s WHERE (id = %s)'
            values = (hive_id, node_id)

            cursor.execute(query, values)
            self._connection.commit()
            cursor.close()
        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            raise DBOperationError('Linking node operation failed')
        
    def unlink_node(self, node_id: str) -> None:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'UPDATE node SET hive_id = %s WHERE (id = %s)'
            values = (None, node_id)

            cursor.execute(query, values)
            self._connection.commit()
            cursor.close()
        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            raise DBOperationError('Unlinking node operation failed')
        
    def remove_node(self, node_id: str) -> None:
        try:
            self.open_connection()

            # Remove all measurements related to the node
            cursor = self._connection.cursor()
            query = 'DELETE FROM measurement WHERE (node_id = %s)'
            values = (node_id,)

            cursor.execute(query, values)
            self._connection.commit()

            # Remove the node
            query = 'DELETE FROM node WHERE (id = %s)'
            values = (node_id,)

            cursor.execute(query, values)
            self._connection.commit()            
            cursor.close()
        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            raise DBOperationError('Removing node operation failed')

    def get_actuator_information(self, node_id: str) -> dict:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'SELECT * FROM actuator_information WHERE (node_id = %s)'
            values = (node_id,)

            cursor.execute(query, values)
            row = cursor.fetchone()
            cursor.close()

            if row:
                actuator_information = {'coap_ip': row[1], 'state': row[2]}
                return actuator_information
            else:
                debug_error(f'No actuator information associated with node {node_id} found')

        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            return None

        return None
    
    def update_actuator_information(self, node_id: str, new_state: int) -> None:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'UPDATE actuator_information SET state = %s WHERE (node_id = %s)'
            values = (new_state, node_id)

            cursor.execute(query, values)
            self._connection.commit()
            cursor.close()
        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            raise DBOperationError('Updating actuator information operation failed')
        
    # ------------------ Measurements Queries ------------------ #
        
    def get_measurements(self, node_id: str, measurement_types: list) -> list:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            filters = f'type = \'{measurement_types[0]}\''
            for measurement_type in measurement_types[1:]:
                filters += f' OR type = \'{measurement_type}\''
            query = f'SELECT * FROM measurement WHERE node_id = %s AND ({filters}) ORDER BY timestamp desc, type LIMIT {len(measurement_types)}'
            values = (node_id,)

            cursor.execute(query, values)
            rows = cursor.fetchall()
            cursor.close()

            if isinstance(rows, list) and len(rows) > 0:
                measurements = [Measurement(measurement_type=row[1], value=row[2], timestamp=row[3]) for row in rows]
                return measurements
            else:
                debug_warning(f'No measurement found')

        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            return None
        return None
    
    # ---------------------- Hive Queries ---------------------- #
        
    def add_hive(self, hive: Hive, polling_time: int) -> None:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'INSERT INTO hive (area_name) VALUES (%s)'
            values = (hive._area_name,)

            cursor.execute(query, values)
            self._connection.commit()
            hive._id = cursor.lastrowid
            cursor.close()

            # Add rule to the hive
            rule = Rule(hive_id=hive._id, polling_time=polling_time)
            self.add_rule(rule=rule)
        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            raise DBOperationError('Adding new hive operation failed')
        
    def remove_hive(self, hive_id: int) -> None:
        try:
            # Unlink all nodes related to the hive
            nodes = self.get_nodes(hive_id=hive_id)
            if nodes:
                for node in nodes:
                    self.unlink_node(node_id=node._id)
            else:
                debug_warning(f'No node associated with hive {hive_id} found')

            # Remove the rule related to the hive
            self.remove_rule(hive_id=hive_id)

            # Remove the hive
            cursor = self._connection.cursor()
            query = 'DELETE FROM hive WHERE (id = %s)'
            values = (hive_id,)

            cursor.execute(query, values)
            self._connection.commit()

            cursor.close()
        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            raise DBOperationError('Removing hive operation failed')

    def get_hives(self, area_name: str) -> list:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'SELECT * FROM hive WHERE (area_name = %s)'
            values = (area_name,)

            cursor.execute(query, values)
            rows = cursor.fetchall()
            cursor.close()

            if isinstance(rows, list) and len(rows) > 0:
                hives = [Hive(hive_id=row[0], area_name=row[1]) for row in rows]
                return hives
            else:
                debug_warning(f'No hive found')
    
        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            return None

        return None

    # ---------------------- Rule Queries ---------------------- #
        
    def add_rule(self, rule: Rule) -> None:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'INSERT INTO rule (hive_id, polling_time, rules) VALUES (%s, %s, %s)'
            values = (rule._hive_id, rule._polling_time, json.dumps(rule._rules))

            cursor.execute(query, values)
            self._connection.commit()
            cursor.close()
        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            raise DBOperationError('Adding new rule operation failed')
        
    def remove_rule(self, hive_id: int) -> None:
        try:
            # Remove rule related to the hive
            cursor = self._connection.cursor()
            query = 'DELETE FROM rule WHERE (hive_id = %s)'
            values = (hive_id,)

            cursor.execute(query, values)
            self._connection.commit()
            cursor.close()
        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            raise DBOperationError('Removing rule operation failed')
        
    def update_rule(self, rule: Rule) -> None:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'UPDATE rule SET polling_time = %s, rules = %s WHERE (hive_id = %s)'
            values = (rule._polling_time, json.dumps(rule._rules), rule._hive_id)

            cursor.execute(query, values)
            self._connection.commit()
            cursor.close()
        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            raise DBOperationError('Updating rule operation failed')

    def get_rule(self, hive_id: int) -> Rule:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'SELECT * FROM rule WHERE (hive_id = %s)'
            values = (hive_id,)

            cursor.execute(query, values)
            row = cursor.fetchone()
            cursor.close()

            if row:
                rule = Rule(hive_id=row[0], polling_time=row[1], rules=json.loads(row[2]))
                return rule
            else:
                debug_error(f'No rule found')
    
        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            return None

        return None 

    def get_rules(self) -> list:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'SELECT * FROM rule'

            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()

            if rows and len(rows) != 0:
                rules = []
                for row in rows:
                    rules.append(Rule(hive_id=row[0], polling_time=row[1], rules=json.loads(row[2])))    
                return rules
            else:
                debug_warning(f'No rule found')
    
        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            return None

        return None      

    # ---------------------- Area Queries ---------------------- #
    
    def add_area(self, area: Area) -> None:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'INSERT INTO area (name, city, region) VALUES (%s, %s, %s)'
            values = (area._name, area._city, area._region)

            cursor.execute(query, values)
            self._connection.commit()
            cursor.close()
        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            raise DBOperationError('Adding new area operation failed')
        
    def remove_area(self, area_name: str) -> None:
        try:
            # Remove all hives related to the area
            hives = self.get_hives(area_name=area_name)
            if hives:
                for hive in hives:
                    self.remove_hive(hive_id=hive._id)
            else:
                debug_warning(f'No hive associated with area {area_name} found')

            # Remove the area
            cursor = self._connection.cursor()
            query = 'DELETE FROM area WHERE (name = %s)'
            values = (area_name,)

            cursor.execute(query, values)
            self._connection.commit()
            cursor.close()
        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            raise DBOperationError('Removing area operation failed')

    def get_areas(self) -> list:
        try:
            self.open_connection()

            cursor = self._connection.cursor()
            query = 'SELECT * FROM area'

            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()

            if isinstance(rows, list) and len(rows) > 0:
                areas = [Area(name=row[0], city=row[1], region=row[2]) for row in rows]
                return areas
            else:
                debug_warning(f'No area found')
    
        except (mysql.connector.Error, DBConnectionError) as err:
            debug_error(err)
            return None

        return None