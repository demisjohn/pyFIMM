'''pyFIMM Documentation:
pyFIMM provides a python interface to Photon Design's FIMMWAVE/FIMMPROP simulation tools.

The interface is set up like Peter Beinstman's CAMFR (CAvity Modelling FRamework) system, in which 1-D Slices are concatenated to produce arbitrary 2-D index profiles (waveguides), which can be further concatenated to produce full 3-D photonic integrated circuits.
Photon Design's pdPythonLib is included in the module.

Originally created by Jared Bauters at the University of California Santa Barbara in 2011.
Updated by Demis D. John, 2015.


Examples
--------
Example of rectangular waveguide construction syntax: We will create a rectangular waveguide of SiO2 cladding and SiN core, calculate the fundamental mode & plot it. `pyfimm` should be replaced with whatever name you imported the pyFIMM module as - for example, if you imported it like so:
    >>> import pyfimm as pf
then replace `pyfimm` with `pf` in the following examples.

First, create some Materials with some refractive index:
    >>> SiO = pyfimm.Material(1.45)    # refractive index of SiO2
    >>> SiN = pyfimm.Material(2.01)    # refractive index of Si3N4

Then, create some 1-D slabs, by calling those Materials with a thickness value, and adding them together from top to bottom in a Slice:
    clad = pyfimm.Slice(  SiO(15.75)  )      # Thicknesses in microns
    core = pyfimm.Slice(  SiO(10.0) + SiN(2.5) + SiO(5.0)  )
This created an imaginary structure from bottom-to-top, for example `core` looks like:

            top         
    --------------------
            SiO
        5.0 um thick
    --------------------
            SiN
       2.50 um thick
    --------------------
            SiO
       10.0 um thick
    --------------------
           bottom

Then make a 2-D structure by calling these Slices with a width value, and adding them together from left to right in a Waveguide:
    >>> WG = pyfimm.Waveguide(  clad(3.0) + core(1.0) + clad(4.0)  )   # Widths in microns
Which creates this imaginary 2-D Waveguide structure from left-to-right:
                                top         
    ---------------------------------------------------------
    |<----- 3.0um------>|<-----1.0um------>|<---- 4.0um---->|
    |                   |        SiO       |                |
    |                   |    5.0 um thick  |                |                
    |                   |------------------|                |
    |        SiO        |        SiN       |       SiO      |
    |      15.75um      |  0.750 um thick  |     15.75um    |
    |       thick       |------------------|      thick     |
    |                   |        SiO       |                |
    |                   |   10.0 um thick  |                |
    ---------------------------------------------------------
                               bottom
    
Then tell FimmWave to actually build these structures:
    >>> WG.buildNode(name='Waveguide', parent=wg_prj)     # Build the Fimmwave Node
Now the RWG waveguide node is available in the Fimmwave GUI.  (Note you should have already made a Project node in fimmwave, which is referenced as the `parent` here.  See Examples for full code.)

You can then calculate the modes as so:
    >>> WG.calc()

And inspect the modes like so:
    >>> WG.mode(0).plot()   # plots the fundamental mode.
Or extract field values like so:
	>>> Mode1_Ex = WG.mode(1).get_field('Ex')   # Saves x-direction E-field for 2nd mode
	
See the Examples directory for full examples, as some details are missing in these.


Requires
--------
numpy, 
matplotlib
FimmWave, setup with TCP port number access (see FimmWave manual section on Python usage).



Get help on commands and objects by typing things like:
    (after you've created some objects, or run your script with 'interact with shell afterwards' enabled and then try these.)
    >>> import pyFIMM as pf     # import the module
    >>> help( pf )
    >>> dir( pf )     # lists all functions and variables provided by the module
    >>> help( pf.set_mode_solver )  # help on one function
    >>> help( pf.Waveguide )    # help on the Waveguide object
    >>> dir ( pf.Waveguide )    # list all functions/variables in the Waveguide object
    >>> help( pf.Waveguide.mode(0).plot )   # help on funciton 'plot' of the Waveguide object
    >>> help( pf.Circ.buildNode )   # help on the `buildNode` function of the Circ object
    
or even easier, while building the script try:
    >>> clad = pf.Material(1.4456)
    >>> core = pf.Material(1.9835)
    >>> help(clad)      # Will show help on the Material object
    >>> strip = pf.Waveguide( side(w_side) + center(w_core) + side(w_side) ) 
    >>> dir(strip)              # will show functions of the Waveguide object
    >>> help(strip.buildNode)   # show help on the Waveguide.buildNode() method

after strip.calc(), try
    >>> dir(  strip.mode(0)  )    # list the functions of a Mode object
    >>> help( strip.mode(0).plot )  # detailed help on the mode plotting function


'''

import __version as version    # file with the version number.
__version__ = version.__version__
__versiondate__ = version.__versiondate__

# Splash screen.
print
print "pyFIMM", version.pyfimm_version, ""
print "Python Interface to Photon Design's FIMMWave software package."
print "Based on Peter Beinstman's CAMFR (CAvity Modelling FRamework) interface."
print
print "Created by Jared Bauters University of California, Santa Barbara & updated by Demis D. John."
print


from __globals import *         # import global vars & FimmWave connection object
from __pyfimm import *          # import the main module, many global functions, base objects like Project, Material, Slice, Section and some rectangular waveguide functions.
from __Waveguide import *       # contains the Waveguide class, including most of the Fimmwave commands for WG creation.
from __Circ import *            # contains Circ class & all other functions for cylindrical geometries.
from __Device import *          # contains the Device class, for constructing 3-D devices 
from __Mode import *            # contains the Mode class, for WGobj.mode(0).xyz operations
from __Tapers import *          # contains all Taper classes, including WG_Lens
from __Cavity import *          # Cavity object & calculations
from __CavityMode import *      # contains the CavityMode class, for CavityOb.mode(0).xyz operations


####################################################################################
# Import Proprietary Modules
####################################################################################

from proprietary import *      # the 'proprietary' folder contains modules/functions from other institutions.
