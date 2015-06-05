'''
pyFIMM/proprietary/ExampleModule.py

This is an example of how to add your own proprietary functionality to pyFIMM.
You could also keep this file outside the main pyFIMM directory and import it in your script, 
but importing it as part of pyFIMM gives it access to all the pyFIMM methods etc.


This example module adds the following functions:
    Adds a `set_temperature()` method to the `Waveguide` object
and
    Creates a new function `get_total_width()` as part of this module.

The functions can then be called as so:
    >>> pf.ExampleModule.get_total_width(  WaveguideObj1, WaveguideObj2, WaveguideObj3 )
and
    >>> WaveguideObj1.set_temperature( 451.0 )   # set the waveguide's temperature
'''

from ..__globals import *         # import global vars & FimmWave connection object & DEBUG() variable
import numpy as np


'''
########################################################
        New Functions from this ExampleModule
########################################################
'''
def get_total_width(  *args  ):
    '''Return the total width of the waveguides passed.
    
    Parameters
    ----------
    *args : any number of Waveguide or Circ objects, each as an individual arguments
    
    Examples
    --------
    >>> pf.ExampleModule.get_total_width(  WaveguideObj1, WaveguideObj2, WaveguideObj2  )
    :   44.2        # returns the total width in microns
    '''
    width = 0
    for wg in args:
        width += wg.get_width()
    return width




'''
########################################################
        New Functions for the Waveguide object
########################################################
'''

from ..__Waveguide import *          # import the Waveguide class, to add functions to it.

# `self` here will be the Waveguide object, once this func is called as a method of that object
def __WG_set_temperature(self,temp):
    '''Set temperature of this Waveguide.  FimmWave default is -1000.0.
    Waveguide Object should have already been built.
    
    Parameters
    ----------
    temp : float
        Temperature in degrees Celcius.
        
    Examples
    --------
    >>> WaveguideObj.set_temperature( 25.0 )    
    '''
    
    if not self.built: raise UserWarning( "Waveguide.set_temperature(): This waveguide has not been built yet!  Please call WaveguideObj.buildNode() first!" )
    
    wgString = self.nodestring + ".temp = " + str(temp)
    # nodestring is the fimmwave string to reference this Waveguide node.
    fimm.Exec(wgString)

# add the above function to the Waveguide class:
Waveguide.set_temperature   =   __WG_set_temperature  


def __WG_get_temperature(self):
    '''Return temperature setting of this Waveguide.
    
    Returns
    -------
    temp : float
        Temperature in degrees Celcius.  Defaults to `-1000.0` if unset.'''
    return fimm.Exec(  self.nodestring + ".temp"  )

# add the above function to the Waveguide class:
Waveguide.get_temperature   =   __WG_get_temperature
    
    
    

