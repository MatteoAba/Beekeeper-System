from utility.db_manager import DBManager
from utility.exception import DBOperationError
from utility.event_manager import EventManager
from utility.entity import Area, Hive
from utility.logger import error, warning, success
from os import system, name
from utility.remote_controller import RemoteController 
import threading

class CLIManager:
    _current_state = None
    _selected_area = None
    _selected_hive = None
    _hive_rules = None
    _db_manager = None
    _db_manager_lock = None
    
    @staticmethod
    def init(db_manager: DBManager, db_manager_lock: threading.Lock) -> None:
        CLIManager._current_state = 'START'
        CLIManager._db_manager = db_manager
        CLIManager._db_manager_lock = db_manager_lock

    @staticmethod
    def run() -> None:
        while(True):
            try:
                match CLIManager._current_state:
                    case 'START':
                        CLIManager._start_state_handler()
                    case 'SELECTED_AREA':
                        CLIManager._selected_area_state_handler()
                    case 'SELECTED_HIVE':
                        CLIManager._selected_hive_state_handler()
                    case 'MANAGE_RULES':
                        CLIManager._manage_rules_state_handler()
            except ValueError:
                warning('Command not valid\n')
    
    @staticmethod
    def _start_state_commands(): 
        print('Commands:')
        print('  1. List areas')
        print('  2. Select area')
        print('  3. Add area')
        print('  4. Remove area')
        print('  5. List unlinked nodes')
        print('  6. Remove unlinked node')

    @staticmethod
    def _start_state_handler():
        CLIManager._start_state_commands()

        while(True):
            command = input('\nCommand: ')
            match command:
                # Show commands list
                case 'help':
                    print()
                    CLIManager._start_state_commands()

                # List areas
                case '1':
                    print()

                    with CLIManager._db_manager_lock:
                        available_areas = CLIManager._db_manager.get_areas()

                    if available_areas:
                        for area in available_areas:
                            print(area)
                    else:
                        warning('No area available') 

                # Select area
                case '2':
                    selected_area_name = input('\nInsert the area name: ')
                    
                    with CLIManager._db_manager_lock:
                        available_areas = CLIManager._db_manager.get_areas()

                    if available_areas:
                        for area in available_areas:
                            if area._name == selected_area_name:
                                CLIManager._selected_area = area
                                CLIManager._current_state = 'SELECTED_AREA'
                                break

                        if CLIManager._selected_area is None:
                            warning(f'No area named \'{selected_area_name}\' found')
                    else:
                        warning('No area available') 
                
                # Add area
                case '3':
                    area_name = input('\nInsert the area name: ')
                    city = input('Insert the city: ')
                    region = input('Insert the region: ')

                    with CLIManager._db_manager_lock:
                        available_areas = CLIManager._db_manager.get_areas()

                    if available_areas:
                        for area in available_areas:
                            if area_name == area._name:
                                warning(f'Area named \'{area_name}\' already exists')
                                continue
                    
                    try:
                        area = Area(name=area_name, city=city, region=region)
                        
                        with CLIManager._db_manager_lock:
                            CLIManager._db_manager.add_area(area=area)

                        success('Area added successfully')
                    except DBOperationError as err:
                        error(err)
                    
                # Remove area
                case '4':
                    warning('\nPay attention: all hives associated with the area will be removed')
                    warning('Pay attention: all nodes associated with the removed hives will become unlinked')
                    area_name = input('Insert the area name: ')

                    with CLIManager._db_manager_lock:
                        available_areas = CLIManager._db_manager.get_areas()

                    try:
                        if available_areas:
                            area_found = False
                            for area in available_areas:
                                if area._name == area_name:
                                    with CLIManager._db_manager_lock:
                                        hives = CLIManager._db_manager.get_hives(area_name=area_name)
                                        CLIManager._db_manager.remove_area(area_name=area_name)
                                    area_found = True
                                    success('Area removed successfully')
                                    
                                    # Remove all polling events associated to the removed area hives
                                    if RemoteController.is_set_polling_time_thread():
                                        elapsed_seconds = RemoteController.update_event_queue(hive_id=None, polling_time=None, update_type='remove', hives_to_remove=hives)

                                        if not EventManager.is_empty_event_queue():
                                            RemoteController.advance_event_queue_time(elapsed_seconds=elapsed_seconds)
                                            RemoteController.resume_event_queue_timer()
                                        else:
                                            RemoteController.unset_polling_time_thread()
                                    break
                            
                            if not area_found:
                                warning(f'No area named \'{area_name}\' found')
                        else:
                            warning('No area available') 
                    except DBOperationError as err:
                        error(err)

                # List unlinked nodes
                case '5':
                    print()

                    with CLIManager._db_manager_lock:
                        unlinked_nodes = CLIManager._db_manager.get_nodes()

                    if unlinked_nodes:
                        for node in unlinked_nodes:
                            print(node)
                    else:
                        warning('No unlinked node available') 

                # Remove unlinked node
                case '6':
                    warning('\nPay attention: all measurements collected from the node will be lost')
                    node_id = input('Insert the node id: ')

                    with CLIManager._db_manager_lock:
                        unlinked_nodes = CLIManager._db_manager.get_nodes()

                    try:
                        if unlinked_nodes:
                            node_found = False
                            for node in unlinked_nodes:
                                if node._id == node_id:
                                    with CLIManager._db_manager_lock:
                                        CLIManager._db_manager.remove_node(node_id=node_id)
                                    node_found = True
                                    success('Node and measurements removed successfully')
                                    break

                            if not node_found:
                                warning(f'No node with id \'{node_id}\' found')
                        else:
                            warning('No unlinked node available') 
                    except DBOperationError as err:
                        error(err)

                # Unknown command
                case _:
                    raise ValueError
                
            if CLIManager._current_state != 'START':
                CLIManager._clear()
                break 

    @staticmethod
    def _selected_area_state_commands(): 
        print('Selected area:')
        print(CLIManager._selected_area)
        print('\nCommands:')
        print('  1. List hives')
        print('  2. Select hive')
        print('  3. Add hive')
        print('  4. Remove hive')
        print('  5. Back to area commands')

    @staticmethod
    def _selected_area_state_handler():
        CLIManager._selected_area_state_commands()

        while(True):
            command = input('\nCommand: ')
            match command:                
                # Show commands list
                case 'help':
                    print()
                    CLIManager._selected_area_state_commands()

                # List hives
                case '1':
                    print()
                    
                    with CLIManager._db_manager_lock:
                        available_hives = CLIManager._db_manager.get_hives(area_name=CLIManager._selected_area._name)
                    
                    if available_hives:
                        for hive in available_hives:
                            print(hive)
                    else:
                        warning('No hive available') 

                # Select hive
                case '2':
                    try:
                        hive_id = int(input('\nInsert the hive id: '))
                        
                        with CLIManager._db_manager_lock:
                            available_hives = CLIManager._db_manager.get_hives(area_name=CLIManager._selected_area._name)
                        
                        if available_hives:
                            for hive in available_hives:
                                if hive._id == hive_id:
                                    CLIManager._selected_hive = hive
                                    CLIManager._current_state = 'SELECTED_HIVE'
                                    break

                            if CLIManager._selected_hive is None:
                                warning(f'No hive with id \'{hive_id}\' found')
                        else:
                            warning('No hive available')
                    except ValueError:
                        warning('Hive id not valid')
                
                # Add hive
                case '3':
                    try:
                        warning('\nThe polling time indicates how often the system will check the condition of the hive and apply the rules')
                        polling_time = int(input('Insert the polling time: '))
                        hive = Hive(hive_id=None, area_name=CLIManager._selected_area._name)
                        
                        with CLIManager._db_manager_lock:
                            CLIManager._db_manager.add_hive(hive=hive, polling_time=polling_time)
                        
                        success(f'Hive added successfully with id \'{hive._id}\'')
                    except DBOperationError as err:
                        error(err)
                    
                # Remove hive
                case '4':
                    try:
                        warning('\nPay attention: all nodes associated with the hive will become unlinked')
                        hive_id = int(input('Insert the hive id: '))

                        with CLIManager._db_manager_lock:
                            available_hives = CLIManager._db_manager.get_hives(area_name=CLIManager._selected_area._name)
                        
                        if available_hives:
                            hive_found = False
                            for hive in available_hives:
                                if hive._id == hive_id:
                                    with CLIManager._db_manager_lock:
                                        CLIManager._db_manager.remove_hive(hive_id=hive_id)
                                    hive_found = True
                                    success('Hive removed successfully')

                                    # Remove the polling event associated to the removed hive
                                    if RemoteController.is_set_polling_time_thread():
                                        elapsed_seconds = RemoteController.update_event_queue(hive_id=hive_id, polling_time=None, update_type='remove')

                                        if not EventManager.is_empty_event_queue():
                                            RemoteController.advance_event_queue_time(elapsed_seconds=elapsed_seconds)
                                            RemoteController.resume_event_queue_timer()
                                        else:
                                            RemoteController.unset_polling_time_thread()
                                    break
                            
                            if not hive_found:
                                warning(f'No hive with id \'{hive_id}\' found')
                        else:
                            warning('No hive available') 
                    except DBOperationError as err:
                        error(err)
                    except ValueError:
                        warning('Hive id not valid')

                # Back to area commands
                case '5':
                    CLIManager._selected_hive = None
                    CLIManager._current_state = 'START'

                # Unknown command
                case _:
                    raise ValueError
                
            if CLIManager._current_state != 'SELECTED_AREA':
                CLIManager._clear()
                break 

    @staticmethod
    def _selected_hive_state_commands(): 
        print('Selected hive:')
        print(CLIManager._selected_hive)
        print('\nCommands:')
        print('  1. List nodes')
        print('  2. List unlinked nodes')
        print('  3. Link node')
        print('  4. Unlink node')
        print('  5. Manage rules')
        print('  6. Back to hive commands')
        print('  7. Back to area commands')
    
    @staticmethod
    def _selected_hive_state_handler():
        CLIManager._selected_hive_state_commands()

        while(True):
            command = input('\nCommand: ')
            match command:
                # Show commands list
                case 'help':
                    print()
                    CLIManager._selected_hive_state_commands()

                # List nodes
                case '1':
                    print()
                    
                    with CLIManager._db_manager_lock:
                        available_nodes = CLIManager._db_manager.get_nodes(hive_id=CLIManager._selected_hive._id)
                    
                    if available_nodes:
                        for node in available_nodes:
                            print(node)
                    else:
                        warning('No node linked to the hive') 
                
                # List unlinked nodes
                case '2':
                    print()
                    
                    with CLIManager._db_manager_lock:
                        unlinked_nodes = CLIManager._db_manager.get_nodes()
                    
                    if unlinked_nodes:
                        for node in unlinked_nodes:
                            print(node)
                    else:
                        warning('No unlinked node available') 

                # Link node
                case '3':
                    node_id = input('\nInsert the node id: ')

                    with CLIManager._db_manager_lock:
                        unlinked_nodes = CLIManager._db_manager.get_nodes()
                    
                    if unlinked_nodes:
                        node_found = False
                        for node in unlinked_nodes:
                            if node_id == node._id:
                                node_found = True
                                break
                        
                        if not node_found:
                            warning(f'No unlinked node with id \'{node_id}\' found')
                            continue

                        try:
                            with CLIManager._db_manager_lock:
                                CLIManager._db_manager.link_node(node_id=node_id, hive_id=CLIManager._selected_hive._id)
                            success('Node linked successfully')
                        except DBOperationError as err:
                            error(err)
                    else:
                        warning('No unlinked node available') 
                    
                # Unlink node
                case '4':
                    node_id = input('\nInsert the node id: ')

                    with CLIManager._db_manager_lock:
                        linked_nodes = CLIManager._db_manager.get_nodes(hive_id=CLIManager._selected_hive._id)
                    
                    if linked_nodes:
                        node_found = False
                        for node in linked_nodes:
                            if node_id == node._id:
                                node_found = True
                                break
                        
                        if not node_found:
                            warning(f'No linked node with id \'{node_id}\' found')
                            continue

                        try:
                            with CLIManager._db_manager_lock:
                                CLIManager._db_manager.unlink_node(node_id=node_id)
                            success('Node unlinked successfully')
                        except DBOperationError as err:
                            error(err)
                    else:
                        warning('No linked node available') 

                # Manage rules
                case '5':
                    with CLIManager._db_manager_lock:
                        rules = CLIManager._db_manager.get_rule(hive_id=CLIManager._selected_hive._id)
                    
                    if rules:
                        CLIManager._hive_rules = rules
                        CLIManager._current_state = 'MANAGE_RULES'
                    else:
                        error('No rule available')

                # Back to hive commands
                case '6':
                    CLIManager._selected_hive = None
                    CLIManager._current_state = 'SELECTED_AREA'

                # Back to area commands
                case '7':
                    CLIManager._selected_area = None
                    CLIManager._selected_hive = None
                    CLIManager._current_state = 'START'

                # Unknown command
                case _:
                    raise ValueError
                
            if CLIManager._current_state != 'SELECTED_HIVE':
                CLIManager._clear()
                break 

    @staticmethod
    def _manage_rules_state_commands(): 
        print(CLIManager._hive_rules)
        print('\nCommands:')
        print('  1. List rules')
        print('  2. Edit rule')
        print('  3. Remove rule')
        print('  4. Edit polling time')
        print('  5. Back to nodes commands')
    
    @staticmethod
    def _manage_rules_state_handler():
        CLIManager._manage_rules_state_commands()
        
        while(True):
            command = input('\nCommand: ')
            match command:
                # Show commands list
                case 'help':
                    print()
                    CLIManager._manage_rules_state_commands()
                
                # List rules
                case '1':
                    print()
                    print(CLIManager._hive_rules)

                # Edit rule
                case '2':
                    rule_number = int(input('\nInsert the rule number: '))
                    match rule_number:
                        # Temperature rule
                        case 1:
                            try:
                                min_temperature = int(input('Insert the minimum temperature threshold: '))
                                target_temperature = int(input('Insert the target temperature: '))

                                temperature_rule = {'min_temperature': min_temperature, 'target_temperature': target_temperature}
                                CLIManager._hive_rules._rules['temperature_rule'] = temperature_rule
                                
                                with CLIManager._db_manager_lock:
                                    CLIManager._db_manager.update_rule(rule=CLIManager._hive_rules)
                                
                                success(f'Rule {rule_number} updated successfully')
                                
                                # Add a new polling event associated with the new rule
                                if RemoteController.is_set_polling_time_thread():
                                    elapsed_seconds = RemoteController.update_event_queue(hive_id=CLIManager._hive_rules._hive_id, polling_time=CLIManager._hive_rules._polling_time, update_type='update')
                                    RemoteController.advance_event_queue_time(elapsed_seconds=elapsed_seconds)
                                    RemoteController.resume_event_queue_timer()
                                else:
                                    RemoteController.start_event_queue_timer(hive_id=CLIManager._hive_rules._hive_id, polling_time=CLIManager._hive_rules._polling_time)

                            except ValueError:
                                warning('Inserted value not valid')
                            except DBOperationError as err:
                                error(err)

                        # Ventilation rule
                        case 2 | 3 | 4 | 5:
                            try:
                                max_temperature = int(input('Insert the maximum temperature threshold: '))
                                max_humidity = int(input('Insert the maximum humidity threshold: '))
                                max_co2 = int(input('Insert the maximum CO2 threshold: '))
                                if rule_number != 2:
                                    is_and = int(input('Insert \'1\' if all thresholds must be verified simultaneously, \'0\' otherwise: '))
                                else:
                                    is_and = 0

                                if is_and != 0 and is_and != 1:
                                    raise ValueError

                                ventilation_rule = {'max_temperature': max_temperature, 'max_humidity' : max_humidity, 'max_co2': max_co2, 'and': is_and}
                                CLIManager._hive_rules._rules['ventilation_rule'][f'{rule_number - 1}'] = ventilation_rule
                                
                                with CLIManager._db_manager_lock:
                                    CLIManager._db_manager.update_rule(rule=CLIManager._hive_rules)
                                
                                success(f'Rule {rule_number} updated successfully')

                                # Add a new polling event associated with the new rule
                                if RemoteController.is_set_polling_time_thread():
                                    elapsed_seconds = RemoteController.update_event_queue(hive_id=CLIManager._hive_rules._hive_id, polling_time=CLIManager._hive_rules._polling_time, update_type='update')
                                    RemoteController.advance_event_queue_time(elapsed_seconds=elapsed_seconds)
                                    RemoteController.resume_event_queue_timer()
                                else:
                                    RemoteController.start_event_queue_timer(hive_id=CLIManager._hive_rules._hive_id, polling_time=CLIManager._hive_rules._polling_time)

                            except ValueError:
                                warning('Inserted value not valid')
                            except DBOperationError as err:
                                error(err)

                # Remove rule
                case '3':
                    rule_number = int(input('\nInsert the rule number: '))
                    match rule_number:
                        # Temperature rule
                        case 1:
                            try:
                                if CLIManager._hive_rules._rules['temperature_rule'] is None:
                                    warning(f'Rule {rule_number} is not yet defined')
                                    continue

                                CLIManager._hive_rules._rules['temperature_rule'] = None
                                
                                with CLIManager._db_manager_lock:
                                    CLIManager._db_manager.update_rule(rule=CLIManager._hive_rules)
                                
                                success(f'Rule {rule_number} removed successfully')

                                # Remove the polling event associated with the removed rule
                                if RemoteController.is_set_polling_time_thread() and not CLIManager._hive_rules.has_rules():
                                    elapsed_seconds = RemoteController.update_event_queue(hive_id=CLIManager._hive_rules._hive_id, polling_time=None, update_type='remove')

                                    if not EventManager.is_empty_event_queue():
                                        RemoteController.advance_event_queue_time(elapsed_seconds=elapsed_seconds)
                                        RemoteController.resume_event_queue_timer()
                                    else:
                                        RemoteController.unset_polling_time_thread()

                            except DBOperationError as err:
                                error(err)

                        # Ventilation rule
                        case 2 | 3 | 4 | 5:
                            try:
                                if CLIManager._hive_rules._rules['ventilation_rule'][f'{rule_number - 1}'] is None:
                                    warning(f'Rule {rule_number} is not yet defined')
                                    continue
                        
                                CLIManager._hive_rules._rules['ventilation_rule'][f'{rule_number - 1}'] = None
                                
                                with CLIManager._db_manager_lock:
                                    CLIManager._db_manager.update_rule(rule=CLIManager._hive_rules)
                                
                                success(f'Rule {rule_number} removed successfully')
                                
                                # Remove the polling event associated with the removed rule
                                if RemoteController.is_set_polling_time_thread() and not CLIManager._hive_rules.has_rules():
                                    elapsed_seconds = RemoteController.update_event_queue(hive_id=CLIManager._hive_rules._hive_id, polling_time=None, update_type='remove')

                                    if not EventManager.is_empty_event_queue():
                                        RemoteController.advance_event_queue_time(elapsed_seconds=elapsed_seconds)
                                        RemoteController.resume_event_queue_timer()
                                    else:
                                        RemoteController.unset_polling_time_thread()

                            except DBOperationError as err:
                                error(err)

                        case _:
                            raise ValueError

                # Edit polling time
                case '4':
                    polling_time = int(input('\nInsert the polling time: '))
                    try:
                        CLIManager._hive_rules._polling_time = polling_time
                        
                        with CLIManager._db_manager_lock:
                            CLIManager._db_manager.update_rule(rule=CLIManager._hive_rules)
                        
                        success(f'Polling time updated successfully')

                        # Update the polling event
                        if RemoteController.is_set_polling_time_thread() and CLIManager._hive_rules.has_rules():
                            elapsed_seconds = RemoteController.update_event_queue(hive_id=CLIManager._hive_rules._hive_id, polling_time=CLIManager._hive_rules._polling_time, update_type='update')
                            RemoteController.advance_event_queue_time(elapsed_seconds=elapsed_seconds)
                            RemoteController.resume_event_queue_timer()

                    except DBOperationError as err:
                        error(err) 

                # Back to hive commands
                case '5':
                    CLIManager._hive_rules = None
                    CLIManager._current_state = 'SELECTED_HIVE'

                case _:
                    raise ValueError

            if CLIManager._current_state != 'MANAGE_RULES':
                CLIManager._clear()
                break 

    @staticmethod
    def _clear():
        if name == 'nt':
            _ = system('cls')
        else:
            _ = system('clear')