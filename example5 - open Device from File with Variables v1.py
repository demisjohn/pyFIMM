'''
##########################################################################

 Example 5:
     Import a Project + Device from File & access the internal variables

##########################################################################
'''

import pyfimm as pf   # Every script must begin with this line

pf.connect()
import sys, os
ScriptPath, ScriptFile = os.path.split( os.path.realpath(__file__)  )                    # Get directory of this script

pf.set_working_directory(ScriptPath)       # Set FimmWave directory to the location of your script (needed to capture output files)
''' Since we're loading an existing Project, we might not need any of these global parameters.  Haven't tested that yet. '''
pf.set_eval_type('n_eff')                  # FIMMWAVE will label modes by the effective index (options: n_eff or beta)
pf.set_mode_finder_type('stable')          # options: stable or fast
pf.set_mode_solver('vectorial FMM real')   # Three words, any permuation of: 'vectorial/semivecTE/semivecTM FDM/FMM real/complex' for RWG.  
pf.set_wavelength(1.55)                    # The unit of space is always 1 micrometer 
pf.set_N_1d(100)                           # # of 1D modes found in each slice (FMM solver only)
pf.set_NX(100)                             # # of horiz. grid points for plotting & FDM
pf.set_NY(100)                             # # of vertical grid points for plotting & FDM
pf.set_N(3)                                # # of modes to solve for

pf.set_material_database('Materials/refbase.mat')



#####################################################
# Import a Device from a saved FimmWave project file
#
# First open the Project file
# Then make a new pyFIMM Device that points to the loaded Device
#####################################################

#pf.set_DEBUG()  # Turn on Debugging verbose output.

ex5prj = pf.import_Project('example5 - Device with Variables v1.prj', overwrite=True)      
# If the project is already loaded, try `overwrite='reuse'` to prevent reloading it.

# Tell pyFIMM the name of the Variable Node in this Project:
ex5prj.set_variables_node('Variables 1')   

# The variables can be interrogated, get and set, via the Project's new attribute: `ex5prj.variablesnode`
# For example:
#print ex5prj.variablesnode.get_var('wCore')
#allvars = ex5prj.variablesnode.get_all()    # save all vars as dictionary
print ex5prj.variablesnode      # show all variables and formulae
# See `help(ex5prj.variablesnode)` for the full list of methods. 

# Load the Device '1x2 Coupler' into a pyFIMM Device object:
dev = pf.import_device(project=ex5prj, fimmpath='1x2 Coupler')
''' 
We just opened a Device from a file, and made a pyFIMM Device object
that points to it.  Since the Device was made in FimmProp, not pyFIMM,
pyFIMM does not try to understand it's inner workings in detail.
Many Device properties are still created though, so that you can 
plot fields, reference elements etc.
'''

# Do something with the new Device:
print dev.name + ": Total Device Length = %f um" %( dev.get_length() )


