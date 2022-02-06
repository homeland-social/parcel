import os
import sys
import argparse
import stat

from binascii import hexlify
from pprint import pprint
from functools import wraps
from contextlib import contextmanager
from os.path import dirname, expanduser, splitext, join as pathjoin

from nacl.signing import SigningKey

from .parcel import Parcel


SUBCOMMANDS = {}
PARCEL_HOME = os.getenv('PARCEL_HOME', '~/.parcel/')
KEY_PATH = pathjoin(PARCEL_HOME, 'key')


def _error(msg, code=1):
    print(msg, file=sys.stderr)
    exit(code)


def _save_key(path, key, overwrite=False):
    with _create_file(path, overwrite=overwrite) as f:
        f.write(key.encode())


def _load_key(path):
    try:
        with open(path, 'rb') as f:
            return SigningKey(f.read())

    except FileNotFoundError:
        _error(f'Key file "{path}" does not exist, use keygen command to '
               f'generate one.')


@contextmanager
def _create_file(path, chmod=stat.S_IRUSR | stat.S_IWUSR, overwrite=False):
    mode = 'wb' if overwrite else 'xb'
    try:
        with open(path, mode) as f:
            os.fchmod(f.fileno(), chmod)
            yield f

    except FileExistsError:
        _error(f'Key file "{path}" exists, try --force')


def subcommand(f):
    SUBCOMMANDS[f.__name__] = f

    @wraps(f)
    def inner(*args, **kwargs):
        return f(*args, **kwargs)
    return inner


@subcommand
def keygen(args):
    """
    Generates a keypair for signing and verifying parcels.
    """
    parser = argparse.ArgumentParser(
        prog='parcel keygen', description=keygen.__doc__)
    parser.add_argument('--path', '-p', default=KEY_PATH)
    parser.add_argument('--force', '-f',  action='store_true')
    args = parser.parse_args(args)

    path = expanduser(args.path)
    try:
        os.makedirs(dirname(path))
    except FileExistsError:
        pass

    key = SigningKey.generate()
    _save_key(args.path, key, overwrite=args.force)


@subcommand
def build(args):
    """
    Build a parcel from a manifest.
    """
    parser = argparse.ArgumentParser(
        prog='parcel build', description=build.__doc__)
    parser.add_argument('manifest')
    parser.add_argument('--key', '-k', default=KEY_PATH, help='Path to load / save key')
    parser.add_argument('--keygen', '-g', action='store_true', help='generate new key')
    parser.add_argument('--force', '-f', action='store_true', help='Overwrite files')
    args = parser.parse_args(args)

    parcel = Parcel.load_manifest(args.manifest)
    path = splitext(args.manifest)[0] + '.pcl'

    if args.keygen:
        key = parcel.save_parcel(path, overwrite=args.force)
        _save_key(args.key, key, overwrite=args.force)

    else:
        key = _load_key(expanduser(args.key))
        parcel.save_parcel(path, key=key, overwrite=args.force)


@subcommand
def info(args):
    """
    Print information about a parcel.
    """
    parser = argparse.ArgumentParser(
        prog='parcel info', description=info.__doc__)
    parser.add_argument('path')
    args = parser.parse_args(args)

    try:
        parcel = Parcel.load_parcel(args.path, verify=True)

    except Exception:
        _error(f'Failed to load {args.path}')

    print('MANIFEST')
    pprint(parcel.manifest)
    print('SECURITY')
    pprint({
        'pubkey': hexlify(parcel.pubkey).decode(),
        'signature': hexlify(parcel.signature).decode(),
    })
    print('FILES')
    files = {
        f.name: f.value.getvalue().decode() for f in parcel.files
    }
    pprint(files)


@subcommand
def lint(args):
    """
    Lint a parcel.
    """
    # Parse the service definition and enumerate files.
    parser = argparse.ArgumentParser(
        prog='parcel lint', description=lint.__doc__)
    parser.add_argument('path')
    args = parser.parse_args(args)

    try:
        parcel = Parcel.load_parcel(args.path, verify=True)

    except Exception:
        _error(f'Failed to load {args.path}')

    try:
        parcel.lint()

    except AssertionError as e:
        _error(f'Linting error: "{e.args[0]}"')

    print('Linting success')


@subcommand
def download(args):
    """
    Download a parcel.
    """


@subcommand
def upload(args):
    """
    Upload a parcel.
    """


def main(args):
    """
    CLI tool for parcel package manager.
    """
    parser = argparse.ArgumentParser(
        prog='parcel', description=main.__doc__)
    parser.add_argument(
        'command', choices=SUBCOMMANDS.keys(), help='Subcommand')
    cmd_args, sub_args = args[1:2], args[2:]
    args = parser.parse_args(cmd_args)
    SUBCOMMANDS[args.command](sub_args)


main(sys.argv)
