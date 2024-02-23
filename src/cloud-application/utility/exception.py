class DBConnectionError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self._message = message

class DBOperationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self._message = message