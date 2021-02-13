"""Module contains the main config class."""
from typing import Dict, List, Optional

from s3fm.api.kb import default_kb_maps
from s3fm.base import KB_MAPS, MODE, BaseStyleConfig


class AppConfig:
    """App config class."""

    border: bool = False


class SpinnerConfig:
    """Spinner config class."""

    prefix_pattern: Optional[List[str]] = None
    postfix_pattern: Optional[List[str]] = None
    text: str = " Loading "
    border: bool = True


class StyleConfig(BaseStyleConfig):
    """Style config class."""

    class Spinner(BaseStyleConfig):
        """Spinner style config."""

        def __init__(self, text: str, prefix: str, postfix: str) -> None:
            """Init spinner style settings."""
            self.text = text
            self.prefix = prefix
            self.postfix = postfix

    def __init__(self) -> None:
        """Initialise the default styles."""
        self.file: str = "#abb2bf"
        self.directory: str = "#61afef"
        self.current_line: str = "reverse"
        self.aaa: str = "#000000 reverse"
        self.spinner = self.Spinner(text="#000000", prefix="#ffffff", postfix="#ffffff")


class KBConfig:
    """Keybinding config class."""

    def __init__(self) -> None:
        """Initialise default kb."""
        self._kb_maps = default_kb_maps

    @property
    def kb_maps(self) -> Dict[MODE, KB_MAPS]:
        """Get kb mappings."""
        return self._kb_maps


class Config:
    """Class to manage configuration of s3fm."""

    def __init__(self):
        """Initialise all configurable variables."""
        self._app = AppConfig()
        self._spinner = SpinnerConfig()
        self._style = StyleConfig()
        self._kb = KBConfig()

    @property
    def style(self) -> StyleConfig:
        """Get style config."""
        return self._style

    @property
    def app(self) -> AppConfig:
        """Get app config."""
        return self._app

    @property
    def spinner(self) -> SpinnerConfig:
        """Get spinner config."""
        return self._spinner

    @property
    def kb(self) -> KBConfig:
        """Get kb config."""
        return self._kb
