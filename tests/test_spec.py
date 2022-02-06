from unittest import TestCase

from parameterized import parameterized

from parcel.spec import Spec


class SpecTestCase(TestCase):
    @parameterized.expand([
        ('foobar=1.0', 'foobar=1.0.0'),
        ('foobar>=1.0', 'foobar=1.0'),
        ('foobar>=1.0', 'foobar=2.0'),
        ('foobar==1.0', 'foobar=1.0'),
    ])
    def test_satisfiability(self, spec1, spec2):
        spec1, spec2 = Spec.parse(spec1), Spec.parse(spec2)
        self.assertTrue(spec1.is_satisfied_by(spec2))
        self.assertTrue(spec2.satisfies(spec1))

    @parameterized.expand([
        ('foobar>=1.0', 'barfoo=1.0'),
        ('foobar>1.0', 'foobar=1.0'),
        ('foobar==1.0', 'foobar=1.0.1'),
    ])
    def test_negative_equality(self, spec1, spec2):
        spec1, spec2 = Spec.parse(spec1), Spec.parse(spec2)
        self.assertFalse(spec1 == spec2)

    @parameterized.expand([
        ('foobar==1.0.1', 'foobar==1.0'),
    ])
    def test_gt(self, spec1, spec2):
        spec1, spec2 = Spec.parse(spec1), Spec.parse(spec2)
        self.assertGreater(spec1, spec2)

    @parameterized.expand([
        ('foobar==0.99', 'foobar==1.0'),
    ])
    def test_lt(self, spec1, spec2):
        spec1, spec2 = Spec.parse(spec1), Spec.parse(spec2)
        self.assertLess(spec1, spec2)

    @parameterized.expand([
        ('foobar==1.0', 'foobar==1.0'),
        ('foobar==1.0.1', 'foobar==1.0'),
    ])
    def test_gte(self, spec1, spec2):
        spec1, spec2 = Spec.parse(spec1), Spec.parse(spec2)
        self.assertGreaterEqual(spec1, spec2)

    @parameterized.expand([
        ('foobar==1.0', 'foobar==1.0'),
        ('foobar==0.99', 'foobar==1.0'),
    ])
    def test_lte(self, spec1, spec2):
        spec1, spec2 = Spec.parse(spec1), Spec.parse(spec2)
        self.assertLessEqual(spec1, spec2)

    @parameterized.expand([
        ('foobar>=1.0', 'foobar==1.0'),
    ])
    def test_cmp_invalid(self, spec1, spec2):
        spec1, spec2 = Spec.parse(spec1), Spec.parse(spec2)
        with self.assertRaises(AssertionError):
            self.assertGreater(spec1, spec2)
        with self.assertRaises(AssertionError):
            self.assertLess(spec1, spec2)
