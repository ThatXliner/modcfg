import toml
import modcfg
from pathlib import Path
import importlib

VERSION = modcfg.__version__


def test_pyproject():
    assert (
        toml.loads(Path(__file__).parent.parent.joinpath("pyproject.toml").read_text())[
            "tool"
        ]["poetry"]["version"]
        == VERSION
    )


def test_doc():
    importlib.import_module("docs.conf").release = VERSION
