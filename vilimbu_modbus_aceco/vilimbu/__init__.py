'''
vilimbu: Modbus Protocol Implementation
-----------------------------------------


Released under the the BSD license
'''

import vilimbu.version as __version
__version__ = __version.version.short()
__author__  = 'vilimbu'
__maintainer__ = 'vilimbu'

#---------------------------------------------------------------------------#
# Block unhandled logging
#---------------------------------------------------------------------------#
import logging as __logging
try:
    from logging import NullHandler as __null
except ImportError:
    class __null(__logging.Handler):
        def emit(self, record):
            pass

__logging.getLogger(__name__).addHandler(__null())

