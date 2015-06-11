'''
##########################################################################

 Simple FimmProp Device example.
 
 Creates a rectangular WG (RWG) with AlGaAs core using the default material database, `refbase.mat`
 Solves for modes & plots the fundamental mode.
 Then makes an identical waveguide that is wider, and creates a Device with the two different waveguide stuck together.

##########################################################################
'''

''' Get help on commands and objects by typing things into the console, like:
>>> help(pyfimm)   or after the import below,    >>> help(pf)
>>> help(pyfimm.set_mode_solver)
>>> help(pyfimm.Waveguide)
>>> help( pyfimm.Mode )         # the Mode class, for selecting a mode to work with
>>> help(pyfimm.Waveguide.buildNode)

or even easier, while building your script try:
>>> help(core)      # will show help on the Material object
>>> help(strip)            # will show help on the Waveguide object
>>> help(strip.buildNode)  # shows options for Circ.buildNode()
>>> dir( strip.mode(0) )     # shows all the available functions that can be performed on modes, which are actually Mode objects.
>>> help( strip.mode(0).plot ) # help on the mode plotting function

For more verbose output, while programming the libraries for example, set the pyfimm DEBUG flag as so:
>>> pyFIMM.set_DEBUG()
This will enable various levels of extra output, that aids in finding out where a calculation or bug is occurring.
'''


import pyfimm as pf   # Every script must begin with this line
#pf.set_DEBUG()      # Enable Debugging output

pf.connect()        # this connects to the FimmWave application.  The FimmWave program should already be open (pdPythonLib.StartApplication() is not supported yet)

# Set Parameters (Your copy of FIMMWAVE has default values for these. You can change more than shown here. See __jaredwave.py
import sys
ScriptPath = sys.path[0]                    # Get directory of this script
pf.set_working_directory(ScriptPath)       # Set FimmWave directory to the location of your script (needed to capture output files)
pf.set_eval_type('n_eff')                  # FIMMWAVE will label modes by the effective index (options: n_eff or beta)
pf.set_mode_finder_type('stable')          # options: stable or fast
pf.set_mode_solver('vectorial FMM real')   # Three words, any permuation of: 'vectorial/semivecTE/semivecTM FDM/FMM real/complex' for RWG.  
pf.set_wavelength(1.55)                    # The unit of space is always 1 micrometer 
pf.set_N_1d(100)                           # # of 1D modes found in each slice (FMM solver only)
pf.set_NX(100)                             # # of horiz. grid points for plotting & FDM
pf.set_NY(100)                             # # of vertical grid points for plotting & FDM
pf.set_N(3)                                # # of modes to solve for

pf.set_material_database('Materials/refbase.mat')   # Use the material database provided by PhotonDesign.  Only one matDB can be used at a time - to use multiple, set up your matDB to `include` other files.

# Project Node - You must build a project node at the beginning of every script
wg_prj = pf.Project()              # Construct a Project object, pass a project name to the constructor (optional).
wg_prj.buildNode('Example 2 - Waveguide Device', overwrite=True)              
# the buildNode() method makes FIMMWAVE build the objects.
# Here we've also set it to overwrite any existing project of the same name.


# Start constructing the Waveguide Node
t_clad = 6.0    # cladding thickness
t_core = 0.1    # core thickness

clad = pf.Material(1.4456)                 # Construct a Material python object, pass a refractive index as the argument

core=pf.Material('AlGaAs', 0.98)    # AlGaAs with 98% Aluminum: defined in material database
# See `help(core)` or `help(pf.Material)`  to see more info on Material objects & options to make them!

center = pf.Slice( clad(t_clad) + core(t_core, cfseg=True) + clad(t_clad) )
# The Core material here is also set as the Confinement Factor Segment.

side = pf.Slice( clad(2*t_clad+t_core) ) 

w_side = 6.0    # cladding width
w_core = 2.8    # width

strip = pf.Waveguide(  side(w_side) + center(w_core) + side(w_side)  )                                                                 
# You can pass the Slice width to the Slice object with ()s

#strip.set_material_database('Materials/refbase.mat')      # can set waveguide-specific material database - not recommended, as Device does not support this.

print "Printing `strip`:"
print strip          # you can print your python objects to check them

#strip.set_parent(wg_prj)        # You have to tell python which project node to build the waveguide node under
#strip.name = 'strip'           # Name the node
#strip.buildNode()
strip.buildNode(name='strip', parent=wg_prj)    # You can also set the parent & name while building.  
#You must always build the node!  This sends the actual Fimmwave commands to generate this waveguide in Fimmwave.

print "Calculating 'strip'..."
strip.calc()            # Tell FIMMWAVE to solve for the modes!



# More sophisticated mode plotting: plot the Ex's of two selected modes & return the handles so that we can manipulate the plots with matplotlib:
fig, axes, images = strip.mode( [0,2] ).plot('Ex', return_handles=True)    

# add the propagation constant of each mode to the plots:
#   position text in axis-scale, not data-scale (`transform=...`)
PlotString = r"kz = %0.3f um^-1" % (    strip.mode(0).get_kz().real    )     # insert the propagation const. into the %0.3f
axes[0].text( 0.05, 0.05,   \
    PlotString,  \
    transform=axes[0].transAxes, horizontalalignment='left', color='green', fontsize=14, fontweight='bold')    

# Do some TeX formatting (sub/superscripts) with a 'raw' (r"...") string.
PlotString = r"$k_z = %0.3f \mu{}m^{-1}$" % (    strip.mode(2).get_kz().real    )
axes[1].text( 0.05, 0.05,   \
    PlotString,  \
    transform=axes[1].transAxes, horizontalalignment='left', color='green', fontsize=14, fontweight='bold')   

# Save the modified figure as so:
fig.savefig('Example 2 - Two Modes with Prop Const.png')





# Create a second waveguide that is identical but with 6.5um wider core:

strip2 = pf.Waveguide( side(w_side) + center(w_core+6.5) + side(w_side) )

#strip2.name='strip 2'
#strip2.set_parent(wg_prj)
strip2.buildNode(name='strip2', parent=wg_prj)      # Two waveguides under the one project.



# Create a FimmProp Device with these two Waveguides concatenated (to propagate through multiple waveguides).  Pass the lengths of each WG as arguments.
dev = pf.Device(  strip(10.0) + strip2(15.0)  )

#dev.set_parent(wg_prj)
#dev.name = 'WG Device'
#dev.buildNode()
dev.buildNode(name='WG Device', parent=wg_prj)  # same as the above three lines

# You should now see the Device called "WG Device" in FimmProp!
#   See `help(dev)` or `dir(dev)` to see what further funcionality is available via pyfimm.



# View fields in the device
dev.set_input( [1,0,0] )  # Set to launch Mode #0 only
dev.plot('I')   # plot the intensity versus Z.
dev.plot('Ex', direction='-z', title='Reflected (-z) field')  # Plot reflected wave only


#wg_prj.savetofile('rectdev with mat db')   # save the project to a file.  '.prj' will be appended.
#wg_prj.delete()        # Delete the whole project!

#pyfimm.disconnect()      # close TCP connection to application.