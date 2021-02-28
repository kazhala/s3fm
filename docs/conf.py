import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "s3fm"
copyright = "2021, Kevin Zhuang"
author = "Kevin Zhuang"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "furo",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_title = "s3fm"
html_static_path = ["_static"]

napoleon_include_init_with_doc = True
autodoc_typehints = "description"
autodoc_member_order = "bysource"
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "prompt_toolkit": ("https://python-prompt-toolkit.readthedocs.io/en/master/", None),
}
