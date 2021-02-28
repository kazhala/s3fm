import os
import sys

import recommonmark
import sphinx_rtd_theme
from recommonmark.transform import AutoStructify
from recommonmark.parser import CommonMarkParser

sys.path.insert(0, os.path.abspath("../"))


project = "s3fm"
copyright = "2021, Kevin Zhuang"
author = "Kevin Zhuang"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx_rtd_theme",
    "recommonmark",
    "sphinx.ext.napoleon",
]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

napoleon_include_init_with_doc = True


def visit_document(*_):
    pass


setattr(CommonMarkParser, "visit_document", visit_document)


def setup(app):
    app.add_config_value(
        "recommonmark_config",
        {"auto_toc_tree_section": "Contents"},
        True,
    )
    app.add_transform(AutoStructify)
