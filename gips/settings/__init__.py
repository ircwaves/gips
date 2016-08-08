import os, sys, glob, importlib

DEFAULT = 'default'

try:
    from .base import *
except ImportError:
    print 'You have no base settings file, but it is required.'
    sys.exit(1)


settings_module = os.environ.get('GIPS_SETTINGS_FILE', DEFAULT)

_cwd = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))
print _cwd
files = glob.glob(_cwd+"/*.py")
modules = map(lambda s: os.path.basename(s)[:-3], files)


def merge(a, b):
    ''' source:
        http://stackoverflow.com/questions/19378143/python-merging-two-arbitrary-data-structures
    '''
    if isinstance(a, dict) and isinstance(b, dict):
        d = dict(a)
        d.update({k: merge(a.get(k, None), b[k]) for k in b})
        return d

    if isinstance(a, list) and isinstance(b, list):
        return [merge(x, y) for x, y in itertools.izip_longest(a, b)]

    return a if b is None else b


# TODO: Add hierarchical import from system, home, local dir

if settings_module in modules:
    try:
        ''' source: http://effbot.org/zone/import-string.htm '''
        namespace = {}
        execfile(_cwd+ '/' + settings_module + '.py', namespace)
        all_names = namespace.get("__all__")
        if all_names is None:
            all_names = (key for key in namespace if key[0] != "_")
        my_namespace = globals()
        for name in all_names:
            my_namespace[name] = merge(
                my_namespace.get(name), namespace.get(name)
            )
    except (ImportError, OSError):
        print 'Error importing settings from {}.py'.format(settings_module)
        sys.exit(1)

else:
    print 'Settings file {}/{}.py not found.'.format(_cwd, settings_module)
    sys.exit(1)
