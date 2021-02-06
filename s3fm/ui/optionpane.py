"""Module contains the floating options pane."""
from prompt_toolkit.formatted_text.base import FormattedText
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl


class OptionPane(Window):
    """Floating pane to display options/actions."""

    def __init__(self) -> None:
        """Initialise the pane."""
        super().__init__(FormattedTextControl(FormattedText([("", "Options")])))
