import time
import tarfile
from typing import Union, TextIO
from contextlib import contextmanager

from . import parse_version


@contextmanager
def path_or_file(path: Union[str, TextIO], mode: str = 'rb'):
    opened, f = (False, path) if not isinstance(path, str) else \
                (True, open(path, mode))
    try:
        yield f

    finally:
        if opened:
            f.close()


def add_tar_file(tf, name, fileobj, mtime=None):
    if mtime is None:
        mtime = time.time()
    tinfo = tarfile.TarInfo(name)
    tinfo.type = tarfile.REGTYPE
    tinfo.mtime = mtime
    tinfo.size = fileobj.getbuffer().nbytes
    fileobj.seek(0)
    tf.addfile(tinfo, fileobj=fileobj)


def read_tar_file(tf, name):
    return tf.extractfile(name).read()
