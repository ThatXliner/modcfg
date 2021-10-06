========
Features
========

ModCFG features the following:

 * :ref:`Enumerations <feature-enums>`
 * :ref:`Date and datetime <feature-dates>`
 * :ref:`Unicode and various other escape sequences <feature-escape>`
 * :ref:`Processed string literals <feature-string>`
 * :ref:`Modules <feature-modules>`


.. note::

	In this documentation, there will be several codeblocks like

    .. code-block:: yaml
        :caption: ModCFG document

        ...

    .. code-block:: python
        :caption: Python script

        ...

    and

    .. code-block:: python
        :caption: Expected output

        ...

    Please interpret the code in ``ModCFG Document`` as the ``DOC`` variable given in the ``Python script``\ s.

.. _feature-enums:

------------
Enumerations
------------

Let's say you have an enum `MyEnum` defined as

.. code-block:: python

    import enum
    class MyEnum(enum.Enum):
        is_cool = "we are swag"
        isnt_cool = "we are not swag"

And we want our clients to use that enum somewhere in the configuration format. Like this (in YAML format):

.. code-block:: yaml
    :caption: Example YAML file

    bob:
        personality: is_cool  # Pretend this is the enumeration
        hair color: brown
        loves yaml: no


Before we look at ModCFG, let's check out some other ways to implement an enumeration system.

JSON
====

JSON has no built-in support for enums so you'll need to turn to post-processors like JSONSchema.

YAML, TOML, INI, etc
====================
The same goes for YAML, TOML, INI, etc. They all don't have built-in enumeration support. You still have to turn to post-processing in order to implement an enum system.

ModCFG
======

But it's really easy to do with ModCFG's built-in enumeration support:

.. code-block:: yaml
    :caption: ModCFG document

    module "Bob":
        personality: :is_cool
        'hair color': brown
        'loves yaml': no

.. code-block:: python
   :caption: Python script

    import modcfg, enum


    class MyEnum(enum.Enum):  # Define the enum
        is_cool = "we are swag"
        isnt_cool = "we are not swag"

    output = modcfg.loads(
        DOC,
        enums=[MyEnum],  # Use the enum
    )
    print(output)

.. code-block:: python
    :caption: Expected output

    [
        Module(
            name="Bob",
            contents={
                "personality": <MyEnum.is_cool: 'we are swag'>,
                "hair color": "brown",
                "loves yaml": "no",
            },
        )
    ]

Epic, right? ModCFG has an exhaustive enumeration resolver which never fails silently unless explicitly requested so.

Here's another example:

.. code-block:: yaml
    :caption: ModCFG document

    module ThatXliner:
        personality = :is_cool
        hair_color => black
        coder = true
    module SomePythoniast:
        hates = :polymorphism
        loves = :duck_typing

.. code-block:: python
   :caption: Python script

    import modcfg, enum


    class MyFirstEnum(enum.Enum):
        is_cool = "we are swag"
        isnt_cool = "we are not swag"


    class MySecondEnum(enum.Enum):
        polymorphism = "sucks"
        duck_typing = "is cool"

    print(
        modcfg.loads(
            DOC,
            enums=[MyFirstEnum, MySecondEnum],
        )
    )

.. code-block:: python
    :caption: Expected output

    [
        Module(
            name="ThatXliner",
            contents={
                "personality": <MyFirstEnum.is_cool: 'we are swag'>,
                "hair_color": "black",
                "coder": True,
            },
        ),
        Module(
            name="SomePythoniast",
            contents={
                "hates": <MySecondEnum.polymorphism: 'sucks'>,
                "loves": <MySecondEnum.duck_typing: 'is cool'>,
            },
        ),
    ]



But there are cases were there are *ambiguous enums*. If that's the case, ModCFG will, if you **didn't explicitly silence it**, :ref:`fail on ambiguous enums <ambiguous-enums>`


.. _ambiguous-enums:

Ambigous Enumerations
=====================

If there's ambiguous enums, ModCFG's exhaustive enumeration resolver will raise a :py:exc:`modcfg.errors.EnumResolveError` like so:

.. code-block:: yaml
    :caption: ModCFG document

    module Story:
        is_made_by_a: :duck_typing  # NANI!?
    mod Python:
        has = :duck_typing

.. code-block:: python
   :caption: Python script

    import modcfg, enum


    class Enum1(enum.Enum):
        duck_typing = "DUCKS CAN TYPE!!?"
        human_typing = "Much better"


    class Enum2(enum.Enum):
        polymorphism = "sucks"
        duck_typing = "is cool"

    print(
        modcfg.loads(
            DOC,
            enums=[Enum1, Enum2],
        )
    )

.. code-block:: python
    :caption: Expected output

    Traceback (most recent call last):
        ...
    modcfg.errors.EnumResolveError: Ambigous enumerations: <Enum1.duck_typing: 'DUCKS CAN TYPE!!?'>, <Enum2.duck_typing: 'is cool'>


Really, **there shouldn't have ambiguous keys**.

But if you really need to, you can silence the ambiguity checker by setting the ``enum_ambiguity_check`` parameter to `False` for :py:func:`modcfg.loads`. It'll return the first found result instead (i.e. making ModCFG guess which one you want, in the order of enums given in the `enums` argument).

But if you *do* find the need for enumerations with ambiguous keys and don't want ModCFG to guess, you can use the *enum namespace specifier* like so:

.. code-block:: yaml
    :caption: ModCFG document

    module Story:
        is_made_by_a: :Enum1.duck_typing  # Can ducks type?
    mod Python:
        has = :Enum2.duck_typing

