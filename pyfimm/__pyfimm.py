'''
pyFIMM - main module

See help on the main module, `help(pyFIMM)`, for usage info.

In this file are the pyFIMM global parameters - set_wavelength, set_N etc.
See __Classes.py for the higher-level classes, such as Project, Node, Material, Layer, Slice and Section.
Waveguide, Circ and Device classes/functions are in their respective separate files.

'''

'''See file __Waveguide.py for the Waveguide class & rectangular WG funcs.
-- Demis 2014-12-31'''


'''See file __Mode.py for the Mode class.
-- Demis 2014-12-31 '''


'''See file __Device.py for the Device class.
-- Demis 2014-12-31 '''


'''See file __Circ.py for Circ class & other cylindrical waveguide functions, such as Cylindrical global params (Np, Nm etc.).
-- Demis 2015-01-03'''

''' See file __Tapers.py for Taper class & WG Lens class & related functions.
-- Demis 2015-01-26'''


#import PhotonDesignLib.pdPythonLib as pd       # moved into __globals.py to eliminate circular import
#fimm = pd.pdApp()

#fimm.ConnectToApp()    # moved into connect()



from __globals import *         # import global vars & FimmWave connection object `fimm`
from __Classes import *         # import higher-level classes

#import numpy as np
#import datetime as dt   # for date/time strings
import os.path      # for path manipulation





####################################################################################
# Fimmwave General Functions
####################################################################################
def connect(hostname='localhost', port=5101):
    '''Open connection to the Fimmwave application.
    
    Parameters
    ----------
    hostname : string, optional; address/hostname to computer (default= 'localhost')
    port : int, optional; port on host computer (default= 5101)
    
    calls pdPythonLib.ConnectToApp(hostname = 'localhost',portNo = 5101)
    '''
    #in pdPythonLib: ConnectToApp(self,hostname = 'localhost',portNo = 5101)
    
    fimm.ConnectToApp(hostname=hostname, portNo=port)
    '''Check the connection:    '''
    try:
        NumSubnodes = int(  fimm.Exec("app.numsubnodes()")  )
        print "Connected! (%i Project nodes found)"%NumSubnodes
    except:
        ErrStr = "Unable to connect to Fimmwave app - make sure it is running & license is active."
        raise IOError(ErrStr)

    
def disconnect():
    '''Terminate the connection to the FimmWave Application & delete the object.'''
    global pd # use this module-level variable.  Dunno why the `global` declaration is only needed in THIS module function (not others!), in order to delete it...
    del pd    # pdPythonLib does some cleanup upon del()'ing

def exitfimmwave():
    '''Closes the Fimmwave app'''
    fimm.Exec("app.exit")

def Exec(string, vars=[]):
    '''Send a raw command to the fimmwave application.  
    `vars` is an optional list of arguments for the command.
    See `help(<pyfimm>.PhotonDesignLib.pdPythonLib.Exec)` for more info.'''
    out = fimm.Exec(string, vars)
    if isinstance(out, list): out = strip_array(out)
    if isinstance(out, str):  out = strip_text(out)
    '''if fimm.Exec returned a string, FimmWave usually appends `\n\x00' to the end'''
        #if out[-2:] == '\n\x00': out = out[:-2]     # strip off FimmWave EOL/EOF chars.
    return out


def close_all(warn=True):
    '''Close all open Projects, discarding unsaved changes.
    
    Parameters
    ----------
    warn : { True | False }, optional
        True by default, which will prompt user for confirmation.
    '''
    nodestring="app"   # top-level, deleting whole Projects
    N_nodes = int(  fimm.Exec(nodestring+".numsubnodes()")  )
    
    wstr = "Will close" if warn else "Closing"
    
    WarnStr = "WARNING: %s all the following open Projects,\n\tdiscarding unsaved changes:\n"%(wstr)
    SNnames = []    #subnode names
    for i in range(N_nodes):
        SNnames.append(  strip_txt(  fimm.Exec(nodestring+r".subnodes["+str(i+1)+"].nodename()")  )  )   
        WarnStr = WarnStr + "\t%s\n"%(SNnames[-1])
    
    print WarnStr
    
    if warn:
        # get user confirmation:
        cont = raw_input("Are you sure? [y/N]: ").strip().lower()
    else:
        cont = 'y'
    
    if cont == 'y':
        fString = ''
        for i in range(N_nodes):
            fString += nodestring + ".subnodes[1].close()\n"
        fimm.Exec( fString )
    else:
        print "close_all(): Cancelled."
