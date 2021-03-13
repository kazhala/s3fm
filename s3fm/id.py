"""Module contains IDs that will be used as arguments.

ID is an identifier that can be used to find certain resource
in some of the mappings. More information about ID please reference
:ref:`pages/configuration:ID`.
"""
from typing import Dict, List, NamedTuple, Union

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.keys import Keys

ID = int
KBs = Union[Keys, str]
KB_MAPS = Dict[str, List[Dict[str, Union[bool, KBs, Condition, List[KBs]]]]]

KBMode = NamedTuple("KBMode", [("normal", ID), ("command", ID)])(0, 1)
PaneMode = NamedTuple("PaneMode", [("s3", ID), ("fs", ID)])(0, 1)
Pane = NamedTuple("PaneFocus", [("left", ID), ("right", ID), ("cmd", ID)])(0, 1, 2)
LayoutMode = NamedTuple(
    "LayoutMode", [("vertical", ID), ("horizontal", ID), ("single", ID)]
)(0, 1, 2)
Direction = NamedTuple(
    "LayoutMode", [("up", ID), ("down", ID), ("left", ID), ("right", ID)]
)(0, 1, 2, 3)

FileType = NamedTuple(
    "FileType",
    [
        ("bucket", ID),
        ("dir", ID),
        ("file", ID),
        ("link", ID),
        ("dir_link", ID),
        ("exe", ID),
    ],
)(0, 1, 2, 3, 4, 5)
File = NamedTuple(
    "File",
    [("name", str), ("type", ID), ("info", str), ("hidden", bool), ("index", int)],
)
