from typing import Optional, List

from ..log import logger
from .common import HandlerMap
from .en import HANDLER_MAP as EN_DEFAULT_HANDLER_MAP
from .de import HANDLER_MAP as DE_DEFAULT_HANDLER_MAP

from .all import LOCALES as ALL_LOCALES

LOCALES = {
    "EN": EN_DEFAULT_HANDLER_MAP,
    "DE": DE_DEFAULT_HANDLER_MAP,
}


def _log_locale_options() -> None:
    logger.info(
        f"To silence this message, set the GOOGLE_TAKEOUT_PARSER_LOCALE to one of:: {', '.join(map(repr, LOCALES.keys()))}"
    )


def resolve_locale(
    locale: Optional[str],
    additional_handlers: List[HandlerMap],
) -> List[HandlerMap]:
    # additional_handlers is passed by the user in python, should override
    if additional_handlers:
        logger.debug(
            f"Using additional handlers (passed in python code, not based on environment variable): {additional_handlers}"
        )
        return additional_handlers

    if locale is None:
        logger.info("No locale specified, using default (EN)")
        _log_locale_options()
        return [EN_DEFAULT_HANDLER_MAP]

    ll = locale.upper()
    if ll in LOCALES:
        logger.debug(f"Using locale {ll}. To override set, GOOGLE_TAKEOUT_PARSER_LOCALE")
        return [LOCALES[ll]]
    else:
        logger.warning(f"Unknown locale {locale}, using default (EN)")
        _log_locale_options()
        return [EN_DEFAULT_HANDLER_MAP]
