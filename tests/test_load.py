import os
import tempfile

from io import BytesIO
from unittest import TestCase
from os.path import dirname, getsize, join as pathjoin

from pkg_resources import parse_version

from parcel.parcel import path_or_file, Manifest, Parcel
from parcel.attrs import Setting


EXAMPLE_JSON = pathjoin(dirname(__file__), 'example.json')
EXAMPLE_PCL = pathjoin(dirname(__file__), 'example.pcl')
EXAMPLE_YML = pathjoin(dirname(__file__), 'example.yml')
EXAMPLE_CFG = pathjoin(dirname(__file__), 'example.cfg')


class ParcelTestCase(TestCase):
    def test_path_or_file_file(self):
        with tempfile.NamedTemporaryFile() as f:
            with path_or_file(f) as f:
                f.write(b'test')
            self.assertFalse(f.closed)

    def test_path_or_file_path(self):
        with tempfile.NamedTemporaryFile() as f:
            with path_or_file(f.name, 'wb') as f:
                f.write(b'test')
            self.assertTrue(f.closed)

    def test_load_json(self):
        parcel = Manifest.load_manifest(EXAMPLE_JSON)
        self.assertIsNone(parcel.lint())
        self.assertEqual('example', parcel.name)
        self.assertEqual(parse_version('0.9.8'), parcel.version)
        self.assertIsNotNone(parcel.uuid)
        self.assertEqual("example.yml", parcel.service_definition)
        self.assertEqual("example.cfg", parcel.files[0].name)
        self.assertEqual(Setting("SHANTY_OAUTH_TOKEN"), parcel.settings[0])

        option = parcel.options[0]
        self.assertEqual("OPTION_A_ENABLED", option.name)
        self.assertEqual("boolean", option.type)
        self.assertEqual("Toggles option A", option.description)
        self.assertEqual(True, option.default)
        self.assertIsNone(option.value)

    def test_load_file(self):
        parcel = Parcel.load_parcel(EXAMPLE_PCL)
        self.assertIsNone(parcel.lint())
        self.assertEqual('example', parcel.name)
        self.assertEqual(parse_version('0.9.8'), parcel.version)
        self.assertIsNotNone(parcel.uuid)
        self.assertEqual("example.yml", parcel.service_definition)
        self.assertEqual("example.cfg", parcel.files[0].name)
        self.assertEqual(Setting("SHANTY_OAUTH_TOKEN"), parcel.settings[0])

    def test_load_corrupt(self):
        size, bio = getsize(EXAMPLE_PCL), BytesIO()
        with open(EXAMPLE_PCL, 'rb') as f:
            # Flip all 7 bits in ASCII
            for i in range(127):
                char = bytes(chr(i), 'utf8')
                # Replace each byte position in turn with current char.
                for ii in range(size):
                    f.seek(0)
                    bio.truncate()
                    if ii != 0:
                        bio.write(f.read(ii))
                    bio.write(char)
                    f.seek(ii + 1)
                    bio.write(f.read())
                    self.assertEqual(
                        f.tell(), bio.tell(), f'i={i} char={char} ii={ii}')
                    bio.seek(0)

                    # Should not load successfully
                    with self.assertRaises(Exception):
                        Parcel.load(bio)
