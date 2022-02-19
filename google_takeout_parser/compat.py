import sys

# from https://github.com/karlicoss/HPI/blob/master/my/core/compat.py

if sys.version_info[:2] >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal  # noqa: F401
