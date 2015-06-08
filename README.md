# pyFIMM
A Python Interface to [PhotonDesign's FimmWave/FimmProp software](http://www.photond.com/products/fimmwave.htm).
Interface based on [Peter Beinstman's CAMFR simulation software](http://camfr.sourceforge.net).
Originally created by Jared Bauters at the [University of California Santa Barbara](ucsb.edu) in 2011; 
Updated by Demis D. John, 2015.


## Description
pyFIMM provides a CAMFR-like scripting interface to [Photon Design's FIMMWAVE/FIMMPROP electromagnetic/photonic simulation tools](http://www.photond.com/products/fimmwave.htm), in Python, to construct, simulate, plot and analyze photonic devices in FimmWave.  This enables one to do additional analysis and math on the simulations in python itself, and defined complex Python functions or loops that use FimmWave to do the heavy-lifting of solving for modes and Scattering Matrices.
In addition, some additional analysis functions are included, based on examples provided by Photon Design.

The interface is set up like [Peter Beinstman's CAMFR (CAvity Modelling FRamework)](http://camfr.sourceforge.net) system, in which 1-D Slices are concatenated to produce arbitrary 2-D index profiles, which can be further concatenated to produce full 3-D photonic integrated circuits.
Photon Design's Python library, `pdPythonLib`, is included in the module.


## Examples
Example of rectangular waveguide construction syntax: We will create a rectangular waveguide of SiO2 cladding and SiN core, calculate the fundamental mode & plot it. 

The following assumes you imported the module via `import pyfimm`, with your script residing in the same directory as the pyfimm folder.  `pyfimm` could be replaced with whatever name you imported the pyFIMM module under - for example, if you imported it like so:

    >>> import pyfimm as pf
    
then replace `pyfimm` with `pf` in the following examples.

First, create some Materials with some refractive index:

    >>> SiO = pyfimm.Material( 1.45 )    # refractive index of SiO2
    >>> SiN = pyfimm.Material( 2.01 )    # refractive index of Si3N4

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
    |      15.75um      |   2.50 um thick  |     15.75um    |
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



## Installation
To use pyFIMM, simply download one of the released versions (see the "releases" or "tags" section of this page) and extract the archive into a directory.  Your Python script should reside in the same directory as the *pyfimm* folder, or else you should the parent directory of the *pyfimm* folder to your Python path at the beginning of your script.    

Since FimmWave & FimmProp require Windows, you must run this on a Windows system with FimmWave installed (or via a Parallels virtual-machine).  Make sure your FimmWave executable starts up with the ability to interact with external scripts like Python (see FimmWave manual section 11.9, for setting up the scripting connection by starting Fimmwave with the '-pt 5101' command-line option, to listen on port 5101). 

These pyfimm scripts can be run like any typical Python script (eg. on the command line via `python myScript.py` or `python -i myScript.py` to interact afterwards).  The preferred method is through a Python IDE like Spyder (a matlab-like IDE).  The simplest installation of Spyder (along with all typical scientific python modules) can be accomplished via [Python(x,y)](https://code.google.com/p/pythonxy/) (Win) or [Anaconda](http://continuum.io/downloads) (Mac,Win,Linux). 

### Requires
* FimmWave by Photon Design, setup with TCP port number access (see FimmWave manual section on Python usage).
* Python 2.7 (may work on other versions, untested)
* numpy
* matplotlib
(both of the above are included as part of scientific python environments [Python(x,y)](https://code.google.com/p/pythonxy/) and [Anaconda](http://continuum.io/downloads))

