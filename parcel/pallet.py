from typing import Generator

from .spec import Spec


class Pallet:
    def __init__(self):
        self._count = 0
        self._specs = {}
        self._names = {}

    def add_spec(self, spec: Spec):
        self._count += 1
        self._specs[self._count] = spec
        self._names.setdefault(spec.name, {})[str(spec.version)] = self._count

    def get(self, id: int) -> Spec:
        return self._specs[id]

    def all(self) -> Generator[Spec, None, None]:
        yield from self._specs.items()

    def search(self, spec: Spec) -> \
            Generator[tuple[int, Spec], None, None]:
        try:
            ids = self._names[spec.name].values()

        except KeyError:
            return

        for id in ids:
            other = self._specs[id]
            if other.satisfies(spec):
                yield id, other
