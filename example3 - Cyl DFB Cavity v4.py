'''
##########################################################################

 Cylindrical waveguide & Device example - a distributed feed-back device
     similar to a VCSEL cavity.  

    Based on the Photon Design web-example: 
        "Modelling a passive optical cavity (VCSEL, DFB)"
        http://www.photond.com/products/fimmprop/fimmprop_applications_17.htm
    
    Calculates the Cavity modes of a cylindrical GaAs/AlGaAs DFB using the
    "Cavity Mode Calculator" code written by Vincent Brulis @ Photon Design, 2014

    Requires pyFIMM v1.2.8 or greater
    
##########################################################################
'''

import numpy as np    # Array math.functions.  Used here for `argmax()`.

import pyfimm as pf   # Every script must begin with this line
''' Get help on commands and objects by typing things into the console, like:
>>> help(pyfimm)   or after the above import,    >>> help(pf)
>>> help(pyfimm.set_mode_solver)
>>> help(pyfimm.Waveguide)
>>> help( pyfimm.Mode )         # the Mode class, for selecting a mode to work with
>>> help(pyfimm.Circ.buildNode)

or even easier, while building your script try:
>>> AlOx = pyfimm.Material(1.60)        # setting up some Materials
>>> AlGaAs = pyfimm.Material(3.25)
>>> help(AlOx)      # will show help on the Material object
>>> CurrentAperture = pyfimm.Circ( AlGaAs(3.5) + AlOx(4.5) )
>>> help(CurrentAperture)            # will show help on the Circ object
>>> help(CurrentAperture.buildNode)  # shows options for Circ.buildNode()
>>> help( CurrentAperture.mode(0) )     # shows functions that can be performed on modes, which are actually Mode objects.
>>> help( CurrentAperture.mode(0).plot ) # help on the mode plotting function

For more verbose output, while programming the libraries for example, set the pyfimm DEBUG parameter like so:
    pyfimm.set_DEBUG()
at the point you want debugging output turned on.  This will enable various levels of extra output, that aids in finding out where a calculation or bug is occurring.  `unset_DEBUG()` can be used to turn off this extra verbosity.
'''


pf.connect()        # this connects to the FimmWave application.  The FimmWave program should already be open (pdPythonLib.StartApplication() is not supported yet)


wl = 1.100  # center wavelength in microns - sets the Bragg wavelength

# Set Parameters (Your copy of FIMMWAVE has default values for these. You can change more than shown here. See __jaredwave.py
import sys
ScriptPath = sys.path[0]                    # Get directory of this script
pf.set_working_directory(ScriptPath)       # Set FimmWave directory to the location of your script (needed to capture output files)
pf.set_eval_type('n_eff')                  # FIMMWAVE will label modes by the effective index (options: n_eff or beta)
pf.set_mode_finder_type('stable')          # options: stable or fast
pf.set_mode_solver('Vectorial GFS Real')   # See `help(pyfimm.set_mode_solver)` for all options.
pf.set_wavelength( wl )                    # The unit of space is always 1 micrometer 
pf.set_N_1d(100)                           # Num. of 1D modes found in each slice (FMM solver only)

pf.set_N(3)                                # Num. of modes to solve for
pf.set_Nm(1)        # theta mode order.  Can accept start/stop values as list, eg. [1,5]
pf.set_Np(2)        # polarization mode order, also can accept start/stop values as list.

dfbproj = pf.Project('Example 3 - DFB Cavity', buildNode=True, overwrite=True)    # Create Proj & build the node in one line.  `overwrite` will overwrite an existing project with the same name.         




# Define materials.
## Refractive indices:
n_GaAs = 3.53
n_AlGaAs = 3.08
CoreHi = pf.Material(n_GaAs)  # GaAs
CoreLo = pf.Material(n_AlGaAs)  # AlGaAs
Clad = pf.Material(1.56)

rCore = 20/2.
TotalDiam = 30
rClad = TotalDiam/2-rCore

pf.set_circ_pml(0)       # thickness of perfectly matched layers for cylindrical (circ) objects

