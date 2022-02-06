import json
from typing import Union, TextIO
from os.path import dirname, basename, isfile, join as pathjoin

import yaml

from . import Version
from .attrs import File, Setting, Option
from .spec import Spec
from .utils import path_or_file


class Manifest(Spec):
    """Deals with metadata. Read-only."""

    def __init__(self, manifest: dict = None, name: str = None,
                 version: Union[str, Version] = None, uuid: str = None,
                 description: str = None, service_definition: str = None,
                 files: list[Union[str, File]] = None):
        self._manifest = manifest or {}
        name = name or self._manifest.get('name')
        version = version or self._manifest.get('version')
        uuid = uuid or self._manifest.get('uuid')
        super().__init__(name=name, version=version, uuid=uuid, oper='==')
        self._options = []
        self._settings = []
        self._requires = []
        self._conflicts = []
        self._files = []
        self.description = description or self._manifest.get('description')
        self.options = self._manifest.get('options', [])
        self.settings = self._manifest.get('settings', [])
        self.requires = self._manifest.get('requires', [])
        self.conflicts = self._manifest.get('conflicts', [])
        self.files = files or self._manifest.get('files', [])
        if service_definition or 'service_definition' in self._manifest:
            self.service_definition = service_definition or \
                self._manifest.get('service_definition')

    @classmethod
    def load_manifest(cls, path: Union[str, TextIO]) -> 'Manifest':
        dir = dirname(path) if isinstance(path, str) else dirname(path.name)
        with path_or_file(path) as f:
            manifest = json.load(f)
        kwargs = {
            'manifest': manifest,
        }
        sd = manifest.pop('service_definition', None)
        if sd:
            kwargs['service_definition'] = File(pathjoin(dir, sd))
        files = manifest.pop('files', None)
        if files:
            kwargs['files'] = [File(pathjoin(dir, fn)) for fn in files]
        return cls(**kwargs)

    def save_manifest(self, path: Union[str, TextIO]):
        with path_or_file(path, 'wb') as f:
            json.dump(self.manifest, f)

    @property
    def manifest(self) -> dict:
        manifest = self._manifest.copy()
        manifest['name'] = self.name
        manifest['version'] = str(self.version)
        manifest['uuid'] = self.uuid
        manifest['options'] = [
            {
                'name': option.name,
                'type': option.type,
                'description': option.description,
                'default': option.default,
            } for option in self._options
        ]
        manifest['settings'] = [
            setting.name for setting in self._settings
        ]
        for attr_name in ('requires', 'conflicts'):
            manifest[attr_name] = [str(s) for s in getattr(self, attr_name)]
        manifest['files'] = [f.name for f in self.files]
        return manifest

    @property
    def description(self) -> str:
        return self._manifest.get('description')

    @description.setter
    def description(self, value: str):
        self._manifest['description'] = value

    @property
    def service_definition(self) -> File:
        return self._manifest.get('service_definition')

    @service_definition.setter
    def service_definition(self, value: Union[str, File]):
        if isinstance(value, str):
            value = File(value)
        self.del_file(value.name)
        self.add_file(value)
        self._manifest['service_definition'] = value.name

    @property
    def options(self) -> list[Option]:
        return self._options

    @options.setter
    def options(self, value: Union[dict, list[dict], list[Option]]):
        if value and isinstance(value, dict):
            value = [
                Option(name, **o) for name, o in value.items()
            ]
        elif value and isinstance(value, list) and isinstance(value[0], dict):
            value = [Option(**o) for o in value]
        self._options = value

    @property
    def settings(self) -> list[Setting]:
        return self._settings

    @settings.setter
    def settings(self, value: Union[dict, list[str], list[Setting]]):
        if value and isinstance(value, dict):
            value = [Setting(name, value) for name, value in value.items()]
        elif value and isinstance(value[0], str):
            value = [Setting(name) for name in value]
        self._settings = value

    @property
    def requires(self) -> list[Spec]:
        return self._requires

    @requires.setter
    def requires(self, value: Union[list[str], list[Spec]]):
        if value and isinstance(value[0], str):
            value = [Spec.parse(s) for s in value]
        self._requires = value

    @property
    def conflicts(self) -> list[Spec]:
        return self._conflicts

    @conflicts.setter
    def conflicts(self, value: Union[list[str], list[Spec]]):
        if value and isinstance(value[0], str):
            value = [Spec.parse(s) for s in value]
        self._conflicts = value

    @property
    def files(self) -> list[File]:
        return self._files

    @files.setter
    def files(self, value: Union[list[str], list[File]]):
        if value and isinstance(value[0], str):
            value = [File(fn) for fn in value]
        self._files = value

    def add_file(self, file: Union[str, File]):
        if isinstance(file, str):
            file = File(file)
        self._files.append(file)

    def del_file(self, name: str):
        for i, file in enumerate(self._files):
            if file.name == name:
                del self._files[i]
                return

    def get_file(self, name: str) -> Union[File, None]:
        for i, file in enumerate(self._files):
            if file.name == name:
                return file

    def parse_service_definition(self) -> dict:
        return yaml.load(
            self.get_file(self.service_definition).value,
            Loader=yaml.SafeLoader)

    def lint(self):
        """
        Check manifest and service_distribution for errors.

        Look for:
         - missing service distribution
         - missing config files
         - extra files
        """
        sd_name = self.service_definition

        if not sd_name:
            _error('No service definition')

        assert self.get_file(sd_name), \
            'Service definition file "{sd_name}" missing'

        sd = self.parse_service_definition()
        # pprint(sd)

        config_names = [o['file'] for o in sd.get('configs', {}).values()]
        for fn in config_names:
            assert self.get_file(fn), f'Config file "{fn}" missing'

        allowed_names = [sd_name]
        allowed_names.extend(config_names)

        # Check for extra files.
        extra_files = [
            file.name for file in self.files if file.name not in allowed_names
        ]
        assert len(extra_files) == 0, f'Extra files in parcel: {extra_files}.'
