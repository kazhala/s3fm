"""Module contains the ErrorPane to display error messages."""
from typing import TYPE_CHECKING, Callable, List, Tuple

from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    Float,
    Window,
    WindowAlign,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets.base import Frame

from s3fm.enums import ErrorType

if TYPE_CHECKING:
    from prompt_toolkit.filters.base import Condition


class ErrorPane(Float):
    """Dedicated pane to display non-application error/warning message.

    Args:
        error: :class:`prompt_toolkit.filters.Condition` to indicate if theres an active error.
        message: A callable to retrieve the error/warning message.
        error_type: A callable to retrieve the error type.
    """

    def __init__(
        self,
        error: "Condition",
        message: Callable[[], str],
        error_type: Callable[[], ErrorType],
    ) -> None:
        self._error = error
        self._message = message
        self._type = error_type

        content = Frame(
            title=self._get_title,
            body=Window(
                content=FormattedTextControl(text=self._get_text),
                align=WindowAlign.CENTER,
            ),
        )

        super().__init__(
            content=ConditionalContainer(content=content, filter=self._error)
        )

    def _get_title(self) -> List[Tuple[str, str]]:
        """Get the error pane tile.

        Returns:
            A list of tuples which can be parsed as
            :class:`prompt_toolkit.formatted_text.FormattedText`.
        """
        error_type = self._type().value
        return [
            ("class:error.%s" % error_type.lower(), error_type),
        ]

    def _get_text(self) -> List[Tuple[str, str]]:
        """Get the error pane tile.

        Returns:
            A list of tuples which can be parsed as
            :class:`prompt_toolkit.formatted_text.FormattedText`.
        """
        return [
            ("class:error.%s" % self._type().value.lower(), self._message()),
            ("", "\n"),
            ("", "\n"),
            ("class:error.instruction", "Press any key to continue ..."),
        ]
