'''
##########################################################################

 Example 4:
     Import a Project from File, and insert a Device from File into a new Project

##########################################################################
'''


import pyfimm as pf   # Every script must begin with this line

pf.connect() 

import sys, os
ScriptPath, ScriptFile = os.path.split( os.path.realpath(__file__)  )                    # Get directory of this script

''' Since we're loading an existing Project, we might not need any of these global parameters.  Haven't tested that yet. '''
pf.set_working_directory(ScriptPath)       # Set FimmWave directory to the location of your script (needed to capture output files)
pf.set_eval_type('n_eff')                  # FIMMWAVE will label modes by the effective index (options: n_eff or beta)
pf.set_mode_finder_type('stable')          # options: stable or fast
pf.set_mode_solver('vectorial FMM real')   # Three words, any permuation of: 'vectorial/semivecTE/semivecTM FDM/FMM real/complex' for RWG.  
pf.set_wavelength(1.55)                    # The unit of space is always 1 micrometer 
pf.set_N_1d(100)                           # # of 1D modes found in each slice (FMM solver only)
pf.set_NX(100)                             # # of horiz. grid points for plotting & FDM
pf.set_NY(100)                             # # of vertical grid points for plotting & FDM
pf.set_N(3)                                # # of modes to solve for

pf.set_material_database('Materials/refbase.mat')  



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
# If the project is already loaded, try `overwrite='reuse'` to prevent reloading it.  `overwrite=True` will delete the opened project before loading the file.
''' 
`openedprj` now refers to the opened Project file, which contains the Device we want to add to our own Project  
You can optionally provide a name to use in FimMWave, along with the usual `overwrite` and `warn` options.  
'''


# Copy the Device 'SlabDev' into our own project, myprj:
dev2 = myprj.import_device(project=openedprj, fimmpath='SlabDev')
''' 
We just imported a Device into our own Project, myprj.  We told it to import it from the opened Project, `openedprj`, and grab the FimMWave node named `SlabDev`.  
`dev2` now refers to this new Device, in our own Project.  In FimmWave, you will see that the Device has been copied into our own Project, 'Example 4 - Import Device'.
Since the Device was made in FimmWave, not pyFIMM, the object `dev2` does not have knowledge about the device's internal workings (for example, paths and complex layouts).  Most Device methods (such as calculating, plotting, getting Smat's) should still work though.
'''

# Do something with the new Device:
print dev2.name + ": Total Device Length = %f um" %( dev2.get_length() )


