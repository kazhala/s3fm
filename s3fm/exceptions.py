"""Module contains custom exceptions for s3fm.

ClientError: Error caused by user.
Bug: Unexpected issue.
"""


class ClientError(Exception):
    """Exception to raise when client config causes problems.

    Args:
        message: Error message to display.
    """

    def __init__(self, message: str) -> None:
        """Set message."""
        self._message = message
        super().__init__(self._message)


class Bug(Exception):
    """Should be used as a wild card exception to catch all unexpected exception.

    Args:
        message: Error message to display.
    """

    def __init__(self, message: str) -> None:
        """Set message."""
        self._message = message
        self._message += "\n"
        self._message += "Something went wrong with s3fm, please report this behavior over at https://github.com/kazhala/s3fm/issues"
        super().__init__(self._message)
