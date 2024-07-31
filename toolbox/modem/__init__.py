__author__ = 'Wijnand Modderman <maze@pyth0n.org>'
__copyright__ = [
    'Copyright (c) 2010 Wijnand Modderman-Lenstra',
    'Copyright (c) 1981 Chuck Forsberg'
]
__license__ = 'MIT'
__version__ = '0.2.4'

import gettext

from toolbox.modem.protocol.xmodem import XModem
from toolbox.modem.protocol.xmodem1k import XModem1K
from toolbox.modem.protocol.xmodemcrc import XModemCrc
from toolbox.modem.protocol.ymodem import YModem
from toolbox.modem.protocol.zmodem import ZModem

gettext.install('modem')

# To satisfy import *
__all__ = [
    'XModem',
    'XModem1K',
    'XModemCrc',
    'YModem',
    'ZModem',
]