#end close_all()
    
    


####################################
#   Fimmwave Global Parameters  ####
####################################

def set_working_directory(wdir):
    '''Set FimmWave working directory. Usually set to same dir as your Python script in order to find FimmWave output files.'''
    #if DEBUG(): print "set_working_directory(): sending setwdir() command:"
    fimm.Exec("app.setwdir("+str(wdir)+")")
    #if DEBUG(): print "set_working_directory(): finished setwdir()."
    
def get_working_directory():
    '''Get fimmwave working directory, as string.'''
    print "Warning: wdir string may not be in standard format."
    return fimm.Exec("app.wdir")[:-2]   # strip off the last two EOF characters

def set_wavelength(lam0):
    '''Set the simulated optical wavelength (microns).'''
    fimm.Exec("app.defaultlambda = {"+str(lam0)+"}")

def get_wavelength():
    '''Return the simulation's optical wavelength (microns).'''
    return fimm.Exec("app.defaultlambda")

def wavelength():
    '''Backwards compatibility only. 
    Return the simulation's optical wavelength (microns).'''
    print "DeprecationWarning: Use get_wavelength() instead."
    return get_wavelength()

def set_material_database(path):
    '''Set the path to the material database (*.mat) file.  Only needed if you are defining materials using this database ('mat'/material type waveguides instead of 'rix'/refractive index).  This sets a global materials file that will be used in every waveguide and device that is built.  
    Although waveguide nodes can specify their own (different) materials files, it is recommended that a global file be used instead since FimmProp Devices do not accept multiple materials files (to avoid confusion and identically-named materials from different files).  The single global file can be set to `include` any other materials files.
    
    Parameters
    ----------
    path : string
        Absolute or relative path to the material database file.  `path` will be automatically converted to an absolute path, as a workaround to a FimmProp Device Node bug that causes it to only accept absolute paths.
        '''
    global global_matDB
    import os
    path = os.path.abspath(path)    # convert to absolute path
    if os.path.isfile(path):
        global_matDB = str(path)
    else:
        ErrStr = "Material database file does not exist at the specified path `%s`" %(path)
        raise IOError(ErrStr)
    if DEBUG(): print "matDB = ", global_matDB

def get_material_database():
    '''Get path to global material database file.
    
    Returns
    -------
    path : string
        Absolute path to the material database file that will be used when building nodes.
        '''
    global global_matDB
    try:
        global_matDB
    except:
        if DEBUG(): print "unset global_matDB --> None"
        global_matDB = None
    return global_matDB




############################################
####        Mode Solver Parameters      ####
############################################

def set_eval_type(eval_type):
    '''FIMMWAVE will label modes by the effective index (n_eff) or propagation constant (beta).
    
    Parameters
    ----------
    eval_type : { 'n_eff' | 'beta' }, case insensitive
        Equivalent strings for 'n_eff': 'neff', 'effective index'
        Equivalent strings for 'beta': 'propagation constant'
    
    Examples
    --------
        >>> set_eval_type("n_eff") 
    '''
    if eval_type.lower() == 'n_eff' or eval_type.lower() == 'neff' or eval_type.lower() == 'effective index':
        fimm.Exec("app.evaltype = 1")
    elif eval_type.lower() == 'beta' or eval_type.lower() == 'propagation constant':
        fimm.Exec("app.evaltype = 0")
    else:
        raise ValueError('invalid input for eval_type')

def get_eval_type():
    '''Return the string "n_eff" or "beta" corresponding to the FimmWave mode labelling scheme.  See also set_eval_type()'''
    eval_type = fimm.Exec("app.evaltype")
    if eval_type == 1:
        return 'n_eff'
    elif eval_type == 0:
        return 'beta'
    else:
        return ''

