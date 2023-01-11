import inspect
import json
import logging
from pathlib import Path

LOGGER = logging.getLogger("leek")
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


def localize(key: str, lang: str):
    stack = inspect.stack()
    frame = stack[1]
    path = Path(frame.filename)

    __ensure_lang_file(path, lang)
    __ensure_lang_file(path, "en-US")

    langs = PATHS[path]
    return langs.get(lang, {}).get(key, None) or langs.get("en-US", {}).get(key, key)
