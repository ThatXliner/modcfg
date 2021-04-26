# ModCFG
![YEs](./noo.png)

[![codecov](https://codecov.io/gh/ThatXliner/modcfg/branch/master/graph/badge.svg)](https://codecov.io/gh/ThatXliner/modcfg) [![Documentation Status](https://readthedocs.org/projects/modcfg/badge/?version=latest)](https://modcfg.readthedocs.io/en/latest/?badge=latest) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![CI](https://github.com/ThatXliner/modcfg/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/ThatXliner/modcfg/actions/workflows/ci.yml)

> YEs, another configuration language

Seriously, how many configuration languages do we have? From the top of my head, I can only name:

 - [JSON](https://www.json.org/)
 - [YAML](https://yaml.org)
 - [INI](https://wikipedia.org/wiki/INI_file)
 - [TOML](https://toml.io/)
 - [XML](https://www.w3.org/XML/)

Hmmm... that's *it* I think. wE NeEd MOrE cOnfIGURaTion LanGuaGEs!!1!1!!

## But actually though

I originally based this off of the Ruby/DSL for homebrew formulas.

Here are my complaints for the alternatives:

 - JSON, while simple, isn't too readable and **only has the bear minimum of datatypes.** That may be a feature for some people, though.
 - YAML is [**dangerous**](https://www.arp242.net/yaml-config.html#insecure-by-default). And [**unpredictable**](https://hitchdev.com/strictyaml/why/implicit-typing-removed/).
 - INI and TOML are quite similar and they both are quite nice with a lot of datatypes but, in my opinion, **the format isn't as natural to read as YAML**. TOML supports dates and datetime, though.
 - Finally, XML is garbage. It's barely human-readable and can decode into a super wonky format. So no.

Finally, I just wanted an excuse to play with Lark.

### Features

 - Enums with a built-in resolver
 - Date time and Date support
 - YAML-like syntax
 - Support for comments, **unicode escape sequences**, **string modifications**, and **cleanly managed indented strings**

### Examples

Given this modcfg document:
```yaml
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
```
and this python script:
```py
import modcfg
modcfg.loads(DOC)  # `DOC` is the document above
```
The output is
```py
[
    Module(
        name="hello_world",
        contents=[
            {
                "hello": "world",
                "this": "also works",
                "single quotes": "equals double quotes",
                "how": {
                    "about": {
                        "some": ["very", "crazy", {"data": {"structures": "o_0"}}]
                    }
                },
            }
        ],
    )
]
```
Crazy, right? It gets better with enums and date(time)s... You might as well read the whole [documentation][documentation].

## Installation

I have not uploaded this to the PyPi. You must develop-install instead.

The classic method:

```bash
$ git clone https://github.com/ThatXliner/modcfg.git
$ cd modcfg
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -e .
```

The best method (requires [Poetry](https://python-poetry.org/)):

```bash
$ git clone https://github.com/ThatXliner/modcfg.git
$ cd modcfg
$ poetry install
```

## FAQ

### Why did you make this

![why](./why.png)

[Lark](https://github.com/lark-parser/lark) is epic.

### Why the name?

**Mod**ular **C**on**f**i**g**uration language.

[documentation]: ./docs