def eval_type():
    '''Backwards compatibility only. 
    Use get_eval_type() instead.'''
    print "eval_type(): DeprecationWarning: Use get_eval_type() instead."
    return get_eval_type()


def set_mode_finder_type(mode_finder_type):
    '''options: "stable" or "fast", passed as string.'''
    if mode_finder_type.lower() == 'stable':
        fimm.Exec("app.homer_opt = 1")
    elif mode_finder_type.lower() == 'fast':
        fimm.Exec("app.homer_opt = 0")
    else:
        print 'invalid input for mode_finder_type'

def get_mode_finder_type():
    '''returns: "stable" or "fast" as string.
    Corresponds to the fimmwave parameter: app.homer_opt
    '''
    mode_finder_type = fimm.Exec("app.homer_opt")
    if mode_finder_type == 1:
        return 'stable'
    elif mode_finder_type == 0:
        return 'fast'
    else:
        return ''

def mode_finder_type():
    '''Backwards compatibility only.  Should Instead get_***().'''
    print "Deprecation Warning:  mode_finder_type():  Use get_mode_finder_type() instead."
    return get_mode_finder_type()
    

def set_solver_speed(string):
    '''options: 'best' (default) or 'fast'   
    used to set the fimmwave param:
    >>> NodeStr.evlist.mpl.speed = <solverspeed>'''
    global global_solver_speed
    if string.lower() == 'best':
        global_solver_speed = 0
    elif string.lower() == 'fast':
        global_solver_speed = 1
    else:
        print 'invalid input for mode_finder_type'
        
def get_solver_speed():
    '''Returns 'best' or 'fast' as string.
    Defaults to 'best', if unset.    '''
    global global_solver_speed
    try:
        global_solver_speed
    except NameError:
        global_solver_speed = 0     # default value if unset
    
    if global_solver_speed==0:
        return 'best'
    elif global_solver_speed==1:
        return 'fast'
    return global_solver_speed




def set_mode_solver(solver):
    '''Set the mode solver.  Takes few words as string.  
    
    Parameters
    ----------
    solver : string, case insensitive
        
    For rectangular waveguides, use a combination of following to create the three-keyword string:
    "vectorial/semivecTE/semivecTM  FDM/FMM  real/complex"
    FDM = Finite Difference Method
    FMM = Field Mode Matching method
    Both of these solvers take all permutations of vectoriality & real/complex.
    eg. "semivecTE FMM complex"   or   "vectorial FDM real"
    
    For Cylindrical Waveguides, use any of these options:
    "vectorial/semivecTE/semivecTM  FDM/GFS/Gaussian/SMF  real/complex"
    where the FDM solver is always "vectorial", and real/complex is only applicable to the FDM solver.  GFS takes 'vectorial' or 'scalar' but not 'semivec'.  Inapplicable keywords will raise an error in FimmWave.
    FDM = Finite-Difference Method
    GFS = General Fiber Solver
    Gaussian = Gaussian Mode Fiber solver (unsupported)
    SMF = Single-Mode Fiber
    
    For Cylindrical Waveguides, here are all the possible options:
    Finite-Difference Method solver: "vectorial FDM real" , "vectorial FDM complex",
    General Fiber Solver: "vectorial GFS real" , "scalar GFS real",
    Single-Mode Fiber solver: "Vectorial SMF" , "SemivecTE SMF" , "SemivecTM SMF",
    Gaussian Fiber Solver (unsupported): "Vectorial Gaussian" , "SemivecTE Gaussian" , "SemivecTM Gaussian".
    '''
    global global_mode_solver
    parts = solver.split()
    if len(parts) > 3 or len(parts)==0: raise ValueError(  "Expected string separated by spaces, with max 3 words.\n`slvr`="+str( solver )   )
    
    #### should do a RegEx to parse the mode solver params, so order or terms is arbitrary
    #   Find the mode solver type first?
    # Only set the parts needed - eg. if only called set_modesolver('SemivecTE') should still use default modesolver, but only change to TE.
    
    global_mode_solver = solver
    
