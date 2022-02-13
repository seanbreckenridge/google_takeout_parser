"""
Result types, from https://github.com/karlicoss/HPI/blob/master/my/core/error.py
"""

from typing import Union, TypeVar
from pathlib import Path

T = TypeVar("T")
E = TypeVar("E", bound=Exception)

ResT = Union[T, E]

Res = ResT[T, Exception]

PathIsh = Union[str, Path]
