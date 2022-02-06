from unittest import TestCase
from pprint import pprint

from parcel.manifest import Manifest
from parcel.solver import Solver


PACKAGES = [
    Manifest({
        'name': 'foo',
        'version': '1.0',
        'requires': [
            'bar==1.0',
        ],
    }),
    Manifest({
        'name': 'foo',
        'version': '2.0',
        'requires': [
            'bar==2.0',
        ],
    }),
    Manifest({
        'name': 'bar',
        'version': '1.0',
        'requires': [
            'foo==1.0',
        ],
    }),
    Manifest({
        'name': 'bar',
        'version': '2.0',
        'requires': [
            'foo==2.0',
        ],
    }),
    Manifest({
        'name': 'quux',
        'version': '1.0',
        'conflicts': [
            'foo',
            'bar'
        ],
        'requires': [
            'schmoo',
        ],
    }),
    Manifest({
        'name': 'baz',
        'version': '1.0',
        'provides': [
            'schmoo',
        ]
    }),
]


INSTALLED = [
    PACKAGES[0], PACKAGES[2]
]


class SolverTestCase(TestCase):
    def setUp(self):
        self.solver = Solver()
        for manifest in PACKAGES:
            self.solver.add_spec(manifest)

    def test_install_foo_2(self):
        solutions = list(self.solver.solve(INSTALLED, [PACKAGES[1]]))
        self.assertEqual(1, len(solutions))
        install, remove = solutions[0]
        self.assertEqual(2, len(install))
        self.assertEqual(2, len(remove))
