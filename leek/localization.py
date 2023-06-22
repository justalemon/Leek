"""
The tools for the localization of strings in the Leek bot.
"""

import inspect
import json
import logging
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger("leek")
LOCALES = [
    "id",
    "da",
    "de",
    "en-GB",
    "en-US",
    "es-ES",
    "fr",
    "hr",
    "it",
    "hu",
    "nl",
    "no",
    "pl",
    "pt-BR",
    "ro",
    "fi",
    "sv-SE",
    "vi",
    "tr",
    "cs",
    "el",
    "bg",
    "ru",
    "ul",
    "hi",
    "th",
    "zh-CN",
    "ja",
    "zh-TW",
    "ko"
]
PATHS: dict[Path, dict[str, dict[str, str]]] = {}


def __localize(key: str, locale: str, *formatting_params: object):
    stack = inspect.stack()
    frame = stack[2]
    path = Path(frame.filename)

    __ensure_lang_file(path, locale, True)
    __ensure_lang_file(path, "en-US", True)

    langs = PATHS[path]
    localized = langs.get(locale, {}).get(key, None) or langs.get("en-US", {}).get(key, key)

    return localized if key == localized else localized.format(*formatting_params)


def __ensure_lang_file(path: Path, lang: str, log: bool) -> None:
    if path in PATHS and lang in PATHS[path]:
        return

    lang_path = path.with_suffix(f".{lang}.json")

    try:
        with open(lang_path, encoding="utf-8") as file:
            lines: dict[str, str] = json.load(file)
    except FileNotFoundError:
        if log:
            LOGGER.warning(f"Couldn't find {lang_path} for lang {lang}")
        lines = {}
    except json.JSONDecodeError:
        LOGGER.exception(f"Unable to load {lang_path}")
        lines = {}

    langs = PATHS.get(path, {})
    langs[lang] = lines
    PATHS[path] = langs


def get_localizations(key: str) -> dict[str, str]:
    """
    Gets all the available localizations for a specific label.
    :param key: The label to localize.
    :return: A dictionary with all the locales as keys and the localized versions as values.
    """
    stack = inspect.stack()
    frame = stack[1]
    path = Path(frame.filename)

    localized = {}

    for locale in LOCALES:
        __ensure_lang_file(path, locale, False)

        if key in PATHS[path][locale]:
            localized[locale] = PATHS[path][locale][key]

    return localized


def localize(key: str, lang: str, *formatting_params: object) -> str:
    """
    Gets a label on a specific locale.
    :param key: The label to localize.
    :param lang: The locale to use.
    :param formatting_params: The parameters to format this label.
    :return: The formatted label in the specified locale, or the label itself if is not present.
    """
    return __localize(key, lang, *formatting_params)


def get_default(key: str, *formatting_params: object) -> str:
    """
    Gets the default english localization of a specific label.
    :param key: The label to localize.
    :param formatting_params: The desired parameters to format this label.
    :return: The formatted label in US English, or the label itself if is not present.
    """
    return __localize(key, "en-US", *formatting_params)
