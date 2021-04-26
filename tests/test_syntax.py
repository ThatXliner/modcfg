import datetime
import enum
import string
import sys
from textwrap import dedent as _

import modcfg
import pytest
from modcfg import Module

# TODO: Test Errors


def test_single_mod():
    assert (
        modcfg.loads(
            _(
                """
                mod a:
                    b = c
                """
            )
        )
        == modcfg.loads("module a:\n\tb -> c")
        == modcfg.loads("module a:\n\tb: c")
        == modcfg.loads("module a:\n\tb : c")
        == modcfg.loads("module a:\n\tb => c")
        == modcfg.loads("module a:\n\tb =>c")
        == modcfg.loads("module a:\n\tb=>c")
        == [Module("a", {"b": "c"})]
    )


def test_multiple_mod():
    assert modcfg.loads(
        _(
            """
            mod a:
                b = c
            mod b:
                c = d
            module c:
                d = e
            """
        )
    ) == [
        Module("a", {"b": "c"}),
        Module("b", {"c": "d"}),
        Module("c", {"d": "e"}),
    ]


def test_no_module():
    assert (
        modcfg.loads(
            _(
                """bruh:
                json: {
                    kinda:
                        - works
                        - {this: [is, insane]}
                }
            """
            )
        )
        == [{"bruh": {"json": {"kinda": ["works", {"this": ["is", "insane"]}]}}}]
    )


class TestStuffInReadme:
    def test_initial(self):
        DOC = _(
            """
            module hello_world:
                hello => world
                this: "also works"
                'single quotes' = "equals double quotes"
                how -> {
                        about: {
                            some:
                                - very
                                - crazy
                                - data:
                                    structures = o_0
                        }
                    }
            """
        )
        DOC2 = _(
            """




            module hello_world:
                hello => world


                this: "also works"
                'single quotes' = "equals double quotes"
                how ->

                        {
                        about: {
                            some:

                                - very



                                - crazy
                                - data:
                                    structures = o_0
                        }
                    }
            """
        )
        assert (
            modcfg.loads(DOC)
            == modcfg.loads(DOC2)
            == [
                Module(
                    name="hello_world",
                    contents={
                        "hello": "world",
                        "this": "also works",
                        "single quotes": "equals double quotes",
                        "how": {
                            "about": {
                                "some": [
                                    "very",
                                    "crazy",
                                    {"data": {"structures": "o_0"}},
                                ]
                            }
                        },
                    },
                )
            ]
        )

    def test_datetimes_and_dates(self):
        DOC = _(
            """
            mod 'Date example':
                today = datetime(2021-04-18 14:50:55.016922)
                tomorrow = date(2021-04-19)
            """
        )
        assert (
            modcfg.loads(DOC)
            == modcfg.loads(DOC.replace("mod", "module"))
            == [
                Module(
                    name="Date example",
                    contents={
                        "today": datetime.datetime(2021, 4, 18, 14, 50, 55, 16922),
                        "tomorrow": datetime.date(2021, 4, 19),
                    },
                )
            ]
        )

    def test_enums(self):
        class MyEnum(enum.Enum):
            is_cool = "we are swag"
            isnt_cool = "we are not swag"

        DOC = _(
            """
            module "Bob":
                personality: :is_cool
                'hair color': brown
                'loves yaml': no
            """
        )
        assert (
            modcfg.loads(DOC, enums=[MyEnum])
            == modcfg.loads(DOC.replace("module", "mod"), enums=[MyEnum])
            == [
                Module(
                    name="Bob",
                    contents={
                        "personality": MyEnum.is_cool,
                        "hair color": "brown",
                        "loves yaml": "no",
                    },
                )
            ]
        )

    def test_more_enums(self):
        DOC = _(
            """
            module ThatXliner:
                personality = :is_cool
                hair_color => brown
                coder = true
            module SomePythoniast:
                hates = :polymorphism
                loves = :duck_typing
            """
        )

        class MyFirstEnum(enum.Enum):
            is_cool = "we are swag"
            isnt_cool = "we are not swag"

        class MySecondEnum(enum.Enum):
            polymorphism = "sucks"
            duck_typing = "is cool"

        assert modcfg.loads(DOC, enums=[MyFirstEnum, MySecondEnum],) == [
            Module(
                name="ThatXliner",
                contents={
                    "personality": MyFirstEnum.is_cool,
                    "hair_color": "brown",
                    "coder": True,
                },
            ),
            Module(
                name="SomePythoniast",
                contents={
                    "hates": MySecondEnum.polymorphism,
                    "loves": MySecondEnum.duck_typing,
                },
            ),
        ]

    def test_yaml_like(self):
        DOC = _(
            """
            bruh:
                yaml: {
                    kinda:
                        - works
                        - {    this: [is,

                            insane]

                 }
                }
            """
        )
        assert modcfg.loads(DOC) == [
            {"bruh": {"yaml": {"kinda": ["works", {"this": ["is", "insane"]}]}}}
        ]
        assert modcfg.loads(DOC, inline=True) == {
            "bruh": {"yaml": {"kinda": ["works", {"this": ["is", "insane"]}]}}
        }

    def test_enum_explicit(self):
        DOC = _(
            """
            module Story:
                is_made_by_a: :Enum1.duck_typing  # NANI!?
            mod Python:
                has = :Enum2.duck_typing
            """
        )

        class Enum1(enum.Enum):
            duck_typing = "DUCKS CAN TYPE!!?"
            human_typing = "Much better"

        class Enum2(enum.Enum):
            polymorphism = "sucks"
            duck_typing = "is cool"

        assert modcfg.loads(DOC, enums=[Enum1, Enum2],) == [
            Module(
                name="Story",
                contents={"is_made_by_a": Enum1.duck_typing},
            ),
            Module(
                name="Python",
                contents={"has": Enum2.duck_typing},
            ),
        ]


