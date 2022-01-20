import tarfile

import pgp


class Parcel:
    def __init__(self, manifest):
        self.manifest = manifest
        self.signatures = signatures

    @property
    def files(self):
        pass

    @property
    def options(self):
        pass

    @property
    def settings(self):
        pass

    @staticmethod
    def _load(path):
        pass

    @staticmethod
    def load(path, verify=True):
        parcel = Parcel._load(path)
        if verify:
            parcel.verify()
        return parcel

    def verify(self):
        pass

    def configure(self, options, settings):
        self.option_values = options
        self.settings_values = settings

    def write(self, path):
        pass


def load(path, *args, **kwargs):
    return Parcel.load(path, *args, **kwargs)


def create(path):
    pass
