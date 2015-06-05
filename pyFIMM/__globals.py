'''pyFIMM's Global Variables
Contains/defines global variables - most importantly the fimmwave connection object `fimm`.

This separate file is required to prevent circular module imports, and enable nested-modules to use the FimmWave connection.
'''

import numpy as np
import matplotlib.pyplot as plt

global pf_DEBUG
pf_DEBUG = False   # set to true for verbose outputs onto Python console - applies to all submodules/files


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
