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

# TODO: Add hierarchical import from system, home, local dir

if settings_module in modules:
    try:
        namespace = {}
        execfile(_cwd+ '/' + settings_module + '.py', namespace)
        all_names = namespace.get("__all__")
        if all_names is None:
            all_names = (key for key in namespace if key[0] != "_")
        my_namespace = globals()
        for name in all_names:
            my_namespace[name] = namespace[name]
    except (ImportError, OSError):
        print 'Error importing settings from {}.py'.format(settings_module)
        sys.exit(1)

else:
    print 'Settings file {}/{}.py not found.'.format(_cwd, settings_module)
    sys.exit(1)