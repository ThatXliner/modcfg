import ast
import datetime
import enum
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Union

import lark.indenter

from . import components, errors, utils

here: Path = Path(__file__).parent


class Indenter(lark.indenter.Indenter):
    NL_type = "_NL"
    OPEN_PAREN_types: List[str] = ["_OPEN_BRACKET", "_OPEN_BRACE"]
    CLOSE_PAREN_types: List[str] = ["_CLOSE_BRACKET", "_CLOSE_BRACE"]
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 4


class MainTransformer(lark.Transformer):
    # pylint: disable=R0201,C0116,C0103
    ALL_NUMBERS = lambda self, x: ast.literal_eval(x)  # type: ignore
    CNAME = lambda self, x: str(x)  # type: ignore
    # TODO: dateutil for full iso support
    def DATE(self, x: str) -> datetime.date:
        clean = utils.FUNCTIONS["date"].search(x).group(1)
        try:
            return datetime.date.fromisoformat(clean)
        except ValueError as error:
            raise errors.InvalidDateFormat("Invalid date format: %s" % clean) from error

    def DATETIME(self, x: str) -> datetime.datetime:
        clean = utils.FUNCTIONS["datetime"].search(x).group(1)
        try:
            return datetime.datetime.fromisoformat(clean)
        except ValueError as error:
            raise errors.InvalidDateFormat("Invalid date format: %s" % clean) from error

    # DATE = lambda self, x: datetime.date.fromisoformat(x.strip()[5:-1])
    # DATETIME = lambda self, x: datetime.datetime.fromisoformat(x[9:-1])
    dict = dict
    list = list
    NULL = lambda _, __: None  # type: ignore
    BOOLEAN = lambda _, thing: str(thing).strip() == "true"  # type: ignore
    pair = tuple

    def start(self, stuff: List[str]) -> Any:
        if self._options["inline"] and len(stuff) == 1:  # Inlining
            return stuff[0]
        return stuff

    def __init__(self, *args, **kwargs) -> None:
        self._options: Dict[str, Union[List[enum.Enum], bool]] = kwargs
        super().__init__(*args)

    def MULTILINE_STR(self, text: str) -> str:
        return utils.parse_strings(3, text)

    def STRING(self, text: str) -> str:
        return utils.parse_strings(1, text)

    def module(self, stuff) -> components.Module:  # type: ignore
        args = stuff

        return components.Module(
            name=args[0],
            contents=args[1],
        )  # TODO: Use dicts instead

    def ENUM(self, given: str) -> Union[str, enum.Enum]:  # TODO: Add abiguity finding
        # TODO: Refactor this
        if not self._options["enums"]:
            if self._options["enum_resolve_fail_silently"] is True:
                return str(given)
            raise errors.EnumResolveError(f"Could not resolve enum for {given}")
        thing = str(given[1:])
        parsed = thing.split(".", 1)
        if len(parsed) == 1:  # No enum name specifier
            assert thing == parsed[0]
            possibles = []
            for entry in self._options["enums"]:
                vmap = dict(entry.__members__)
                if thing in vmap:
                    if self._options["enum_ambiguity_check"] is False:
                        return vmap[thing]  # Short circut
                    possibles.append(vmap.pop(thing))
            if len(possibles) > 1:
                raise errors.EnumResolveError(
                    "Ambigous enumerations: {}".format(", ".join(map(repr, possibles)))
                )
            if len(possibles) == 0:
                if self._options["enum_resolve_fail_silently"] is True:
                    return str(given)
                raise errors.EnumResolveError(f"Could not resolve enum for {given}")
            assert len(possibles) == 1
            return possibles[0]
        assert len(parsed) == 2
        for entry in self._options["enums"]:
            if parsed[0] == entry.__name__:
                vmap = dict(entry.__members__)
                if parsed[1] in vmap:
                    return vmap[parsed[1]]
        if self._options["enum_resolve_fail_silently"] is True:
            return str(given)
        raise errors.EnumResolveError(f"Could not resolve enum for {given}")


grammar = lark.Lark(
    here.joinpath("grammar.lark").read_text(),
    postlex=Indenter(),
    parser="lalr",
    maybe_placeholders=True,
)
