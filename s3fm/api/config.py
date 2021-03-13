"""Module contains the main config class."""
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
)

from prompt_toolkit.filters.base import Condition

from s3fm.api.kb import default_key_maps
from s3fm.exceptions import ClientError
from s3fm.id import ID, KB_MAPS, File, FileType, KBMode, KBs

if TYPE_CHECKING:
    from s3fm.app import App


class AppConfig:
    """App config class."""

    def __init__(self) -> None:
        self.border = False
        self.padding = 1
        self._custom_effects = []
        self.cycle = False

    def use_effect(self, func: Callable[["App"], None]) -> None:
        """Register custom function to run on :class:`~s3fm.app.App` re-render.

        Works sort of like `useEffect` in React.js. It runs on every UI redraw.

        Warning:
            Running heavy functions will affect the performance significantly as
            the UI redraw is happening very often. Its not recommended to register
            function that runs on every UI redraw.

        Note:
            Use :attr:`s3fm.app.App.rendered` to check if the UI is rendered or not.
            If its true, it means that the :class:`~s3fm.app.App` has not yet rendered.

            Check out the example for a code snippet which demonstrate how to run
            certain actions only the first time when the :class:`~s3fm.app.App` is loaded.

        Args:
            func: A callable to be registered to run on UI redraw.

        Examples:
            >>> from s3fm.api.config import Config
            >>> config = Config()
            >>> @config.app.use_effect
            ... def _(app):
            ...     if not app.rendered:
            ...         # only run the following once
            ...         @app.kb.add("c-q")
            ...         def _(_):
            ...             app.exit()
            ...     else:
            ...         # any code to run on every UI redraw
        """
        self._custom_effects.append(func)

    @property
    def custom_effects(self) -> List[Callable[["App"], None]]:
        """List[Callable[["App"], None]]: Custom effects to run on every render."""
        return self._custom_effects


class SpinnerConfig:
    """Spinner config class."""

    prefix_pattern: Optional[List[str]] = None
    postfix_pattern: Optional[List[str]] = None
    text: str = " Loading "
    border: bool = True


class LineModeConfig:
    """LineMode configuration.

    Borrowed the name from ranger: https://github.com/ranger/ranger/wiki/Custom-linemodes

    This class contains the mappings for filename/filetype with icons as well as filename/filetype
    with style classes.

    Use the :meth:`LineModeConfig.register` to register custom linemode processing function which
    will override the default processing logic.
    """

    def __init__(self) -> None:
        self.nerd_font = True
        self.extension_maps = {
            ".7z": "  ",
            ".gz": "  ",
            ".jar": "  ",
            ".zip": "  ",
            ".xz": "  ",
            ".tar": "  ",
            ".taz": "  ",
            ".gif": "  ",
            ".jpeg": "  ",
            ".jpg": "  ",
            ".png": "  ",
            ".svg": "  ",
            ".gif": "  ",
            ".ico": "  ",
            ".mp3": "  ",
            ".mp4": "  ",
            ".avi": "  ",
            ".mov": "  ",
            ".doc": "  ",
            ".docx": "  ",
            ".xls": "  ",
            ".xlsx": "  ",
            ".xlsm": "  ",
            ".ppt": "  ",
            ".pptx": "  ",
            ".pdf": "  ",
            ".license": "  ",
            ".sh": "  ",
            ".zsh": "  ",
            ".bash": "  ",
            ".bats": "  ",
            ".js": "  ",
            ".yml": "  ",
            ".yaml": "  ",
            ".toml": "  ",
            ".conf": "  ",
            ".json": " ﬥ ",
            ".md": "  ",
            ".css": "  ",
            ".jsx": "  ",
            ".tsx": "  ",
            ".html": "  ",
            ".xml": "  ",
            ".py": "  ",
            ".ts": "  ",
            ".vim": "  ",
        }
        self.exact_maps = {
            ".vim": "  ",
            ".vimrc": "  ",
            ".viminfo": "  ",
            ".git": "  ",
            ".config": "  ",
            ".git": "  ",
            "Downloads": "  ",
            "Pictures": "  ",
            "Documents": "  ",
            "node_modules": "  ",
            ".DS_Store": "  ",
            ".gitignore": "  ",
            ".gitconfig": "  ",
            "Dockerfile": "  ",
            "docker-compose.yml": "  ",
            "LICENSE": "  ",
            "..": "  ",
        }
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
        """Register custom processing function.

        Multiple processing function can be registered. The registered function will
        override the default processing function.

        The custom processing function must return a tuple of 4 values consisting:
            1. The style class to use for the line.
            2. The icons to display for the line.
            3. The name of the file to display for the line.
            4. Additional information of the file to display at the end of the line.

        They can be empty string if nothing is intended to display.

        Args:
            func: Custom processing function.

        Examples:
            >>> from s3fm.api.config import Config
            >>> config = Config()
            >>> @config.linemode.register
            ... def custom_process(file):
            ...     style_class = config.linemode.style_maps[file.type]
            ...     icon = config.linemode.filetype_maps[file.type]
            ...     name = file.name
            ...     info = file.info
            ...     return style_class, icon, name, info
        """
        self._process.append(func)

    @property
    def process(
        self,
    ) -> List[Callable[[File], Optional[Tuple[str, str, str, str]]]]:
        """List[Callable[[File], Optional[Tuple[str, str, str, str]]]]: All custom processing function."""
        return self._process


