"""Broker adapter errors. Never include secrets in messages."""


class BrokerError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class BrokerUnsupportedError(BrokerError):
    def __init__(self, operation: str) -> None:
        super().__init__("UNSUPPORTED_OPERATION", f"{operation} is not supported for this broker")


class BrokerAuthError(BrokerError):
    def __init__(self, message: str = "Broker authentication failed") -> None:
        super().__init__("BROKER_AUTH_FAILED", message)
