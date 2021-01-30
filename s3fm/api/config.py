"""Module contains the main config class."""
from typing import List, NamedTuple, Optional

from s3fm.exceptions import ClientError


class Config:
    """Class to manage configuration of s3fm."""

    def __init__(self):
        """Initialise all configurable variables."""
        self._app = AppConfig()
        self._spinner = SpinnerConfig()

    @property
    def app(self):
        """Get the app config."""
        return self._app

    @property
    def spinner(self):
        """Get the spinner config."""
        return self._spinner


class AppConfig(NamedTuple):
    """App config class."""

    border: bool = False


class SpinnerConfig(NamedTuple):
    """Spinner config class."""

    prefix_pattern: Optional[List[str]] = None
    postfix_pattern: Optional[List[str]] = None
    text: str = "Loading"
    border: bool = True
