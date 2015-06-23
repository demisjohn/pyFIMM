'''pyFIMM's Global Variables
Contains/defines global variables - most importantly the fimmwave connection object `fimm`.

This separate file is required to prevent circular module imports, and enable nested-modules to use the FimmWave connection.
'''

import numpy as np
import matplotlib.pyplot as plt

'''
# import some pyFIMM objects/functions for global access from within the module:
## for Mode.py:
import pylab as pl
#import matplotlib.pyplot as plt
from pylab import cm    # color maps
#import numpy as np
import math
import os  # for filepath manipulations (os.path.join/os.mkdir/os.path.isdir)
from __pyfimm import get_N, get_wavelength

## For Device.py
from __pyfimm import Node, Project, Material, Layer, Slice
from __Waveguide import Waveguide   # rectangular waveguide class
from __Circ import Circ        # cylindrical (fiber) waveguide class
from __Tapers import Taper, Lens      # import Taper/WGLens classes
from __Mode import Mode     # import Mode class


## for pyfimm.py:
from __Device import Device     # Device class
#import numpy as np
import datetime as dt   # for date/time strings
import os.path      # for path manipulation
import random       # random number generators

## for Waveguide.py & Circ.py:
from numpy import inf           # infinity, for hcurv/bend_radius
#from __pyfimm import *          # all global modesolver params.

## for Tapers.py:
#from __pyfimm import *       # import the main module (should already be imported), includes many 'rect' classes/funcs
#from __Mode import *            # import Mode class
#from __Waveguide import *       # import Waveguide class
#from __Circ import *            # import Circ class
#from __pyfimm import DEBUG()        # Value is set in __pyfimm.py
#from numpy import inf              # infinity, for hcurv/bend_radius
#import numpy as np              # math
'''

#print "**** __globals.py: Finsihed importing pyFIMM modules"

global pf_DEBUG
pf_DEBUG = False   # set to true for verbose outputs onto Python console - applies to all submodules/files
# can be changed at run-time via `set/unset_DEBUG()`

# custom colormaps:
from colormap_HotCold import cm_hotcold


# Create FimmWave connection object.
import PhotonDesignLib.pdPythonLib as pd
global fimm
fimm = pd.pdApp()





#  These override the value set above in `pf_DEBUG`
def set_DEBUG():
    '''Enable verbose output for debugging.'''
    global pf_DEBUG
    pf_DEBUG = True

def unset_DEBUG():
    '''Disable verbose debugging output.'''
    global pf_DEBUG
    pf_DEBUG = False

def DEBUG():
    '''Returns whether DEBUG is true or false'''
    return pf_DEBUG

def AMF_FolderStr():
    '''Folder name to store temporary files in.'''
    return 'pyFIMM_temp'
