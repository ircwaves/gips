import sys

try:
    from .base import *
except ImportError:
    print 'You have no settings file configured. Copy template.py to base.py and modify for your use.'
    sys.exit()    
