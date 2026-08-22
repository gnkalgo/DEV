"""Service-layer failures mapped to the API error envelope."""


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class AuthError(AppError):
    pass


class ServiceError(AppError):
    pass
