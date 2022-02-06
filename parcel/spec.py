from typing import Union
from uuid import uuid4

from . import parse_version, Version


def _split_spec(spec: str) -> list[str]:
    for oper in ('==', '<=', '>=', '=', '>', '<'):
        if oper in spec:
            spec, _, vers = spec.rpartition(oper)
            # NOTE: we allow = or ==, but convert to ==.
            if oper == '=':
                oper = '=='
            return spec, oper, parse_version(vers)
    return spec, None, None


class Spec:
    def __init__(self, name: str, version: str, oper: str = None,
                 uuid: str = None):
        self._version = None
        self.uuid = uuid or str(uuid4())
        self.name = name
        self.version = version
        self.oper = oper

    def __str__(self) -> str:
        parts = [self.name]
        if self.oper is not None:
            parts.append(self.oper)
        if self.version is not None:
            parts.append(str(self.version))
        return ''.join(parts)

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: 'Spec') -> bool:
        return self.name == other.name and self.oper == other.oper and \
               self.version == other.oper

    def __lt__(self, other: 'Spec') -> bool:
        assert self.oper == other.oper == '==', \
            'Specs must be absolute for comparison'
        if self.name != other.name:
            return False
        return self.version < other.version

    def __gt__(self, other: 'Spec') -> bool:
        assert self.oper == other.oper == '==', \
            'Specs must be absolute for comparison'
        if self.name != other.name:
            return False
        return self.version > other.version

    def __le__(self, other: 'Spec') -> bool:
        assert self.oper == other.oper == '==', \
            'Specs must be absolute for comparison'
        if self.name != other.name:
            return False
        return self.version <= other.version

    def __ge__(self, other: 'Spec') -> bool:
        assert self.oper == other.oper == '==', \
            'Specs must be absolute for comparison'
        if self.name != other.name:
            return False
        return self.version >= other.version

    @staticmethod
    def parse(spec: str) -> 'Spec':
        name, oper, version = _split_spec(spec)
        return Spec(name, version, oper=oper)

    @property
    def version(self) -> Version:
        return self._version

    @version.setter
    def version(self, value: Union[str, Version]):
        if isinstance(value, str):
            value = parse_version(value)
        self._version = value

    @property
    def requires(self):
        return []

    @property
    def conflicts(self):
        return []

    def satisfies(self, other):
        return other.is_satisfied_by(self)

    def is_satisfied_by(self, other):
        if self.name != other.name:
            # Names MUST match.
            return False

        if self.oper is None and self.version is None:
            # Name only match.
            return True
        elif other.oper != '==':
            # We can only compare against absolute versions.
            return False

        # Perform actual comparison based on operator.
        if self.oper == '==':
            return other.version == self.version
        elif self.oper == '>=':
            return other.version >= self.version
        elif self.oper == '<=':
            return other.version <= self.version
        elif self.oper == '>':
            return other.version > self.version
        elif self.oper == '<':
            return other.version < self.version
        elif self.oper == '!=':
            return other.version != self.version
        else:
            raise AssertionError(f'Invalid operator: {self.oper}')
