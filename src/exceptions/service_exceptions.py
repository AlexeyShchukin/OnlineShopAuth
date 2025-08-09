from fastapi import status


class ServiceException(Exception):
    """Base exception for the service layer."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = "An unexpected server error occurred."

    def __init__(
            self,
            message: str | None = None,
            status_code: int | None = None
    ):
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)


class BlockedUserException(ServiceException):
    """Raised when a user is blocked due to too many attempts."""
    status_code = status.HTTP_403_FORBIDDEN
    message = "Too many login attempts. Try again later."


class UserNotFoundException(ServiceException):
    """Raised when a user is not found in the database."""
    status_code = status.HTTP_404_NOT_FOUND
    message = "User not found."


class InactiveUserException(ServiceException):
    """Raised when a user account is not active."""
    status_code = status.HTTP_403_FORBIDDEN
    message = "User account is inactive."


class InvalidPasswordException(ServiceException):
    """Raised for an incorrect password."""
    status_code = status.HTTP_401_UNAUTHORIZED
    message = "Incorrect password."

    def __init__(self, message: str | None = None, remaining_attempts: int = 0):
        super().__init__(message=message, status_code=self.status_code)
        self.remaining_attempts = remaining_attempts


class TooManyAttemptsException(ServiceException):
    """Raised when max login attempts are reached."""
    status_code = status.HTTP_403_FORBIDDEN
    message = "Too many failed login attempts. You are temporarily blocked."


class TokenNotFoundException(ServiceException):
    """Raised when a refresh token is not found in db."""
    status_code = status.HTTP_401_UNAUTHORIZED
    message = "Invalid refresh token"


class TokenAlreadyUsedException(ServiceException):
    """
    Raised when a refresh token has been used outside of the grace period.
    """
    status_code = status.HTTP_401_UNAUTHORIZED
    message = "Refresh token has been already used"


class UserAlreadyExistsException(ServiceException):
    """Raised when a user with the same email already exists."""
    status_code = status.HTTP_400_BAD_REQUEST
    message = "User with this email already exists."


class MissingTokenException(ServiceException):
    """Raised when a refresh token is not found in cookies."""
    status_code = status.HTTP_401_UNAUTHORIZED
    message = "Refresh token missing"


class InvalidTokenException(ServiceException):
    """Raised when a token is malformed or invalid."""
    status_code = status.HTTP_401_UNAUTHORIZED
    message = "Invalid token payload"