class BaseStyleConfig:
    """Base style config class.

    Inherit this class to create complex style options
    such as :class:`~s3fm.api.config.StyleConfig`.

    The `__iter__` method will help transform this class into
    a processable dictionary for :meth:`prompt_toolkit.styles.Style.from_dict`.
    """

    def clear(self) -> None:
        """Clear all default styles recursively.

        This will completly wipe all the default style value.
        """
        for key, value in self.__dict__.items():
            if isinstance(value, BaseStyleConfig):
                value.clear()
            else:
                setattr(self, key, "")

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        """Customise the iteration method for custom :func:`dict` behavior.

        When calling :func:`dict` on this class, nested :class:`BaseStyleConfig`
        will return as attribute as chained string as the key.

        Yields:
            Yields a tuple of key and value.
        """
        for key, value in self.__dict__.items():
            if isinstance(value, BaseStyleConfig):
                for subkey, subvalue in value.__dict__.items():
                    yield ("%s.%s" % (key, subkey), subvalue)
            else:
                yield (key, value)


class StyleConfig(BaseStyleConfig):
    """Style config class.

    Change the attribute within this class to update the color config
    for different style class.

    All attribute will later be converted to a dictionary that is able
    to be consumed by :meth:`prompt_toolkit.styles.Style.from_dict`.
    """

    class Spinner(BaseStyleConfig):
        """Nested spinner style config."""

        def __init__(self) -> None:
            self.text = "#000000"
            self.prefix = "#ffffff"
            self.postfix = "#ffffff"

    class FilePane(BaseStyleConfig):
        """Nested filepane style config."""

        def __init__(self) -> None:
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
        self.spinner = self.Spinner()
        self.filepane = self.FilePane()

    def register(self, class_name: str) -> Callable[[Any], None]:
        """Register custom style class.

        User can create custom style class. However, at the moment, the custom class
        can only be applied and used for :class:`LineModeConfig`.

        Args:
            class_name: Name for the custom class.

        Returns:
            A decorator that register the custom class.

        Examples:
            >>> from s3fm.api.config import Config, BaseStyleConfig
            >>> from s3fm.id import FileType
            >>> config = Config()
            >>> @config.style.register(class_name="custom_class")
            ... class CustomClass(BaseStyleConfig):
            ...     def __init__(self):
            ...         self.file_color = "#e5c07b"
            >>> config.linemode.style_maps[FileType.file] = "class:custom_class.file_color"
        """

        def decorator(style_cls) -> None:
            class_to_register = style_cls()
            if not isinstance(class_to_register, BaseStyleConfig):
                raise ClientError(
                    "registered style class should inherit `BaseStyleConfig`."
                )
            setattr(self, class_name, class_to_register)

        return decorator


