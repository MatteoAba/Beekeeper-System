from datetime import datetime

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
    print(f'({datetime.now().strftime("%H:%M:%S")}) {RED_COLOR}[-] {msg} {DEFAULT_COLOR}')

def warning(msg: str) -> None:
    print(f'({datetime.now().strftime("%H:%M:%S")}) {YELLOW_COLOR}[!] {msg} {DEFAULT_COLOR}')  

def info(msg: str) -> None:
    print(f'({datetime.now().strftime("%H:%M:%S")}) {CYAN_COLOR}[i] {msg} {DEFAULT_COLOR}')

def info_debug(msg: str) -> None:
    if debug_mode:
        print(f'({datetime.now().strftime("%H:%M:%S")}) {CYAN_COLOR}[i-debug] {msg} {DEFAULT_COLOR}')

def trace(msg: str) -> None:
    print(f'({datetime.now().strftime("%H:%M:%S")}){DEFAULT_COLOR} {msg} {DEFAULT_COLOR}')

def success(msg: str) -> None:
    print(f'({datetime.now().strftime("%H:%M:%S")}) {GREEN_COLOR}[+] {msg} {DEFAULT_COLOR}')