"""Module contains custom exceptions for s3fm.

ClientError: Error caused by user.
Bug: Unexpected issue.
Notification: Non-application error.
"""
from s3fm.enums import ErrorType


class ClientError(Exception):
    """Exception to raise when client config causes problems.

    Args:
        message: Error message to display.
    """

    def __init__(self, message: str) -> None:
        self._message = message
        super().__init__(self._message)


class Bug(Exception):
    """Should be used as a wild card exception to catch all unexpected exception.

    Args:
        message: Error message to display.
    """

    def __init__(self, message: str) -> None:
        self._message = message
        self._message += "\n"
        self._message += "Something went wrong with s3fm, please report this behavior over at https://github.com/kazhala/s3fm/issues."
        super().__init__(self._message)


class Notification(Exception):
    """Used to display error message to the user but not exit the app.

    Args:
        message: Error message to display.
        error_type: Error type.
    """

    def __init__(self, message: str, error_type: ErrorType = ErrorType.error) -> None:
        self._message = message
        self.type = error_type
        super().__init__(self._message)
