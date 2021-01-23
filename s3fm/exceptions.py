"""Module contains custom exceptions for s3fm."""


class ClientError(Exception):
    """Exception to raise when client config cause problems."""

    def __init__(self, message: str) -> None:
        """Set message."""
        self._message = message
        super().__init__(self._message)


class Bug(Exception):
    """Should be used as a wild card exception to catch all unexpected exception."""

    def __init__(self, message: str) -> None:
        """Set message."""
        self._message = message
        self._message += "\n"
        self._message += "Something went wrong with s3fm, please report this behavior over at https://github.com/kazhala/s3fm/issues"
        super().__init__(self._message)
