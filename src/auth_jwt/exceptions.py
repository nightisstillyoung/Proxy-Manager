from fastapi import status

from base_exceptions import BaseAppError


class AuthException(BaseAppError):
    def __init__(self, status_: int = status.HTTP_403_FORBIDDEN, details: str = "You are not logged in"):
        super().__init__(status_, details)


class WrongCredentials(AuthException):
    def __init__(self):
        super().__init__(details="Incorrect username or password")


class ChangePasswordError(AuthException):
    def __init__(self):
        super().__init__(details="Incorrect password or new password is too short")


class TokenAuthError(AuthException):
    def __init__(self):
        super().__init__(
            details="Failed to authenticate by JWT token (maybe user is no longer exists?). Try to log in again."
        )


class InvalidToken(AuthException):
    def __init__(self):
        super().__init__(
            details="JWT token is invalid or/and it's signature is invalid."
        )


class UserInactive(AuthException):
    def __init__(self):
        super().__init__(details="This user is inactive now. Contact your admin for more details")


class TokenExpired(AuthException):
    def __init__(self):
        super().__init__(details="JWT token expired. Please log in again.")


# not used anywhere for now
class AccessError(AuthException):
    def __init__(self):
        super().__init__(details="You do not have access to this resource")
