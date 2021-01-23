"""Module contains the main config class."""
from s3fm.exceptions import ClientError


class Config:
    """Class to manage configuration of s3fm."""

    def __init__(self):
        """Initialise all configurable variables."""
        self._border = False

    @property
    def border(self):
        """Get border value."""
        return self._border

    @border.setter
    def border(self, value):
        """Set border value."""
        if not isinstance(value, bool):
            raise ClientError("border should be type of bool")
        self._border = value
