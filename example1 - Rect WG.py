'''
##########################################################################

Simple rectangular waveguide example using the FMM solver

Note that other python sessions using FimmWave connections should be terminated
before a new connection can be created, or the python terminal won't be able to
connect to FimmWave.

In Spyder, make sure you select "Interact with the Python console after execution"
to allow for dynamic commands and interacting with the objects you created.  
If Spyder doesn't return an interactive console after running the script, then 
check this setting in Run > Configure...  
 
##########################################################################
 '''

import pyfimm as pf # Every script must begin with this line
''' Get help on commands and objects by typing things like:
    (after you've created some objects, or run your script with 'interact with shell afterwards' enabled and then try these.)
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


pf.connect()    # connect to the FimmWave application, which must already running.


# Set global Parameters (Your copy of FIMMWAVE has default values for these. You can change more than shown here. See `dir(pyfimm)`, `help(pyfimm)`, or open the file `pyFIMM/__pyfimm.py`
import sys
pf.set_working_directory(sys.path[0])     # Set this directory to the location of your script, which is given by sys.path[0]
pf.set_eval_type('n_eff')    # FIMMWAVE will label modes by the effective index (options: n_eff or beta)
pf.set_mode_finder_type('stable')   # options: stable or fast
pf.set_mode_solver('vectorial FMM real')    # Three words, any permuation of: 'vectorial/semivecTE/semivecTM FDM/FMM real/complex'
pf.set_wavelength(1.55)      # The unit of space is always 1 um 
pf.set_N_1d(100)    # No. of 1D modes found in each slice (FMM solver only)
pf.set_NX(100)  # No. of horizontal grid points
pf.set_NY(100)  # No. of vertical grid points
pf.set_N(3)     # No. of modes to solve for

# Project Node: You must build a project node at the beginning of every script
wg_prj = pf.Project('Example 1 - WG Proj')   # Make a Project object, pass a project name to the constructor
wg_prj.buildNode()      # the buildNode() method is what makes FIMMWAVE build your python objects. If you don't call it, your script won't do anything!


# Construct the Waveguide Node
# WG Geometry:
t_clad = 6.0    # cladding thickness
t_core = 0.1

w_core = 2.8
w_side = 6.0    # cladding width



clad = pf.Material(1.4456)      # Construct a Material python object, pass a refractive index to the constructor
core = pf.Material(1.9835)

center = pf.Slice( clad(t_clad) + core(t_core, cfseg=True) + clad(t_clad) )      
side = pf.Slice(   clad(2*t_clad + t_core)   )
# Passing a thickness to a Material object as the argument creates  a Layer object.  
# Layer objects can be stacked (bottom to top) using the + operator - "clad" & "core" have been stacked here.
# You then pass a stack of Layer objects to the Slice object constructor
# You can also set the "cfseg" (Confinement Factor) flag for a layer if desired, as done here for the waveguide core.


strip = pf.Waveguide( side(w_side) + center(w_core) + side(w_side) ) 
# Construct a Waveguide object by adding Slice objects (left to right).
# You can pass the Slice width to the Slice object with ()'s

print "Printing `strip`:"
print strip         # you can print your python objects to the shell to check them

strip.set_parent(wg_prj)     # You have to tell python which project node to build the waveguide node under
strip.name = 'strip'    # Name the node
strip.buildNode()       # You must always build the node!

# The above three lines can also be done in one line:
#strip.buildNode(parent=wg_prj, name='strip')


strip.calc()           # Tell FIMMWAVE to solve for the modes!

strip.mode(0).plot()        # Plot the fundamental mode with python!
#strip.mode(0).plot('Ey')    # plot Ey instead
strip.mode('all').plot(title='Strip WG: All Modes')    # plot all the calc'd modes (3 in this case) on one figure 


#strip.delete()         # delete FIMMWAVE nodes if you want to!
#wg_prj.delete()


#pf.disconnect()      # close TCP connection to application. Other pyFIMM scripts won't be able to use FimmWave until you either disconnect or kill the script's shell entirely.