"""Module contains the main config class."""
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Union

from prompt_toolkit.filters.base import Condition

from s3fm.api.kb import default_key_maps
from s3fm.base import ID, KB_MAPS, BaseStyleConfig, File, FileType, KBMode, KBs
from s3fm.exceptions import ClientError

if TYPE_CHECKING:
    from s3fm.app import App


class AppConfig:
    """App config class."""

    border: bool = False
    padding: int = 1


class SpinnerConfig:
    """Spinner config class."""

    prefix_pattern: Optional[List[str]] = None
    postfix_pattern: Optional[List[str]] = None
    text: str = " Loading "
    border: bool = True


class LineModeConfig:
    """Icon config class."""

    def __init__(self) -> None:
        """Init Icon config."""
        self.nerd_font = True
        self.extension_maps = {}
        self.exact_maps = {".vim": "  ", ".git": "  "}
        self.filetype_maps = {
            FileType.bucket: "  ",
            FileType.dir: "  ",
            FileType.link: "  ",
            FileType.dir_link: "  ",
            FileType.file: "  ",
            FileType.exe: "  ",
        }
        self.style_maps = {
            FileType.bucket: "class:filepane.bucket",
            FileType.dir: "class:filepane.dir",
            FileType.link: "class:filepane.link",
            FileType.dir_link: "class:filepane.dir_link",
            FileType.file: "class:filepane.file",
            FileType.exe: "class:filepane.exe",
        }
        self._process = []

    def register(
        self, func: Callable[[File], Optional[Tuple[str, str, str, str]]]
    ) -> None:
        """Register custom processing function."""
        self._process.append(func)

    @property
    def process(
        self,
    ) -> List[Callable[[File], Optional[Tuple[str, str, str, str]]]]:
        """Get all custom processing function."""
        return self._process


class StyleConfig(BaseStyleConfig):
    """Style config class."""

    class Spinner(BaseStyleConfig):
        """Spinner style config."""

        def __init__(self) -> None:
            """Init spinner style settings."""
            self.text = "#000000"
            self.prefix = "#ffffff"
            self.postfix = "#ffffff"

    class FilePane(BaseStyleConfig):
        """FilePane style config."""

        def __init__(self) -> None:
            """Init filepane style settings."""
            self.current_line = "#61afef reverse"
            self.other_line = "#abb2bf"
            self.focus_path = "#a0c980"
            self.unfocus_path = "#5c6370"
            self.file = "#abb2bf"
            self.dir = "#61afef"
            self.bucket = "#61afef"
            self.link = "#abb2bf"
            self.dir_link = "#61afef"
            self.exe = "#98c379"

    def __init__(self) -> None:
        """Initialise the default styles."""
        self.spinner = self.Spinner()
        self.filepane = self.FilePane()


class KBConfig:
    """Keybinding config class."""

    def __init__(self) -> None:
        """Initialise default kb."""
        self._kb_maps = default_key_maps
        self._custom_kb_maps = {KBMode.normal: {}, KBMode.command: {}}
        self._custom_kb_lookup = {KBMode.normal: {}, KBMode.command: {}}

    def map(
        self,
        action: Union[str, Callable[["App"], None]],
        keys: Union[KBs, List[KBs]],
        mode_id: ID = KBMode.normal,
        filter: Callable[[], bool] = lambda: True,
        eager: bool = False,
        **kwargs
    ) -> None:
        """Map keys to actions."""
        if isinstance(action, str):
            if action in self._kb_maps[mode_id]:
                self._kb_maps[mode_id][action].append(
                    {
                        "keys": keys,
                        "filter": Condition(filter),
                        "eager": eager,
                        **kwargs,
                    }
                )
            else:
                raise ClientError("keybinding action %s does not exists." % action)
        else:
            if str(action) in self._custom_kb_maps[mode_id]:
                self._custom_kb_maps[mode_id][str(action)].append(
                    {
                        "keys": keys,
                        "filter": Condition(filter),
                        "eager": eager,
                        **kwargs,
                    }
                )
            else:
                self._custom_kb_maps[mode_id][str(action)] = [
                    {
                        "keys": keys,
                        "filter": Condition(filter),
                        "eager": eager,
                        **kwargs,
                    }
                ]
                self._custom_kb_lookup[mode_id][str(action)] = action

    def unmap(
        self, action: Union[str, Callable[["App"], None]], mode_id: ID = KBMode.normal
    ) -> None:
        """Unmap actions."""
        if isinstance(action, str):
            self._kb_maps[mode_id].pop(action, None)
        else:
            self._custom_kb_maps[mode_id].pop(str(action), None)

    @property
    def kb_maps(self) -> Dict[ID, KB_MAPS]:
        """Get kb mappings."""
        return self._kb_maps

    @property
    def custom_kb_maps(self) -> Dict[ID, KB_MAPS]:
        """Get custom kb mappings."""
        return self._custom_kb_maps

    @property
    def custom_kb_lookup(self) -> Dict[ID, Dict[str, Any]]:
        """Get custom kb lookup."""
        return self._custom_kb_lookup


class Config:
    """Class to manage configuration of s3fm."""

    def __init__(self):
        """Initialise all configurable variables."""
        self._app = AppConfig()
        self._spinner = SpinnerConfig()
        self._style = StyleConfig()
        self._kb = KBConfig()
        self._linemode = LineModeConfig()

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

    @property
    def linemode(self) -> LineModeConfig:
        """Get icon config."""
        return self._linemode
