from typing import Optional, Dict

from ..log import logger
from .common import HandlerMap
from .en import HANDLER_MAP as EN_DEFAULT_HANDLER_MAP
from .de import HANDLER_MAP as DE_DEFAULT_HANDLER_MAP

LOCALES = {
    "EN": EN_DEFAULT_HANDLER_MAP,
    "DE": DE_DEFAULT_HANDLER_MAP,
}


def resolve_locale(
    locale: Optional[str], additional_handlers: Dict[str, HandlerMap]
) -> HandlerMap:
    if locale is None:
        logger.info("No locale specified, using default (EN)")
        return EN_DEFAULT_HANDLER_MAP

    ll = locale.upper()
    if ll in additional_handlers:
        return additional_handlers[ll]
    elif ll in LOCALES:
        return LOCALES[ll]
    else:
        logger.warning(f"Unknown locale {locale}, using default (EN)")
        return EN_DEFAULT_HANDLER_MAP