class KBConfig:
    """Keybinding config class.

    Remap default keybindings and also create custom keybindings
    for custom functions.
    """

    def __init__(self) -> None:
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
        """Map keys to actions.

        Mapping for both builtin functions and custom functions should both
        use this function. Builtin functions can be recognised as str while
        custom functions should be provided directly.

        Args:
            action: Provide str will indicate mappings for builtin functions.
                Provide a callable for custom function mappings.
            keys: Keys to map to the action.
            mode_id (ID): Which mode the keybinding should be operating.
            filter: A callable to enable the keybinding only in certain conditions.
            eager: Force priority of the keybindings. Meaning if theres already
                a mapping using a key like `f`, set this flag to overwrite the other
                duplicated key maps.
            **kwargs: Additional args to provide to the :meth:`prompt_toolkit.key_binding.KeyBindings.add`.

        Raises:
            ClientError: When the provided str doesn't match any available default functions.

        Examples:
            >>> from s3fm.api.config import Config
            >>> config = Config()
            >>> config.kb.map(action=lambda app: app.exit(), keys="c-q")
            >>> config.kb.map(action="focus_cmd", keys=["c-w", ":"])
        """
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
        """Unmap actions and keys.

        Use this method to unmap default functions or custom functions.

        Note:
            This will unmap all keys binded to the function. At the moment, you cannot
            select which keys to unmap from a function.

        Args:
            action: Provide str will indicate unmapping for builtin functions.
                Provide a callable for unmapping custom function mappings.
            mode_id (ID): Which mode the keybinding should be unmapped.

        Examples:
            >>> from s3fm.api.config import Config
            >>> config = Config()
            >>> def exit_app(app):
            ...     app.exit()
            >>> config.kb.unmap("exit")
            >>> config.kb.map(action=exit_app, keys="c-q")
        """
        if isinstance(action, str):
            self._kb_maps[mode_id].pop(action, None)
        else:
            self._custom_kb_maps[mode_id].pop(str(action), None)

    @property
    def kb_maps(self) -> Dict[ID, KB_MAPS]:
        """Dict[ID, KB_MAPS]: Configured kb mappings."""
        return self._kb_maps

    @property
    def custom_kb_maps(self) -> Dict[ID, KB_MAPS]:
        """Dict[ID, KB_MAPS]: Custom kb mappings."""
        return self._custom_kb_maps

    @property
    def custom_kb_lookup(self) -> Dict[ID, Dict[str, Any]]:
        """Dict[ID, Dict[str, Any]]: Custom kb lookup."""
        return self._custom_kb_lookup


class Config:
    """Configuration class to customise s3fm.

    Note:
        This is just a highlevel container for all config classes. Please
        reference individual config class documentation for detailed usage.
    """

    def __init__(self):
        self._app = AppConfig()
        self._spinner = SpinnerConfig()
        self._style = StyleConfig()
        self._kb = KBConfig()
        self._linemode = LineModeConfig()

    @property
    def style(self) -> StyleConfig:
        """:class:`StyleConfig`: Style config."""
        return self._style

    @property
    def app(self) -> AppConfig:
        """:class:`AppConfig`: App config."""
        return self._app

    @property
    def spinner(self) -> SpinnerConfig:
        """:class:`SpinnerConfig`: Spinner config."""
        return self._spinner

    @property
    def kb(self) -> KBConfig:
        """:class:`KBConfig`: Kb config."""
        return self._kb

    @property
    def linemode(self) -> LineModeConfig:
        """:class:`LineModeConfig`: Icon config."""
        return self._linemode
