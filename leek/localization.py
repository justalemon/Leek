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


def __ensure_lang_file(path: Path, lang: str):
    if path in PATHS and lang in PATHS[path]:
        return

    lang_path = path.with_suffix(f".{lang}.json")

    if lang_path.is_file():
        with open(lang_path, encoding="utf-8") as file:
            lines: dict[str, str] = json.load(file)
    else:
        LOGGER.warning(f"Couldn't find {lang_path} for lang {lang}")
        lines = {}

    langs = PATHS.get(path, {})
    langs[lang] = lines
    PATHS[path] = langs


def localize(key: str, lang: str, *formatting_params: Any):
    stack = inspect.stack()
    frame = stack[1]
    path = Path(frame.filename)

    __ensure_lang_file(path, lang)
    __ensure_lang_file(path, "en-US")

    langs = PATHS[path]
    localized = langs.get(lang, {}).get(key, None) or langs.get("en-US", {}).get(key, key)

    return localized if key == localized else localized.format(*formatting_params)
