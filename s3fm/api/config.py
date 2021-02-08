"""Module contains the main config class."""
from typing import List, NamedTuple, Optional


class Config:
    """Class to manage configuration of s3fm."""

    def __init__(self):
        """Initialise all configurable variables."""
        self._app = AppConfig()
        self._spinner = SpinnerConfig()
        self._style = StyleConfig()

    @property
    def style(self):
        """Get style config."""
        return self._style

    @property
    def app(self):
        """Get app config."""
        return self._app

    @property
    def spinner(self):
        """Get spinner config."""
        return self._spinner


class StyleConfig:
    """Style config class."""

    def __init__(self) -> None:
        """Initialise the default style."""
        self.file: str = "#abb2bf"
        self.directory: str = "#61afef"
        self.current_line: str = "reverse"
        self.aaa: str = "#000000 reverse"

    def clear(self) -> None:
        """Clear all default styles."""
        for attribute in self.__dict__.keys():
            setattr(self, attribute, "")


class AppConfig(NamedTuple):
    """App config class."""

    border: bool = False


class SpinnerConfig(NamedTuple):
    """Spinner config class."""

    prefix_pattern: Optional[List[str]] = None
    postfix_pattern: Optional[List[str]] = None
    text: str = "Loading"
    border: bool = True
