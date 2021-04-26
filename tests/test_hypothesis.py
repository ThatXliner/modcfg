# TODO: Try to use string.printable
# Hypothesis will be more slower

import re
import string
import sys
from enum import Enum
from functools import lru_cache

import modcfg.parser
from hypothesis import HealthCheck, assume, given, settings, reproduce_failure
from hypothesis import strategies as st
from modcfg import Module

NON_DIGIT = "".join(set(string.ascii_letters) - set(string.digits))


def utf8_encodable(terminal: str) -> bool:
    try:
        terminal.encode(encoding="utf8")
        return True
    except UnicodeEncodeError:  # pragma: no cover
        # Very rarely, a "." in some terminal regex will generate a surrogate
        # character that cannot be encoded as UTF-8.  We apply this filter to
        # ensure it doesn't happen at runtime, but don't worry about coverage.
        return False


@lru_cache()
def identifiers() -> st.SearchStrategy[str]:
    _lead = []
    _subs = []
    for char in map(chr, range(sys.maxunicode + 1)):
        if not utf8_encodable(char):
            continue
        if char.isidentifier():
            _lead.append(char)  # e.g. "a"
        if ("_" + char).isidentifier():
            _subs.append(char)  # e.g. "1"
    pattern = "[{}][{}]*".format(re.escape("".join(_lead)), re.escape("".join(_subs)))
    return st.from_regex(pattern, fullmatch=True).filter(str.isidentifier)


#
#
# class MyEnum:
#     a = "a"
#     b = "b"
#     c = "c"
#     d = 1
#     e = auto()


@st.composite
def module(draw):
    return Module(
        draw(variable_names()),
        contents=draw(
            st.one_of(
                st.lists(generate_dumpable(), max_size=5),
                st.dictionaries(variable_names(), generate_dumpable(), max_size=5),
            ),
        ),
    )


@st.composite
def name(draw):
    return draw(
        st.from_regex(
            "("
            + r't?l?r?(("""(?:\s|.)*?(?<!\\)(\\\\)*?""")|('
            + r"'''(?:\s|.)*?(?<!\\)(\\\\)*?'''))'"
            + ")|("
            + r'l?r?(("(?!"").*?(?<!\\)(\\\\)*?"|'
            + r"'(?!'').*?(?<!\\)(\\\\)*?'))"
            + ")|("
            + r"[a-zA-Z_]\w*"
            + ")",
        ).filter(lambda x: x in string.ascii_letters)
    )


@st.composite
def variable_names(draw):  # XXX: When we have unicode support
    return draw(st.text(alphabet=NON_DIGIT, min_size=1, max_size=5)) + draw(
        st.text(string.ascii_letters, max_size=5)
    )


@st.composite
def enum_variable_names(draw):
    output = draw(variable_names())
    assume(not (output.startswith("_") and output.endswith("_")))
    return output


@st.composite
def generate_enum(draw):
    return draw(
        st.builds(
            Enum,
            variable_names(),
            st.dictionaries(enum_variable_names(), st.text(), min_size=1, max_size=5),
        )
    )


def generate_dumpable():
    return st.one_of(
        st.lists(_generate_dumpable(), max_size=5),
        st.dictionaries(variable_names(), _generate_dumpable(), max_size=5),
    )


@st.composite
def _generate_dumpable(draw):
    output = draw(
        st.recursive(
            name()
            | st.integers()
            | st.datetimes()
            | st.dates()
            | st.sampled_from(draw(generate_enum()))
            | st.none()
            | st.booleans(),
            lambda children: st.lists(children)
            | st.dictionaries(keys=name(), values=children),
            max_leaves=5,
        )
    )

    return output


@settings(
    suppress_health_check=[HealthCheck(2), HealthCheck(3)]
)  # Ignore 'filter-too-much' and 'too-slow'
@given(
    enum_resolve_fail_silently=st.just(True),
    enums=st.one_of(st.none(), st.lists(generate_enum())),
    objects=st.one_of(
        st.lists(st.one_of(generate_dumpable(), module()), min_size=1, max_size=5),
        module(),
    ),
)
def test_roundtrip_loads_dumps(enum_resolve_fail_silently, enums, objects):
    s = modcfg.parser.dumps(objects=objects)
    try:
        value0 = modcfg.parser.loads(
            s=s, enums=enums, enum_resolve_fail_silently=enum_resolve_fail_silently
        )
    except modcfg.errors.EnumResolveError:  # XXX
        pass
    else:
        value1 = modcfg.parser.dumps(objects=value0)
        assert value0 == modcfg.loads(
            value1, enums=enums, enum_resolve_fail_silently=enum_resolve_fail_silently
        ), (s, value0, value1)


@given(
    stuff=st.characters(min_codepoint=0, max_codepoint=sys.maxunicode + 1).filter(
        lambda x: x not in string.whitespace + string.ascii_letters
    )
)
def test_unicode_escapes(stuff):
    assert (
        modcfg.loads(
            "{"
            + "main: "
            + repr(stuff.encode("unicode_escape", errors="backslashreplace"))[
                1:
            ].replace("\\\\", "\\")
            + "}",
            inline=True,
        )["main"]
        == stuff
    )
