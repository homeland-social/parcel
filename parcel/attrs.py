from io import BytesIO
from typing import Union, Any
from os.path import (
    isfile, basename, join as pathjoin, split as pathsplit
)


class Option:
    def __init__(self, name: str, type: str, description: str, default: Any,
                 value: Any = None):
        self.name = name
        self.type = type
        self.description = description
        self.default = default
        self.value = value

    def __eq__(self, other: 'Option') -> bool:
        return self.name == other.name


class Setting:
    def __init__(self, name: str, value: Any = None):
        self.name = name
        self.value = value

    def __eq__(self, other):
        return self.name == other.name


class File:
    def __init__(self, path: str, value: Union[bytes, BytesIO] = None):
        self._value = None
        if value is None:
            assert isfile(path), f'Path "{path}" does not exist'
            self.name = basename(path)
            with open(path, 'rb') as f:
                self.value = BytesIO(f.read())
        else:
            self.name = basename(path)
            self.value = value

    @property
    def value(self) -> BytesIO:
        return self._value

    @value.setter
    def value(self, value: Union[bytes, BytesIO]):
        if isinstance(value, bytes):
            value = BytesIO(value)
        self._value = value
