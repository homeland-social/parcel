"Parcel package and metadata handling."

import json
import tarfile
from os.path import isdir
from typing import Union, TextIO
from io import BytesIO

from nacl.signing import SigningKey, VerifyKey

from .utils import add_tar_file, read_tar_file, path_or_file
from .attrs import File
from .manifest import Manifest


class Parcel(Manifest):
    """Deals with package files. Can modify properties."""

    def __init__(self, **kwargs):
        self.signature = kwargs.pop('signature', None)
        self.pubkey = kwargs.pop('pubkey', None)
        super().__init__(**kwargs)

    @staticmethod
    def load_parcel(path: Union[str, TextIO], verify: bool = True) -> 'Parcel':
        with path_or_file(path) as f:
            outer = tarfile.open(fileobj=f, mode='r:gz')
            try:
                pubkey = outer.extractfile('pubkey').read()
                message = outer.extractfile('message').read()
                signature = outer.extractfile('signature').read()

            finally:
                outer.close()

            if verify:
                key = VerifyKey(pubkey)
                key.verify(message, signature)

            inner = tarfile.open(fileobj=BytesIO(message), mode='r')
            try:
                manifest = json.loads(read_tar_file(inner, 'manifest.json'))
                kwargs = {
                    'pubkey': pubkey,
                    'signature': signature,
                    'manifest': manifest,
                }
                sd = manifest.pop('service_definition', None)
                if sd:
                    kwargs['service_definition'] = \
                        File(sd, value=read_tar_file(inner, sd))
                files = manifest.get('files')
                if files:
                    kwargs['files'] = [
                        File(fn, value=read_tar_file(inner, fn))
                        for fn in files
                    ]
                return Parcel(**kwargs)

            finally:
                inner.close()

    def save_parcel(self, path: Union[str, TextIO], key: bytes = None,
                    overwrite: bool = False) -> SigningKey:
        iio = BytesIO()
        inner = tarfile.open(fileobj=iio, mode='w')
        try:
            add_tar_file(
                inner,
                'manifest.json',
                BytesIO(json.dumps(self.manifest).encode('utf8'))
            )

            for file in self.files:
                add_tar_file(inner, file.name, file.value)

        finally:
            inner.close()

        iio.seek(0)
        if key is None:
            key = SigningKey.generate()

        signed = key.sign(iio.getvalue())
        self.pubkey = key.verify_key.encode()
        self.signature = signed.signature

        mode = 'xb' if not overwrite else 'wb'
        with path_or_file(path, mode) as f:
            outer = tarfile.open(fileobj=f, mode='w:gz')
            try:
                add_tar_file(outer, 'message', BytesIO(signed.message))
                add_tar_file(outer, 'signature', BytesIO(signed.signature))
                add_tar_file(outer, 'pubkey', BytesIO(self.pubkey))

            finally:
                outer.close()

        return key

    def configure(self, options: dict, settings: dict):
        assert set(options.keys()) == set(self.options.keys()), \
            "Incomplete options"
        assert set(settings) == set(self.settings.keys()),  \
            "Incomplete settings"
        self._option_values = options
        self._settings_values = settings

    def generate(self, path: Union[str, TextIO]):
        assert isdir(path), 'Must output to a directory'
