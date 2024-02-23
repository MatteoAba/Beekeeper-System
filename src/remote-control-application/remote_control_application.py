from utility.cli_manager import CLIManager
from utility.db_manager import DBManager
from utility.remote_controller import RemoteController
from utility.coap_client import CoAPClient
from utility.logger import info
import threading

DATABASE_NAME = 'beekeeper'
DATABASE_HOST = 'localhost'
DATABASE_PORT = 3306
DATABASE_USER = 'root'
DATABASE_PASSWORD = 'password'

if __name__ == '__main__':
    try:
        db = DBManager(name=DATABASE_NAME, host=DATABASE_HOST, port=DATABASE_PORT, user=DATABASE_USER, password=DATABASE_PASSWORD)
        db_lock = threading.Lock()

        CoAPClient.init(db_manager=db, db_manager_lock=db_lock)
        coap_client_thread = threading.Thread(target=CoAPClient.run, daemon=False)
        coap_client_thread.start()

        RemoteController.init(db_manager=db, db_manager_lock=db_lock)
        RemoteController.run()

        CLIManager.init(db_manager=db, db_manager_lock=db_lock)
        CLIManager.run()
    except KeyboardInterrupt:
        info('\nClosing program...')
        RemoteController.stop()
        with db_lock:
            db.close_connection()
        exit(0)