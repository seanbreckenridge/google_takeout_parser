import sys
from typing import TYPE_CHECKING

# from https://github.com/karlicoss/HPI/blob/master/my/core/compat.py

if sys.version_info[:2] >= (3, 8):
    from typing import Literal
else:
    if TYPE_CHECKING:
        from typing_extensions import Literal
    else:
        from typing import Union
        Literal = Union