# Fiber waveguides:
Hi = pf.Circ( CoreHi(rCore) + Clad(rClad) )
Lo = pf.Circ( CoreLo(rCore) + Clad(rClad) )

#Hi.set_joint_type("special complete")   # default is "complete"
#Lo.set_joint_type("special complete")

# Build these waveguides in FimmWave.  The Device will reference the pre-built waveguide nodes.
Hi.buildNode(name='Hi', parent=dfbproj)
Lo.buildNode(name='Lo', parent=dfbproj)


# Lengths
dHi = wl/4/n_GaAs   #77.90368e-3
dLo = wl/4/n_AlGaAs #89.28571e-3

# Construct the device, split into two parts with same waveguide type at central split.  This is important so that the modal basis set of each half of the cavity is the same.
Nperiods = 50
# Devices are built from left to right:
dfb_left = pf.Device(   Lo(1.0) + Nperiods*( Hi(dHi) + Lo(dLo) ) + Hi(dHi/2)   )     
# With Hi waveguide cut in half at center & quarter-wave shift (Lo section with double length):
dfb_right = pf.Device(   Hi(dHi/2) + Lo(dLo*2) + Hi(dHi) + Nperiods*( Lo(dLo) + Hi(dHi)) + Lo(1.0)   )

dfb_left.set_joint_type('special complete')
dfb_right.set_joint_type('special complete')

# Build these Devices in FimmProp:
dfb_left.buildNode(name='DFBleft', parent=dfbproj)
dfb_right.buildNode(name='DFBright', parent=dfbproj)

# Show the devices in the FImmWave GUI:
pf.Exec(dfb_right.nodestring + '.findorcreateview()')
pf.Exec(dfb_left.nodestring + '.findorcreateview()')

dfb_right.calc()


dfb_right.plot_refractive_index()   # Fig1: show the refractive index versus Z for this device.


dfb_left.set_input([1,0,0], side='right', normalize=True)   # launch only 1st Mode from right side
dfb_left.plot('Ex', direction='left')     # Fig2: Plot Ex field for this launch, for left-propagating field (since injected on right side)
#dfb_left.plot('Ey', refractive_index=True)  # can also plot refractive index on same figure




# ---  Now Calculate the Cavity modes!  ---
#WLs = [1.080, 1.100, 1.120]              # for fast example
#WLs = np.arange( 1.100-0.060, 1.100+0.060, 0.005 )     # coarse eigenmode calculation
#WLs = np.concatenate([    np.arange(1.100-0.060, 1.100-0.007, 0.005) , np.arange(1.100-0.007, 1.100+0.007, 0.0005) , np.arange(1.100+0.007, 1.100+0.060, 0.005)    ])    # coarse away from resonance, fine at resonance
WLs = np.arange( wl-0.010, wl+0.010, 0.005 )      # refined calc @ resonance only


# Set up Cavity with Left & Right devices:
DFB = pf.Cavity(dfb_left, dfb_right)    

DFB.plot_refractive_index()     # Fig3: show the refractive index profile along Z, at (x,y)=(0,0)

DFB.calc(WLs)       # Calculate the Cavity resonances etc.
# try `help DFB` or dir(DFB) After calling calc() - you'll see that new variables are available, such as the eigenvectors & resonance wavelengths etc.  '''

#DFB.mode(0).plot()         # plot eigenvalues of 1st mode (plot defaults to 'EigV')
DFB.mode('all').plot('EigVals')      # Fig4: plot eigenvalues of all modes


# plot resonance fields for 2 of the modes:
DFB.mode( [0,1] ).plot('Ex', 'resonance', refractive_index=True, title="DFB + 1/2-wave")     # Fig5: plot Ex field for the resonance wavelengths of specified modes.


# To view the resonance mode profile:
#    In FimmProp, on Either device, select 
#        View > Input Field
#    And then select the appropriate tab (Left-Hand or Right-Hand input), and
#    click 'Update' in the Preview area, to see what the superposition of modes
#    according to the EigenVector looks like.


#pyfimm.disconnect()      # close TCP connection to application.