def get_mode_solver():
    '''Return mode solver as string.  
    
    Returns
    -------
    mode_solver : string
        String representation of the mode solver to use.  Returns `None` if unset, and default modesolver for each waveguide type will be used.
        See set_mode_solver() for available parameters.
        Returns <None> if unset.
    '''
    global global_mode_solver
    try:
        global_mode_solver
    except NameError:
        global_mode_solver = None
    return global_mode_solver

def mode_solver():
    '''Backwards compatibility only.  Should Instead get_***().'''
    print "Deprecation Warning:  mode_solver():  Use get_mode_solver() instead."
    return get_mode_solver()


def set_NX(mnx):
    '''Set # of horizontal grid points.
    
    Parameters
    ----------
    mnx : int
        Number of horizontal grid points in mode representation/solver (depending on solver).  Defaults to 60.
    '''
    global global_NX
    global_NX = mnx

def get_NX():
    '''Return # of horizontal grid points.  Defaults to 60.'''
    global global_NX
    try:
        global_NX
    except NameError:
        global_NX = 60
    return global_NX
    
def NX():
    '''Backwards compatibility only.  Should Instead use get_NX().'''
    print "Deprecation Warning:  NX():  Use get_NX() instead."
    return get_NX()


def set_NY(mny):
    '''Set # of vertical grid points
    
    Parameters
    ----------
    mny : int
        Number of horizontal grid points in mode representation/solver (depending on solver).  Defaults to 60.'''
    global global_NY
    global_NY = mny

def get_NY():
    '''Return # of vertical grid points. Defaults to 60.'''
    global global_NY
    try:
        global_NY
    except NameError:
        global_NY = 60
    return global_NY
    
def NY():
    '''Backwards compatibility only.  Should Instead use get_NY().'''
    print "Deprecation Warning:  NY():  Use get_NY() instead."
    return get_NY()


def set_N(mn):
    '''Set # of modes to solve for.
    For cylindrical waveguides, this sets the number of Axial Quantum Number modes to solve for.  set_Np() chooses the polarization modes.
    
    Parameters
    ----------
    mn : int >=1
        Number of modes to solve for.  Defaults to 10.'''
    global global_N
    global_N = mn

def get_N():
    '''Return # of modes to solve for.  
    Defaults to 10 if unset.'''
    global global_N
    try:
        global_N
    except NameError:
        global_N = 10
    return global_N

def N():
    '''Backwards compatibility only.  Should Instead use get_***().'''
    print "Deprecation Warning:  N():  Use get_N() instead."
    return get_N()


def set_vertical_symmetry(symmtry):
    global global_vertical_symmetry
    global_vertical_symmetry = symmtry

def get_vertical_symmetry():
    global global_vertical_symmetry
    try:
        global_vertical_symmetry
    except NameError:
        global_vertical_symmetry = None
    return global_vertical_symmetry

def vertical_symmetry():
    '''Backwards compatibility only.  Should Instead use get_***().'''
    print "Deprecation Warning:  vertical_symmetry():  Use get_vertical_symmetry() instead."
    return get_vertical_symmetry()


def set_horizontal_symmetry(symmtry):
    global global_horizontal_symmetry
    global_horizontal_symmetry = symmtry

def get_horizontal_symmetry():
    global global_horizontal_symmetry
    try:
        global_horizontal_symmetry
    except NameError:
        global_horizontal_symmetry = None
    return global_horizontal_symmetry

def horizontal_symmetry():
    '''Backwards compatibility only.  Should Instead use get_***().'''
    print "Deprecation Warning:  horizontal_symmetry():  Use get_horizontal_symmetry() instead."
    return get_horizontal_symmetry()


def set_min_TE_frac(mintefrac):
    '''Set minimum TE fraction to constrain mode solver to a particular polarization.'''
    global global_min_TE_frac
    global_min_TE_frac = mintefrac

def get_min_TE_frac():
    '''Return minimum TE fraction. Defaults to 0.'''
    global global_min_TE_frac
    try:
        global_min_TE_frac
    except NameError:
        global_min_TE_frac = 0
    return global_min_TE_frac
    
