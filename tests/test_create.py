from unittest import TestCase
from os.path import join as pathjoin, dirname
from io import BytesIO

from parameterized import parameterized

from parcel import Version
from parcel.parcel import Parcel, Manifest
from parcel.attrs import Setting, Option
from parcel.spec import Spec


EXAMPLE_JSON = pathjoin(dirname(__file__), 'example.json')
EXAMPLE_YML = pathjoin(dirname(__file__), 'example.yml')
EXAMPLE_CFG = pathjoin(dirname(__file__), 'example.cfg')


class ParcelCreateTestCase(TestCase):
    def setUp(self):
        self.parcel = Manifest()

    def test_create_name(self):
        self.parcel.name = 'foobar'
        self.assertEqual('foobar', self.parcel.name)

    def test_create_version(self):
        self.parcel.version = '1.0.8'
        self.assertEqual(Version('1.0.8'), self.parcel.version)

    def test_create_service_definition(self):
        with self.assertRaises(AssertionError):
            self.parcel.service_definition = 'foobar.yml'
        self.parcel.service_definition = EXAMPLE_YML

    def test_create_files(self):
        with self.assertRaises(AssertionError):
            self.parcel.files = ['foobar.cfg']
        self.parcel.files = [EXAMPLE_CFG]

    def test_create_options_dict(self):
        self.parcel.options = []
        self.assertEqual(0, len(self.parcel.options))
        self.parcel.options = {
            'OPTION_A': {
                'type': 'bool',
                'description': 'An option that toggles A',
                'default': True,
                'value': False,
            }
        }
        self.assertEqual(1, len(self.parcel.options))
        self.assertEqual('OPTION_A', self.parcel.options[0].name)
        self.assertEqual('bool', self.parcel.options[0].type)
        self.assertEqual('An option that toggles A', self.parcel.options[0].description)
        self.assertEqual(True, self.parcel.options[0].default)
        self.assertEqual(False, self.parcel.options[0].value)

    def test_create_options_obj(self):
        self.parcel.options = [
            Option('OPTION_A', 'bool', 'An option that toggles A', True, False),
        ]
        self.assertEqual(1, len(self.parcel.options))
        self.assertEqual('OPTION_A', self.parcel.options[0].name)
        self.assertEqual('bool', self.parcel.options[0].type)
        self.assertEqual('An option that toggles A', self.parcel.options[0].description)
        self.assertEqual(True, self.parcel.options[0].default)
        self.assertEqual(False, self.parcel.options[0].value)

    def test_create_settings_dict(self):
        self.parcel.settings = []
        self.assertEqual(0, len(self.parcel.settings))
        self.parcel.settings = {
            'SETTING_A': 'foobar'
        }
        self.assertEqual(1, len(self.parcel.settings))
        self.assertEqual('SETTING_A', self.parcel.settings[0].name)
        self.assertEqual('foobar', self.parcel.settings[0].value)

    def test_create_settings_list(self):
        self.parcel.settings = ['SETTING_A']
        self.assertEqual(1, len(self.parcel.settings))
        self.assertEqual('SETTING_A', self.parcel.settings[0].name)
        self.assertIsNone(self.parcel.settings[0].value)

    def test_create_settings_obj(self):
        self.parcel.settings = [
            Setting('SETTING_A', 'foobar'),
        ]
        self.assertEqual(1, len(self.parcel.settings))
        self.assertEqual('SETTING_A', self.parcel.settings[0].name)
        self.assertEqual('foobar', self.parcel.settings[0].value)

    @parameterized.expand([
        'requires',
        'conflicts',
    ])
    def test_create_spec_str(self, attr_name):
        setattr(self.parcel, attr_name, ['foobar=1.0.8'])
        obj = getattr(self.parcel, attr_name)
        self.assertEqual(1, len(obj))
        obj = obj[0]
        self.assertEqual('foobar', obj.name)
        self.assertEqual('==', obj.oper)
        self.assertEqual(Version('1.0.8'), obj.version)

    @parameterized.expand([
        'requires',
        'conflicts',
    ])
    def test_create_spec_obj(self, attr_name):
        setattr(self.parcel, attr_name, [Spec('foobar', '1.0.8', '=')])
        obj = getattr(self.parcel, attr_name)
        self.assertEqual(1, len(obj))
        obj = obj[0]
        self.assertEqual('foobar', obj.name)
        self.assertEqual('=', obj.oper)
        self.assertEqual(Version('1.0.8'), obj.version)


class ParcelSaveTestCase(TestCase):
    def test_save_parcel(self):
        parcel = Parcel(name='example', version='1.0.8',
                        description='An example parcel.',
                        service_definition=EXAMPLE_YML)
        parcel.add_file(EXAMPLE_CFG)
        parcel.options = {
            'SETTING_ONE': {
                'description': 'An option that toggles ONE.',
                'type': 'bool',
                'default': False,
            },
        }
        parcel.settings = ['OPTION_A']
        parcel.requires = ['other==1.0']
        self.assertIsNone(parcel.lint())

        bio = BytesIO()
        key = parcel.save_parcel(bio)
        bio.seek(0)

        # Ensure we can load what we saved.
        loaded = Parcel.load_parcel(bio, verify=True)
        self.assertIsNone(loaded.lint())
        self.assertEqual(parcel.name, loaded.name)
        self.assertEqual(parcel.version, loaded.version)
        self.assertEqual(parcel.uuid, loaded.uuid)
        self.assertEqual(2, len(parcel.files))
