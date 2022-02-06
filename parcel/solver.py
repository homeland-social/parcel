"Simple package manager, dependency solver."

import itertools
import logging
from typing import Generator

import pycosat

from .pallet import Pallet
from .spec import Spec


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


class Solver:
    def __init__(self):
        self.pallet = Pallet()

    def _packages_cnf(self) -> Generator[list[int], None, None]:
        for id, spec in self.pallet.all():
            # Only one version of each package can be installed at a time.
            query = Spec(spec.name, spec.version, oper='!=')
            for sid, s in self.pallet.search(query):
                if id == sid:
                    continue
                yield [-id, -sid]
            # Handle conflicts, if any.
            for c in spec.conflicts:
                state = [-id]
                state.extend([-id for id, _ in self.pallet.search(c)])
                yield state
            # Handle requires, if any.
            for r in spec.requires:
                state = [-id]
                state.extend([id for id, _ in self.pallet.search(r)])
                yield state

    def _installed_cnf(self, installed: list[Spec]) -> \
            Generator[list[int], None, None]:
        # Add all available versions of each installed package where the
        # version is >= the installed version.
        for spec in installed:
            query = Spec(spec.name, spec.version, oper='>=')
            yield [id for id, _ in self.pallet.search(query)]

    def _selected_cnf(self, selected: list[Spec]) -> \
            Generator[list[int], None, None]:
        for spec in selected:
            yield [id for id, _ in self.pallet.search(spec)]

    def _print_exp(self, exp: list[int], pre: str = ''):
        def _format(id):
            sign = '+' if id > 0 else '-'
            spec = self.pallet.get(abs(id))
            return f'{sign}{spec.name}-{spec.version}'

        LOGGER.debug(pre + ', '.join(map(_format, exp)))

    def _debug(self, cnf: list[int]) -> Generator[list[int], None, None]:
        for o in cnf:
            self._print_exp(o, pre='Repo ')
            yield o

    def add_spec(self, *args, **kwargs):
        "Adds spec to list of available parcels"
        return self.pallet.add_spec(*args, **kwargs)

    def solve(self, installed: list[Spec], selected: list[Spec]) -> \
            Generator[tuple[list[Spec], list[Spec]], None, None]:
        """
        Solves package installation dependencies.

        Accepts a list of specs for what is currently installed as well as a
        list of specs for what is desired.

        Returns a generator of possible solutions in the form of a tuple of:
        (install, remove)

        Where isntall is a list of specs to install, and remove is a list of
        specs to remove.
        """
        cnf = itertools.chain(
            self._packages_cnf(),
            self._installed_cnf(installed),
            self._selected_cnf(selected)
        )
        ids = []
        for i in installed:
            ids.extend([id for id, _ in self.pallet.search(i)])
        cnf = self._debug(cnf)
        for sol in pycosat.itersolve(cnf):
            self._print_exp(sol, pre='Solv ')
            yield (
                [
                    self.pallet.get(id) for id in sol if id > 0
                ],
                [
                    self.pallet.get(abs(id))
                    for id in sol if id < 0 and abs(id) in ids
                ],
            )