def min_TE_frac():
    '''Backwards compatibility only.  Should Instead use get_***().'''
    print "Deprecation Warning:  min_TE_frac():  Use get_min_TE_frac() instead."
    return get_min_TE_frac()


def set_max_TE_frac(maxtefrac):
    '''Set maximum TE fraction to constrain mode solver to a particular polarization.'''
    global global_max_TE_frac
    global_max_TE_frac = maxtefrac

def get_max_TE_frac():
    '''Return maximum TE fraction.'''
    global global_max_TE_frac
    try:
        global_max_TE_frac
    except NameError:
        global_max_TE_frac = 100
    return global_max_TE_frac
    
def max_TE_frac():
    '''Backwards compatibility only.  Should Instead use get_***().'''
    print "Deprecation Warning:  max_TE_frac():  Use get_max_TE_frac() instead."
    return get_max_TE_frac()


def set_min_EV(min_ev):
    global global_min_ev
    global_min_ev = min_ev

def get_min_EV():
    global global_min_ev
    try:
        global_min_ev
    except NameError:
        global_min_ev = None
    return global_min_ev
    
def min_EV():
    '''Backwards compatibility only.  Should Instead use get_***().'''
    print "Deprecation Warning:  min_EV():  Use get_min_EV() instead."
    return get_min_EV()


def set_max_EV(max_ev):
    global global_max_ev
    global_max_ev = max_ev

def get_max_EV():
    global global_max_ev
    try:
        global_max_ev
    except NameError:
        global_max_ev = None
    return global_max_ev
    
def max_EV():
    '''Backwards compatibility only.  Should Instead use get_***().'''
    print "Deprecation Warning:  max_EV():  Use get_max_EV() instead."
    return get_max_EV()


def set_RIX_tol(rixTol):
    global global_rix_tol
    global_rix_tol = rixTol

def get_RIX_tol():
    global global_rix_tol
    try:
        global_rix_tol
    except NameError:
        global_rix_tol = None
    return global_rix_tol
    
def RIX_tol():
    '''Backwards compatibility only.  Should Instead use get_***().'''
    print "Deprecation Warning:  RIX_tol():  Use get_RIX_tol() instead."
    return get_RIX_tol()


def set_N_1d(n1d):
    '''# of 1D modes found in each slice (FMM solver only)'''
    global global_n1d
    global_n1d = n1d

def get_N_1d():
    '''Return # of 1D modes found in each slice (FMM solver only)'''
    global global_n1d
    try:
        global_n1d
    except NameError:
        global_n1d = None
    return global_n1d

def N_1d():
    '''Backwards compatibility only.  Should Instead use get_***().'''
    print "Deprecation Warning:  N_1d():  Use get_N_1d() instead."
    return get_N_1d()


def set_mmatch(match):
    '''
    Parameters
    ----------
    match : float
    
    See Fimmwave Manual section 5.4.12.
    If mmatch is set to zero then it will be chosen automatically. 
    If mmatch is set to e.g. 3.5 then the interface will be set in the center of the third slice from the left.
    '''
    global global_mmatch
    global_mmatch = match

def get_mmatch():
    '''Return mmatch - see set_mmatch() for more info.'''
    global global_mmatch
    try:
        global_mmatch
    except NameError:
        global_mmatch = None
    return global_mmatch

def mmatch():
    '''Backwards compatibility only.  Should Instead use get_***().'''
    print "Deprecation Warning:  mmatch():  Use get_mmatch() instead."
    return get_mmatch()



def set_temperature(temp):
    '''
    Parameters
    ----------
    temp : float
    
    Set global temperature in degrees Celsius.  Eventually, will be able to set temperature per-Waveguide to override this.  If unset, the temperature is left to the FimmWave default.
    '''
    print "WARNING: set_temperature(): Not implemented yet!  Does not currently set the temperature in FimmWave nodes."
    global global_temperature
    global_temperature = temp

def get_temperature():
    '''Return global temperature in degrees Celsius.  Returns <None> if unset.'''
    global global_temperature
    try:
        global_temperature
    except NameError:
        global_temperature = None
    return global_temperature
#end get_temperature


