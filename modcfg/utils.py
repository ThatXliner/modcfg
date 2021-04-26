import re
import textwrap
from typing import Dict, Match, Pattern

# from . import errors

_unescape_map: Dict[str, str] = {
    '"': '"',
    "'": "'",
    "/": "/",
    "\\": "\\",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}

_unescape_re: Pattern[str] = re.compile(
    r"\\"  # Non-escaped Escaping Backslash
    + r"(["
    + "".join(map(re.escape, _unescape_map))  # Anything in _unescape_map
    + r"]|(?:u[0-9A-Fa-f]{4})|(?:U[0-9A-Fa-f]{8})|(?:x[0-9A-Fa-f]{2}))"  # Or unicode
)


def _unescape(match: Match[str]) -> str:
    char = match.group(1)
    if char[0] in {"u", "U", "x"}:  # Unicode
        return chr(int(char[1:], 16))
    return _unescape_map[char]


def parse_escape(s: str) -> str:
    return _unescape_re.sub(_unescape, s)


INDENT: str = " " * 4


def _function(name: str) -> Pattern[str]:
    return re.compile(name + r"\s*\(\s*(.+)\s*\)")


FUNCTIONS: Dict[str, Pattern[str]] = {
    "datetime": _function("datetime"),
    "date": _function("date"),
}


def parse_strings(str_char_len: int, text: str) -> str:
    actions = []
    output = text[:-str_char_len]

    if output.startswith("t"):
        output = output[1:]
        assert not output.startswith("t")
        actions.append(textwrap.dedent)
    if output.startswith("l"):
        output = output[1:]
        assert not output.startswith("l")
        actions.append(lambda x: x.lstrip())
    if output.startswith("r"):
        output = output[1:]
        assert not output.startswith("r")
        actions.append(lambda x: x.rstrip())

    output = output[str_char_len:]
    for action in actions:
        output = action(output)
    return str(parse_escape(output))
