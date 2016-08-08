import os, sys, glob, importlib

DEFAULT = 'default'

try:
    from .base import *
except ImportError:
    print 'You have no base settings file, but it is required.'
    sys.exit(1)


settings_module = os.environ.get('GIPS_SETTINGS_FILE', DEFAULT)

_cwd = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))

files = glob.glob(_cwd+"/*.py")
modules = map(lambda s: os.path.basename(s)[:-3], files)

if settings_module in modules:
    try:
        eval('from {} import *'.format(settings_module))
    except ImportError, OSError:
        print 'Error importing settings from {}.py'.format(settings_module)
        sys.exit(1)

else:
    print 'Settings file {}/{}.py not found.'.format(_cwd, settings_module)
    sys.exit(1)