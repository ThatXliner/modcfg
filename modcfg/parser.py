# TODO: Support for single values

import datetime
import enum
import textwrap
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import lark
import lark.indenter

from . import components, errors, lark_components, utils

# TODO: Better type hints


def loads(
    s: str,
    enums: Optional[List[enum.Enum]] = None,
    enum_resolve_fail_silently: bool = False,
    enum_ambiguity_check: bool = True,
    inline: bool = False,
) -> Union[
    Union[components.Module, List[Any], Dict[str, Any]],
    List[Union[components.Module, List[Any], Dict[str, Any]]],
]:
    """Serializes the document, `s`, to Python objects.

    Args:
        s (str): The ModCFG document to parse and evaluate.
        enums (Optional[List[enum.Enum]]): The list of Python enums that should be serialized from in the document. Defaults to None.
        enum_resolve_fail_silently (bool): Implicitly convert enum values to `str` if couldn't resolve the enum. Defaults to True.
        enum_ambiguity_check (bool): Fail if the enums given are ambigous. Defaults to True.
        inline (bool): Inline the output. See docs for more details. Defaults to False.

    Returns:
        Union[Union[components.Module, List[Any], Dict[str, Any]],List[Union[components.Module, List[Any], Dict[str, Any]]]]: The serialized Python object.

    Raises:
        `errors.ModCFGError`: There was an error processing your document

    :canonical: modcfg.parser
    """
    # We must do the tree separately because we're also parsing indentation
    # See https://github.com/lark-parser/lark/issues/818
    transformer = lark_components.MainTransformer(
        enums=enums,
        enum_resolve_fail_silently=enum_resolve_fail_silently,
        inline=inline,
        enum_ambiguity_check=enum_ambiguity_check,
    )
    try:
        tree = lark_components.grammar.parse(s)
    except lark.exceptions.UnexpectedInput as parse_error:
        error: Type[errors.ModCFGSyntaxError] = parse_error.match_examples(
            lark_components.grammar.parse, errors.ERROR_MAP, use_accepts=True
        )
        if error is None:  # pragma: no cover
            raise
        raise error(
            parse_error.get_context(s),
            parse_error.line,  # pylint: disable=E1101
            parse_error.column,  # pylint: disable=E1101
        ) from parse_error
    else:
        try:
            return transformer.transform(tree)
        except lark.exceptions.VisitError as error:
            raise error.orig_exc


T = TypeVar("T")


def _unparse(
    thing: Union[
        str,
        List[T],
        Dict[str, T],
        datetime.date,
        datetime.datetime,
        enum.Enum,
        None,
        bool,
    ],
    # enums: Optional[List[enum.Enum]] = None,
) -> str:
    if isinstance(thing, bool):
        return "true" if thing else "false"
    if isinstance(thing, (str, float, int)):
        return repr(thing)
    if isinstance(thing, list):
        return "[" + ", ".join(_unparse(k) for k in thing) + "]"
    if isinstance(thing, dict):
        return (
            "{"
            + ", ".join(f"{_unparse(k)}: {_unparse(v)}" for k, v in thing.items())
            + "}"
        )
    if isinstance(thing, (datetime.date, datetime.datetime)):
        return f"{thing.__class__.__name__}({thing})\n"
    if thing is None:
        return "null"
    if isinstance(thing, enum.Enum):
        return ":" + thing.__class__.__name__ + "." + thing.name
    raise errors.DumpError(f"Failed to dump object {type(thing).__name__}")


def _dump_module(module: components.Module) -> str:
    # if len(module.contents) == 0:
    #     raise errors.EmptyBody(
    #         f"components.Module must contain something (module {module.name!r} of arg `module`)"
    #     )
    output = f"mod {module.name}:\n"
    inner = ""
    inner += textwrap.indent(_unparse(module.contents).strip("\n"), utils.INDENT)
    return output + inner + "\n"


def dumps(
    objects: Union[
        List[T],
        Dict[str, T],
        components.Module,
    ],
) -> str:
    R"""Converts objects to `str` that can be `loads`\ ed back.

    Basically `json.dumps` but for ModCFG.

    Args:
        objects (Union[List[Any], Dict[str, Any], components.Module]): The objects to dump.

    Returns:
        str: Returns the dumped `str`.

    Raises:
        `errors.DumpError`: Invalid object (couldn't dump it)

    :canonical: modcfg.parser
    """
    output = ""
    if isinstance(objects, components.Module):  # Single module
        return _dump_module(objects)
    if isinstance(objects, (list, dict)):
        # if not objects:
        #     raise ValueError("Dict must contain something.")
        for obj in objects:
            if isinstance(obj, components.Module):
                output += _dump_module(obj)
            else:
                output += _unparse(obj)
    else:
        # raise ValueError("Must be a list or dict of stuff")
        output += _unparse(objects)
    return textwrap.dedent(output.strip("\n"))