class Enum1(enum.Enum):
    duck_typing = "DUCKS CAN TYPE!!?"
    human_typing = "Much better"


class Enum2(enum.Enum):
    polymorphism = "sucks"
    duck_typing = "is cool"


class TestResolveEnum:
    def test_fail_on_ambiguity(self):
        DOC = _(
            """
            module Story:
                is_made_by_a: :duck_typing  # NANI!?
            mod Python:
                has = :duck_typing
            """
        )
        with pytest.raises(modcfg.errors.EnumResolveError):
            modcfg.loads(
                DOC,
                enums=[Enum1, Enum2],
            )

    def test_ignore_ambiguity_is_deterministic(self):
        DOC = _(
            """
            module Story:
                is_made_by_a: :duck_typing  # NANI!?
            mod Python:
                has = :duck_typing
            """
        )
        assert modcfg.loads(DOC, enums=[Enum1, Enum2], enum_ambiguity_check=False) == [
            Module("Story", {"is_made_by_a": Enum1.duck_typing}),
            Module("Python", {"has": Enum1.duck_typing}),
        ]
        assert modcfg.loads(DOC, enums=[Enum2, Enum1], enum_ambiguity_check=False) == [
            Module("Story", {"is_made_by_a": Enum2.duck_typing}),
            Module("Python", {"has": Enum2.duck_typing}),
        ]

    def test_impossible_enum_resolve_will_fail(self):
        DOC = _(
            """
            module Story:
                is_made_by_a: :duck_typing  # NANI!?
            mod Python:
                has = :duck_typing
            """
        )

        class WeirdEnum(enum.Enum):
            useless = True

        with pytest.raises(modcfg.errors.EnumResolveError):
            modcfg.loads(DOC)
        with pytest.raises(modcfg.errors.EnumResolveError):
            modcfg.loads(DOC, enums=[])

        assert (
            modcfg.loads(DOC, enum_resolve_fail_silently=True)
            == [
                Module(name="Story", contents={"is_made_by_a": ":duck_typing"}),
                Module(name="Python", contents={"has": ":duck_typing"}),
            ]
            == modcfg.loads(DOC, enums=[WeirdEnum], enum_resolve_fail_silently=True)
        )
        with pytest.raises(modcfg.errors.EnumResolveError):
            modcfg.loads(DOC, enums=[WeirdEnum])
        with pytest.raises(modcfg.errors.EnumResolveError):
            modcfg.loads("""{main: :e.e}""", enums=[WeirdEnum])
        assert modcfg.loads(
            """{main: :e.e}""", enums=[WeirdEnum], enum_resolve_fail_silently=True
        ) == [{"main": ":e.e"}]


def test_mixed_module_bad():
    with pytest.raises(modcfg.errors.MixedModuleContents):
        modcfg.loads(
            _(
                """
                mod a:
                    a = a
                    b = b
                    - c
                """
            )
        )
    with pytest.raises(modcfg.errors.MixedModuleContents):
        modcfg.loads(
            _(
                """
                mod a:
                    a = a
                    - b
                    - c
                """
            )
        )
    with pytest.raises(modcfg.errors.MixedModuleContents):
        modcfg.loads(
            _(
                """
                mod a:
                    a = a
                    - b
                    c = c
                """
            )
        )


def test_invalid_escape():
    assert (
        modcfg.loads(
            "{" + "main: " + R"'\x'" + "}",
            inline=True,
        )["main"]
        == R"\x"
    )


class TestInvalidDatesAndDatetimes:
    def test_raises_on_invalid_date(self):
        with pytest.raises(modcfg.errors.InvalidDateFormat):
            modcfg.loads("{main: date(random junk that's definetly not a date lol)}")
        with pytest.raises(modcfg.errors.InvalidDateFormat):
            modcfg.loads("{main: date(9/9/1111)}")
        assert modcfg.loads("{main: date(1111-09-01)}", inline=True)[
            "main"
        ] == datetime.date(1111, 9, 1)
        with pytest.raises(modcfg.errors.InvalidDateFormat):
            modcfg.loads("{main: date(1*9-1111)}")
        with pytest.raises(modcfg.errors.InvalidDateFormat):
            modcfg.loads("{main: date(1-9/1111)}")
        with pytest.raises(modcfg.errors.InvalidDateFormat):
            modcfg.loads("{main: date(1111-99-01)}")

    def test_raises_on_invalid_datetime(self):
        with pytest.raises(modcfg.errors.InvalidDateFormat):
            modcfg.loads(
                "{main: datetime(random junk that's definetly not a datetime lol)}"
            )
        with pytest.raises(modcfg.errors.InvalidDateFormat):
            modcfg.loads("{main: date(2021-04-25 21:99:07.573107)}")
        with pytest.raises(modcfg.errors.InvalidDateFormat):
            modcfg.loads("{main: date(1-04-25 21:17:07.573107)}")
