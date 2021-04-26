from typing import Any, Dict, List, NamedTuple, Union


class Module(NamedTuple):
    name: str
    contents: Union[List[Any], Dict[Any, Any]]