.. code-block:: python
    :caption: Python script

    import modcfg, enum


    class Enum1(enum.Enum):
        duck_typing = "DUCKS CAN TYPE!!?"
        human_typing = "Much better"


    class Enum2(enum.Enum):
        polymorphism = "sucks"
        duck_typing = "is cool"

    print(
        modcfg.loads(
            DOC,
            enums=[Enum1, Enum2],
        )
    )

.. code-block:: python
    :caption: Expected output

    [
        Module(
            name="Story",
            contents={"is_made_by_a": <Enum1.duck_typing: 'DUCKS CAN TYPE!!?'>},
        ),
        Module(
            name="Python", contents={"has": <Enum2.duck_typing: 'is cool'>},
        ),
    ]

.. _feature-modules:

-------
Modules
-------
ModCFG features serialization of hashable objects called *modules*. They're actually :py:obj:`NamedTuple <typing.NamedTuple>`\ s that contain 2 slots:

 * name: The name of the module
 * contents: The module contents

The thing is, ModCFG currently doesn't treat a list of modules like dictionaries where one module with the same name as one defined earlier can overwrite said module defined earlier.

Not required
============
Instead of limiting ModCFG to a configuration format that requires modules, I decided I wanted it to also be a data format: a YAML-like alternative:

>>> import modcfg
>>> DOC = """
... bruh:
...    yaml: {
...        kinda:
...            - works
...            - {    this: [is,
...
...                insane]
...
...     }
...    }
    """
>>> print(modcfg.loads(DOC))
[{'bruh': {'yaml': {'kinda': ['works', {'this': ['is', 'insane']}]}}}]


Want to remove those unnecessary brackets around it which denotes a list? Set the `inline` parameter of :py:func:`modcfg.loads` to `True`. What this does is that if, **and only if**, the parsed and evaluated values is a **one-element list**, then it'll return *that one element*.

Why is the default a list? That way, one can define multiple modules in a document, like this:

.. code-block:: yaml
    :caption: ModCFG document

    module "Module one!":
        some: content
    mod "Module 2.":
        some: 'more content!'

.. code-block:: python
    :caption: Python script

    import modcfg

    print(modcfg.loads(DOC))

.. code-block:: python
    :caption: Expected output

    [
        Module(name="Module one!", contents={"some": "content"}),
        Module(name="Module 2.", contents={"some": "more content!"}),
    ]

Or even (*shudder*)

.. code-block:: yaml
    :caption: ModCFG document

    module "Module one!":
        some: content
    [loving]
    {weird: stuff}

.. code-block:: python
    :caption: Python script

    import modcfg

    print(modcfg.loads(DOC))

.. code-block:: python
    :caption: Expected output

    [
        Module(name="Module one!", contents={"some": "content"}),
        ["loving"],
        {"weird": "stuff"},
    ]

.. _feature-dates:

-------------------
Datetimes and dates
-------------------

ModCFG supports datetimes and dates:

.. code-block:: yaml
    :caption: ModCFG document

    mod 'Date example':
        today = datetime(2021-04-18 14:50:55.016922)
        tomorrow = date(2021-04-19)

.. code-block:: python
    :caption: Python script

    import modcfg
    print(modcfg.loads(DOC))

.. code-block:: python
    :caption: Expected output

    [
        Module(
            name="Date example",
            contents=[
                {
                    "today": datetime.datetime(2021, 4, 18, 14, 50, 55, 16922),
                    "tomorrow": datetime.date(2021, 4, 19),
                }
            ],
        )
    ]

.. <details>
..
.. <summary>Why is it <code>date()</code> and <code>datetime()</code>?</summary>
..
.. Because if I wanted to use the "clean" syntax, I would have to shove a really long regex. And we all know [regexes suck](https://xkcd.com/1171/).
..
.. So really, it's for the parser. For now, at least.
..
.. </details>


.. _feature-string:

-------
Strings
-------

Single-line strings can be single quoted (``'``) or double quoted (``"``). You can leave out the quotes if the string contents matches the following regex:

:regexp:`[a-zA-Z_]\\w*`

Multiline strings can also be single or double quoted. They are denoted with 2 quote characters.

Both (multiline or single-line) strings may be prefixed with ``t``, ``l``, or ``r`` this is what they mean:

t
    Dedent the string's contents (uses :py:func:`textwrap.dedent`).
l
    Run :py:meth:`str.lstrip` on the string's contents.
r
    Run :py:meth:`str.rstrip` on the string's contents. Very similar to ``l``.

.. warning::

	When prefixing, you must put ``t``, ``l``, or ``r`` in that exact order.

.. _feature-escape:

Escaping characters
===================

You can create unicode characters using the ``\uXXXX`` escape sequence. The ``u`` is case-insensitive

Example:

>>> import modcfg
>>> print(modcfg.loads(R'{main: "\U0001f642"}'))
[{'main': '🙂'}]



.. seealso::

    https://docs.python.org/3/howto/unicode.html#unicode-literals-in-python-source-code

-----------------
Future restraints
-----------------

Key-value separation characters
===============================

Currently, I can't decide whether the key separation character (the `:` in `{hello: world}`) should be which character. So I made it the following characters letting *you* decide.

 * **:** Good ol' colon
 * **=>** Fat arrow
 * **->** Skinny arrow
 * **=** Equal sign

I may make a poll in the future.

Module definition keywords
==========================
Currently, you can use either ``mod`` or ``module`` to define a module.

In the future, I plan to limit it to either one or the other.
