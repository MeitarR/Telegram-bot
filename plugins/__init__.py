from plugins import *
from os.path import dirname, basename, isfile
import glob


def do_import(mud_name):
    globals()[mud_name] = __import__(mud_name)

modules = glob.glob(dirname(__file__) + "/*.py")
__all__ = \
    [
        basename(f)[:-3]
        for f in modules
        if isfile(f) and not f.endswith('__init__.py')
    ]

[do_import('plugins.' + name) for name in __all__]