def get_amf_data(modestring, filename="temp", precision=r"%10.6f", maxbytes=500):
    '''Return the various mode profile data from writing an AMF file.
    This returns data for all field components of a mode profile, the start/end x/y values in microns, number of data points along each axis and some other useful info.
    The AMF file and accompanying temporary files will be saved into the directory designated by the variable `AMF_Folder_Str()`, which is typically something like "pyFIMM_temp/".
    Temporary files are created in order to extract the commented lines.
    This function currently does NOT return the field vlaues, as they are much more efficiently acquired by the FimMWave functions get_field()
    
    Parameters
    ----------
    modestring : str
        The entire FimmWave string required to produce the amf file, omitting the ".writeamf(...)" function itself, typically a reference to the individual mode to be output.  An example would be:
            app.subnodes[7].subnodes[1].evlist.list[1].profile.data
    
    filename : str, optional
        Desired filename for the AMF-file &  output.
    
    precision : str, optional
        String passed to the FimmWave function `writeamf()` to determine output precision of field values, as a standard C-style format string.  Defaults to "%10.6f", specifying a floating point number with minimum 10 digits and 6 decimal points.
    
    maxbytes : int, optional
        How many bytes to read from the AMF file.  This prevents reading all the field data, and speeds up execution/memory usage.  Defaults to 500 bytes, which typically captures the whole AMF file header info.
    
    
    Returns
    -------
    A dictionary is returned containing each value found in the AMF file header.
    {'beta': (5.980669+0j),     # Beta (propagation constant), as complex value
     'hasEX': True,             # does the AMF file contain field values for these components?
     'hasEY': True,
     'hasEZ': True,
     'hasHX': True,
     'hasHY': True,
     'hasHZ': True,
     'isWGmode': True,          # is this a waveguide mode?
     'iscomplex': False,        # are the field values (and Beta) complex?
     'lambda': 1.55,            # wavelength
     'nx': 100,                 # Number of datapoints in the x/y directions
     'ny': 100,
     'xmax': 14.8,              # x/y profile extents, in microns
     'xmin': 0.0,
     'ymax': 12.1,
     'ymin': 0.0}
    
    Examples
    --------
    >>> ns = "app.subnodes[7].subnodes[1].evlist.list[1].profile.data"
    >>> fs = "pyFIMM_temp\mode1_pyFIMM.amf"
    >>> data = pf.get_amf_data(ns, fs)
    
    '''
    
    
    
    '''
  100 100 //nxseg nyseg
    0.000000      14.800000       0.000000      12.100000  //xmin xmax ymin ymax
  1 1 1 1 1 1 //hasEX hasEY hasEZ hasHX hasHY hasHZ
    6.761841       0.000000  //beta
    1.550000  //lambda
  0 //iscomplex
  1 //isWGmode
    '''
    import re   # RegEx module
    
    # write an AMF file with all the field components.
    if not filename.endswith(".amf"):  filename += ".amf"   # name of the files
    
    # SubFolder to hold temp files:
    if not os.path.isdir(str( AMF_FolderStr() )):
        os.mkdir(str( AMF_FolderStr() ))        # Create the new folder if needed
    mode_FileStr = os.path.join( AMF_FolderStr(), filename )
    
    if DEBUG(): print "Mode.plot():  " + modestring + ".writeamf("+mode_FileStr+",%s)"%precision
    fimm.Exec(modestring + ".writeamf("+mode_FileStr+",%s)"%precision)

    ## AMF File Clean-up
    #import os.path, sys  # moved to the top
    fin = open(mode_FileStr, "r")
    if not fin: raise IOError("Could not open '"+ mode_FileStr + "' in " + sys.path[0] + ", Type: " + str(fin))
    #data_list = fin.readlines()        # put each line into a list element
    data_str = fin.read( maxbytes )     # read file as string, up to maxbytes.
    fin.close()
    
    out = {}    # the data to return, as dictionary
    
    ''' Grab the data from the header lines '''
    # how much of the data to search (headers only):
    s = [0, 2000]   # just in case the entire file gets read in later, to grab field data
    # should disable this once we know we don't need the AMF field data
    
    # Set regex pattern to match:
    '''  100 100 //nxseg nyseg'''
    pat = re.compile(     r'\s*(\d+)\s*(\d+)\s*//nxseg nyseg'  )
    m = pat.search(  data_str[s[0]:s[1]]  )      # perform the search
    # m will contain any 'groups' () defined in the RegEx pattern.
    if m:
        print 'segment counts found:', m.groups()   #groups() prints all captured groups
        nx = int( m.group(1) )	# grab 1st group from RegEx & convert to int
        ny = int( m.group(2) )
        print '(nx, ny) --> ', nx, ny
    out['nx'],out['ny'] = nx, ny

    # Set regex pattern to match:
    '''    0.000000      14.800000       0.000000      12.100000  //xmin xmax ymin ymax'''
    pat = re.compile(     r'\s*(\d+\.?\d*)\s*(\d+\.?\d*)\s*(\d+\.?\d*)\s*(\d+\.?\d*)\s*//xmin xmax ymin ymax'  )
    m = pat.search(  data_str[s[0]:s[1]]  )      # perform the search
    # m will contain any 'groups' () defined in the RegEx pattern.
    if m:
        print 'window extents found:',m.groups()    #groups() prints all captured groups
        xmin = float( m.group(1) )	# grab 1st group from RegEx & convert to int
        xmax = float( m.group(2) )
        ymin = float( m.group(3) )
        ymax = float( m.group(4) )
        print '(xmin, xmax, ymin, ymax) --> ', xmin, xmax, ymin, ymax
    out['xmin'],out['xmax'],out['ymin'],out['ymax'] =  xmin, xmax, ymin, ymax

    # Set regex pattern to match:
    '''  1 1 1 1 1 1 //hasEX hasEY hasEZ hasHX hasHY hasHZ'''
    pat = re.compile(     r'\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*//hasEX hasEY hasEZ hasHX hasHY hasHZ'  )
    m = pat.search(  data_str[s[0]:s[1]]  )      # perform the search
    # m will contain any 'groups' () defined in the RegEx pattern.
    if m:
        print 'components found:',m.groups()    #groups() prints all captured groups
        hasEX = bool( int(m.group(1)) )	# grab 1st group from RegEx & convert to int
        hasEY = bool( int(m.group(2)) )
        hasEZ = bool( int(m.group(3)) )
        hasHX = bool( int(m.group(4)) )
        hasHY = bool( int(m.group(5)) )
        hasHZ = bool( int(m.group(6)) )
        print '(hasEX, hasEY, hasEZ, hasHX, hasHY, hasHZ) --> ', hasEX, hasEY, hasEZ, hasHX, hasHY, hasHZ
    out['hasEX'],out['hasEY'],out['hasEZ'],out['hasHX'],out['hasHY'],out['hasHZ'] \
        = hasEX, hasEY, hasEZ, hasHX, hasHY, hasHZ

    # Set regex pattern to match:
    '''    6.761841       0.000000  //beta'''
    pat = re.compile(     r'\s*(\d+\.?\d*)\s*(\d+\.?\d*)\s*//beta'  )
    m = pat.search(  data_str[s[0]:s[1]]  )      # perform the search
    # m will contain any 'groups' () defined in the RegEx pattern.
    if m:
        print 'beta found:',m.groups()    #groups() prints all captured groups
        beta_r = float( m.group(1) )	# grab 1st group from RegEx & convert to int
        beta_i = float( m.group(2) )
        beta = beta_r + beta_i*1j
        print 'beta --> ', beta
    out['beta'] = beta

    # Set regex pattern to match:
    '''    1.550000  //lambda'''
    pat = re.compile(     r'\s*(\d+\.?\d*)\s*//lambda'  )
    m = pat.search(  data_str[s[0]:s[1]]  )      # perform the search
    # m will contain any 'groups' () defined in the RegEx pattern.
    if m:
        print 'lambda found:',m.groups()    #groups() prints all captured groups
        lam = float( m.group(1) )	# grab 1st group from RegEx & convert to int
        print 'lambda --> ', lam
    out['lambda'] =  lam 


    # Set regex pattern to match:
    '''  0 //iscomplex'''
    pat = re.compile(     r'\s*(\d)\s*//iscomplex'  )
    m = pat.search(  data_str[s[0]:s[1]]  )      # perform the search
    # m will contain any 'groups' () defined in the RegEx pattern.
    if m:
        print 'iscomplex found:',m.groups()    #groups() prints all captured groups
        iscomplex = bool( int(m.group(1)) )	# grab 1st group from RegEx & convert to int
        print 'iscomplex --> ', iscomplex
    out['iscomplex'] =  iscomplex 

    # Set regex pattern to match:
    '''  1 //isWGmode'''
    pat = re.compile(     r'\s*(\d)\s*//isWGmode'  )
    m = pat.search(  data_str[s[0]:s[1]]  )      # perform the search
    # m will contain any 'groups' () defined in the RegEx pattern.
    if m:
        print 'isWGmode found:',m.groups()    #groups() prints all captured groups
        isWGmode = bool( int(m.group(1)) )	# grab 1st group from RegEx & convert to int
        print 'isWGmode --> ', isWGmode
    out['isWGmode'] =  isWGmode



    
    
    return out
    
    """
    # Delete File Header
    nxy_data = data_list[1]
    xy_data = data_list[2]
    slvr_data = data_list[6]
    del data_list[0:9]
    
    # strip the comment lines from the nxy file:
    nxyFile = os.path.join( AMF_FolderStr(), "mode" + str(num) + "_pyFIMM_nxy.txt")
    fout = open(nxyFile, "w")
    fout.writelines(nxy_data)
    fout.close()
    nxy = pl.loadtxt(nxyFile, comments='//')
    nx = int(nxy[0])
    ny = int(nxy[1])
    
    xyFile = os.path.join( AMF_FolderStr(), "mode" + str(num) + "_pyFIMM_xy.txt")
    fout = open(xyFile, "w")
    fout.writelines(xy_data)
    fout.close()
    xy = pl.loadtxt(xyFile, comments='//')
    
    slvrFile = os.path.join( AMF_FolderStr(), "mode" + str(num) + "_pyFIMM_slvr.txt")
    fout = open(slvrFile, "w")
    fout.writelines(slvr_data)
    fout.close()
    iscomplex = pl.loadtxt(slvrFile, comments='//')

    # Find Field Component
    if field_cpt_in == None:
        '''If unspecified, use the component with higher field frac.'''
        tepercent = fimm.Exec(self.modeString + "list[{" + str(num) + "}].modedata.tefrac")
        if tepercent > 50:
            field_cpt = 'Ex'.lower()
        else:
            field_cpt = 'Ey'.lower()
    #end if(field_cpt_in)
    
    if field_cpt == 'Ex'.lower():
        data = data_list[1:nx+2]
    elif field_cpt == 'Ey'.lower():
        data = data_list[(nx+2)+1:2*(nx+2)]
    elif field_cpt == 'Ez'.lower():
        data = data_list[2*(nx+2)+1:3*(nx+2)]
    elif field_cpt == 'Hx'.lower():
        data = data_list[3*(nx+2)+1:4*(nx+2)]
    elif field_cpt == 'Hy'.lower():
        data = data_list[4*(nx+2)+1:5*(nx+2)]
    elif field_cpt == 'Hz'.lower():
        data = data_list[5*(nx+2)+1:6*(nx+2)]
    else:
        ErrStr = 'Invalid Field component requested: ' + str(field_cpt)
        raise ValueError(ErrStr)
    
    del data_list
    
    # Resave Files
    fout = open(mode_FileStr+"_"+field_cpt.strip().lower(), "w")
    fout.writelines(data)
    fout.close()
    
    # Get Data
    if iscomplex == 1:
        field_real = pl.loadtxt(mode_FileStr, usecols=tuple([i for i in range(0,2*ny+1) if i%2==0]))
        field_imag = pl.loadtxt(mode_FileStr, usecols=tuple([i for i in range(0,2*ny+2) if i%2!=0]))
    else:
        field_real = pl.loadtxt(mode_FileStr)
    """


#end get_amf_data()