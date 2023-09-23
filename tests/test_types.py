import inspect

import google_takeout_parser.models as mod
from cachew import get_union_args


def test_check_union() -> None:
    """
    Makes sure that any classes defined in models are included in the union type

    sanity check test to ensure cachew doesn't fail with difficult to debug union/errors
    """

    classes = {
        v
        for _name, v in inspect.getmembers(mod, predicate=inspect.isclass)
        if mod.BaseEvent in v.__mro__ and v != mod.BaseEvent
    }
    ua = get_union_args(mod.DEFAULT_MODEL_TYPE)
    assert ua is not None
    union_args = set(ua)

    assert union_args == classes
