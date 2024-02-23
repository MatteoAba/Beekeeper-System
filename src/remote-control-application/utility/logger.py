RED_COLOR = "\033[91m"
GREEN_COLOR = "\033[92m"
YELLOW_COLOR = "\033[93m"
BLUE_COLOR = "\033[94m"
PURPLE_COLOR = "\033[95m"
CYAN_COLOR = "\033[96m"
WHITE_COLOR = "\033[97m"
DEFAULT_COLOR = WHITE_COLOR

debug_mode = True

def error(msg: str) -> None:
    print(f'{RED_COLOR}{msg}{DEFAULT_COLOR}')

def debug_error(msg: str) -> None:
    if debug_mode:
        print(f'{RED_COLOR}[DEBUG] {msg}{DEFAULT_COLOR}')

def warning(msg: str) -> None:
    print(f'{YELLOW_COLOR}{msg}{DEFAULT_COLOR}')  

def debug_warning(msg: str) -> None:
    if debug_mode:
        print(f'{YELLOW_COLOR}[DEBUG] {msg}{DEFAULT_COLOR}')  

def info(msg: str) -> None:
    print(f'{CYAN_COLOR}{msg}{DEFAULT_COLOR}')

def trace(msg: str) -> None:
    print(f'{DEFAULT_COLOR}{msg}{DEFAULT_COLOR}')

def success(msg: str) -> None:
    print(f'{GREEN_COLOR}{msg}{DEFAULT_COLOR}')