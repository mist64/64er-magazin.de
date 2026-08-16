"""Import one numbered step from another.

A Python module name cannot start with a digit, so `from 010_ocr_blocks import
ARTICLE_LABELS` is a syntax error.  The steps are named after their spec files
anyway -- one directory, one convention, `NNN_name.{md,sh,py}` -- and this is
the price: three call sites load their dependency by path instead of by name.

Unnumbered because it is not a step.  Same for llm.py, which is the transport
steps 020 and 030 share.
"""

import importlib.util
import os
import sys


def load(stem):
    """Load `<stem>.py` from this directory as a module, once."""
    if stem in sys.modules:
        return sys.modules[stem]
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), stem + ".py")
    spec = importlib.util.spec_from_file_location(stem, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[stem] = mod          # before exec_module, so a cycle cannot loop
    spec.loader.exec_module(mod)
    return mod
