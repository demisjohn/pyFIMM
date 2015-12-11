'''
##########################################################################

 Example 4:
     Import a Project from File, and insert a Device from File into a new Project

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
import sys, os
ScriptPath, ScriptFile = os.path.split( os.path.realpath(__file__)  )                    # Get directory of this script

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



# 1st Make our own project, as usual:
myprj = pf.Project() 
myprj.buildNode('Example 4 - Import Device', overwrite=True)              



#####################################################
# Import a Device from a saved FimmWave project file
#
# First open the Project file
# Then copy the Device into our own project
#####################################################

#pf.set_DEBUG()  # Turn on Debugging verbose output.

# Open a saved Project file:
openedprj = pf.import_Project('T:\Python Work\pyFIMM Simulations\example4 - WG Device 1.prj')
''' 
`openedprj` now refers to the opened Project file, which contains the Device we want to add to our own Project  
You can optionally provide a name to use in FimMWave, along with the usual `overwrite` and `warn` options.  
'''


# Copy teh Device 'SlabDev' into our own project, wg_prj:
dev2 = myprj.import_device(project=openedprj, fimmpath='SlabDev')
''' 
We just imported a Device into our own Project, wg_prj.  We told it to import it from the opened Project, `prj_2`, and grab the FimMWave node named `SlabDev`.  
`dev2` now refers to this new Device, in our own Project.  In FimmWave, you will see that the Device has been copied into our own Project, 'Example 4 - Import Device'.
'''

# Do something with the new Device:
print dev2.name + ": Total Device Length = %f um" %( dev2.get_length() )


