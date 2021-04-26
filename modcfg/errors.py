from typing import Dict, List, NamedTuple, Optional, Type


class Error(NamedTuple):
    desc: str
    help_text: Optional[str] = None


class ModCFGError(Exception):
    """Base error class for ModCFG."""


class ModCFGSyntaxError(ModCFGError):
    """There was an error parsing the ModCFG document"""


class InvalidEscape(ModCFGSyntaxError):
    """You used an invalid escape sequence"""


class InvalidDateFormat(ModCFGSyntaxError):
    """Your date(time)s cannot be parsed"""

    label: Error = Error(
        "Your date(time)s cannot be parsed",
        "Remember, it's ISO 8601 format (TODO: Full ISO 8601 support). (YYYY-MM-DD for dates,\n"
        "YYYY-MM-DD[*HH[:MM[:SS[.fff[fff]]]][+HH:MM[:SS[.ffffff]]]] for datetimes)",
    )


class DumpError(ModCFGError):
    """Failed to dump"""


class EnumResolveError(ModCFGError):
    """There was an error when resolving enumeration(s)"""


class EmptyBody(ModCFGSyntaxError):
    label: Error = Error(
        "Your module body is empty", "Try adding stuff to the body of your module"
    )


class BadIndentation(ModCFGSyntaxError):
    label: Error = Error(
        "Your indentaton is inconsistent",
        "Did you mean to make the indentation the same?",
    )


class Y_U_NO_TEXT(ModCFGSyntaxError):
    label: Error = Error("There is no content to parse", "Try adding some content")


class BadName(ModCFGSyntaxError):
    label: Error = Error(
        "Your name is not valid", "Just so you know, it should not start with a number"
    )


class BadKeyChar(ModCFGSyntaxError):
    label: Error = Error(
        "The keys are not valid",
        "That there are no newlines before and after it",
    )


class InvalidKeyChar(ModCFGSyntaxError):
    label: Error = Error(
        "The keys are not valid",
        "Make sure the keys are either one of the following characters:\n - {}".format(
            "\n - ".join(map(repr, (":", "=>", "=", "->")))
        ),
    )


class MixedModuleContents(ModCFGSyntaxError):
    label: Error = Error(
        "The keys are not valid",
        "You can only put a dict or a list in a module, mutually exclusive",
    )


ERROR_MAP: Dict[Type[ModCFGSyntaxError], List[str]] = {
    EmptyBody: ["""mod a:"""],
    BadIndentation: ["""mod s:\n - e\n  - e"""],
    Y_U_NO_TEXT: ["", "\n", "\n   \n"],
    BadName: [
        "mod s:\n 1 = 1\n",
        "mod s:\n e = e\n 1 = 1\n",
        "mod s:\n w = null #eeeee\n 1 = 1\n",
        "mod a:\n b = c #eeeee\n 1 = 1\n",
    ],
    InvalidKeyChar: ["mod a:\n    b * c"],
    MixedModuleContents: [
        "mod a:\n    a=b\n     - b",
        "mod a:\n    a = b\n    - c\n    b = b",
    ],
    InvalidDateFormat: ["{main: date(a)}", "{main:datetime(b)}"],
}
