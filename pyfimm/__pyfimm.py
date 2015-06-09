'''
pyFIMM - main module

See help on the main module, `help(pyFIMM)`, for usage info.

This file contains the higher-level classes, such as Project, Node, Material, Layer, Slice and Section.
Waveguide, Circ and Device classes/functions are in their respective separate files.
Also in this file are the pyFIMM global parameters - set_wavelength, set_N etc. etc.
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

import numpy as np
import datetime as dt   # for date/time strings
import os.path      # for path manipulation
import random       # random number generators





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
        NumSubnodes = int(  fimm.Exec("app.numsubnodes")  )
        print "Connected! (%i Project nodes found)"%NumSubnodes
    except:
        ErrStr = "Unable to connect to Fimmwave app - make sure it is running & license is active."
        raise IOError(ErrStr)

    
def disconnect():
    '''Terminate the connection to the FimmWave Application & delete the object.'''
    global pd # use this module-level variable.  Dunno why the `global` declaration is only needed in THIS module function (not others!), in order to delete it...
    del pd    # pdPythonLib does some cleanup upon del()'ing


def Exec(string, vars=[]):
    '''Send a raw command to the fimmwave application.  
    See `help(<pyfimm>.PhotonDesignLib.pdPythonLib.Exec)` for more info.'''
    out = fimm.Exec(string, vars)
    if isinstance(out, str):
        '''if fimm.Exec returned a string, FimmWave usually appends `\n\x00' to the end'''
        if out[-2:] == '\n\x00': out = out[:-2]     # strip off FimmWave EOL/EOF chars.
    return out

def striptxt(FimmString):
    '''Remove the EOL characters from FimmWave output strings.'''
    junkchars = '\n\x00'    # characters to remove
    if FimmString.endswith(junkchars): out = FimmString.strip( junkchars )     # strip off FimmWave EOL/EOF chars.
    return out

def striparray(FimmArray):
    '''Remove EOL & 'None' elements of a returned list or array.'''
    if  isinstance( FimmArray,  list ):
        if  FimmArray[0]  is None:  out = FimmArray[1:]     # omit 1st 'None' element
    

def checkNodeName( name, level=0, warn=True ):
    ''' See if the project name exists in FimmWave, and return a modified project name (with ms time-stamp) if it exists.
    level=0 means top-level (project names only).  This is currently the only supported mode.  Eventually could support checking names of subnodes.
    
    Returns
    -------
    nodename : str
        Name of the offending identically-named node.
    
    nodenum : int
        Node Number of the offending identically-named node.
    '''
    if level==0: nodestring = "app."    # top-level
    N_nodes = int(  fimm.Exec(nodestring+"numsubnodes")  )
    SNnames = []    #subnode names
    for i in range(N_nodes):
        SNnames.append(  fimm.Exec(nodestring+r"subnodes["+str(i+1)+"].nodename").strip()[:-2]  )   
        # trim whitespace via string's strip(), strip the two EOL chars '\n\x00' from end via indexing [:-2]
    # check if node name is in the node list:
    sameprojnum = np.where( np.array(SNnames) == np.array([name]) )[0]
    #if DEBUG(): print "Node._checkNodeName(): [sameprojname] = ", sameprojname, "\nSNnames= ", SNnames
    if len( sameprojnum  ) > 0:
        '''if identically-named node was found'''
        '''change the name of this new node'''
        if warn: print "WARNING: Node name `" + name + "` already exists;"
        sameprojnum = sameprojnum[0]+1
        name += "." +str( get_next_refnum() )       #dt.datetime.now().strftime('.%f')   # add current microsecond to the name
        print "\tNode name changed to: ", name
    else:
        if DEBUG(): print "Node name `%s` is unique." % name
        pass
    return name, sameprojnum
#end checknodename()


def get_next_refnum():
    '''Returns a 6-digit random number to use for naming new FimmWave references/nodes.  Will ensure that a duplicate is never returned.  All used values are stored in the pyFIMM global variable `global_refnums`.'''
    global global_refnums
    try:
        global_refnums
    except NameError:
        global_refnums = []     # default value if unset
    
    cont, i =  1,1
    while cont == 1:
        ''' If random number `r` is already in the global list, make a new one '''
        r = random.randint(100000,999999)   # 6-digit random number
        if len( np.where(  np.array(global_refnums) == np.array([r]) )[0]  ) == 0:
            ''' If random number `r` is not in the global list, continue '''
            cont = 0    # stop the loop
        
        # make sure the loop doesn't run away, in case the used has made 1 million objects!
        i = i+1
        if i > 1000:
            cont = 0
            raise UserWarning("Could not generate a random number after 1000 iterations! Aborting...")
    # end while(cont)
    
    global_refnums.append(  r  )
    return global_refnums[-1]   # return last random number



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
         



####################################################################################
# Classes
####################################################################################
class Node(object):
    """class Node: creates a Fimmwave node
        Node() - Creates TimeStamped Node Name, Number 0, No Parent or Children
        Node('NameOfNode')
        Node('NameOfNode', NodeNumber)
        Node('NameOfNode', NodeNumber, ParentNodeObject)
        Node('NameOfNode', NodeNumber, ParentNodeObject, Children)
        
        If 'NameOfNode' already exists, the name will be modified by adding a random number to the end as ".123456".
        The modified name can be found in the variable: `Node.name`
        if the keyword argument `overwrite=True` is provided, then an existing Node with the same name will be deleted upon building."""
    def __init__(self,*args, **kwargs):
        if len(args) == 0:
            self.name = 'Fimmwave Node ' + dt.datetime.now().strftime("%Y-%m-%d %H.%M.%S")
            self.num = 0
            self.parent = None
            self.children = []
            self.type = None
            self.savepath = None
        elif len(args) == 1:
            self.name = args[0]
            self.num = 0
            self.parent = None
            self.children = []
            self.type = None
            self.savepath = None
        elif len(args) == 2:
            self.name = args[0]
            self.num = args[1]
            self.parent = None
            self.children = []
            self.type = None
            self.savepath = None
        elif len(args) == 3:
            self.name = args[0]
            self.num = args[1]
            self.parent = args[2]
            self.children = []
            self.type = None
            self.savepath = None
        elif len(args) == 4:
            self.name = args[0]
            self.num = args[1]
            self.parent = args[2]
            self.children = args[3]
            self.type = None
            self.savepath = None
        else:
            print 'Invalid number of input arguments to Node()'
        
        
        overwrite = kwargs.pop('overwrite', False)  # to overwrite existing project of same name
        warn = kwargs.pop('warn', True)     # display warning is overwriting?
        
        """
        ## Check if top-level node name conflicts with one already in use:
        #AppSubnodes = fimm.Exec("app.subnodes")        # The pdPythonLib didn't properly handle the case where there is only one list entry to return.  Although we could now use this function, instead we manually get each subnode's name:
        N_nodes = int(  fimm.Exec("app.numsubnodes")  )
        SNnames = []
        for i in range(N_nodes):
            SNnames.append(  fimm.Exec(r"app.subnodes["+str(i+1)+"].nodename").strip()[:-2]  )   
            # trim whitespace with string's strip(), strip the EOL chars '\n\x00' from end with indexing [:-2]
        
        # check if node name is in the node list:
        sameprojname = np.where( np.array(SNnames) == np.array([self.name]) )[0]
        if DEBUG(): print "Node.buildNode(): [sameprojname] = ", sameprojname, "\nSNnames= ", SNnames
        if len( sameprojname  ) > 0:
            '''if identically-named node was found'''
            if overwrite:
                '''delete the offending identically-named node'''
                if warn: print "Deleting Node #" + str(sameprojname) + " `" + SNnames[sameprojname] + "`."
                sameprojname = sameprojname[0]+1
                fimm.Exec("app.subnodes["+str(sameprojname)+"].delete")
            else: 
                '''change the name of this new node'''
                if warn: print "WARNING: Node name `" + self.name + "` already exists;"
                self.name += "." +str( get_next_refnum() )  #dt.datetime.now().strftime('.%f')   # add current microsecond to the name
                print "\tNode name changed to: ", self.name
            #end if(overwrite)
        else:
            if DEBUG(): print "Node name is unique."
        #end if(self.name already exists aka. len(sameprojname)
        """
        
        
        if kwargs:
            '''If there are unused key-word arguments'''
            ErrStr = "WARNING: Node(): Unrecognized keywords provided: {"
            for k in kwargs.iterkeys():
                ErrStr += "'" + k + "', "
            ErrStr += "}.    Continuing..."
            print ErrStr
    #end __init__()
    
    def _checkNodeName(self, nodestring, overwrite=False, warn=True):
        '''Check for duplicate node name, overwrite if desired.'''
        ## Check if top-level node name conflicts with one already in use:
        #AppSubnodes = fimm.Exec("app.subnodes")        # The pdPythonLib didn't properly handle the case where there is only one list entry to return.  Although we could now use this function, instead we manually get each subnode's name:
        N_nodes = int(  fimm.Exec(nodestring+"numsubnodes")  )
        SNnames = []    #subnode names
        for i in range(N_nodes):
            SNnames.append(  fimm.Exec(nodestring+r"subnodes["+str(i+1)+"].nodename").strip()[:-2]  )   
            # trim whitespace via string's strip(), strip the two EOL chars '\n\x00' from end via indexing [:-2]
        # check if node name is in the node list:
        sameprojname = np.where( np.array(SNnames) == np.array([self.name]) )[0]
        #if DEBUG(): print "Node._checkNodeName(): [sameprojname] = ", sameprojname, "\nSNnames= ", SNnames
        if len( sameprojname  ) > 0:
            '''if identically-named node was found'''
            if overwrite:
                '''delete the offending identically-named node'''
                if warn: print "Overwriting existing Node #" + str(sameprojname) + ", `" + SNnames[sameprojname] + "`."
                sameprojname = sameprojname[0]+1
                fimm.Exec(nodestring+"subnodes["+str(sameprojname)+"].delete")
            else: 
                '''change the name of this new node'''
                if warn: print "WARNING: Node name `" + self.name + "` already exists;"
                self.name += "." +str( get_next_refnum() )      #dt.datetime.now().strftime('.%f')   # add current microsecond to the name
                print "\tNode name changed to: ", self.name
            #end if(overwrite)
        else:
            #if DEBUG(): print "Node name is unique."
            pass
        #end if(self.name already exists aka. len(sameprojname) )
        
        
    
    def set_parent(self,parent_node):
        self.parent = parent_node
        parent_node.children.append(self)
        
    def delete(self):
        if self.parent is None:
            fimm.Exec("app.subnodes[{"+str(self.num)+"}].delete()")
        else:
            fimm.Exec("app.subnodes[{"+str(self.parent.num)+"}].subnodes[{"+str(self.num)+"}].delete()")
            
#end class Node

            
            
class Project(Node):
    """Create new Fimmwave Project, with incremented node number.
    Project inherits from the Node class. 
    Arguments are passed to this Node class constructor - type help('pyFIMM.Node') for available arguments.
    
    Parameters
    ----------
    buildNode : { True | False }
        build the project node as well?
    overwrite : { True | False }
        if True, will overwrite an already-open project with the same name in Fimmwave.  If False, will append timestamp (ms only) to supplied project name.
    name : string
        Set the fimmwave name for this node
        """
    def __init__(self, *args, **kwargs):
        self.built = False
        build = kwargs.pop('buildNode', False)  # to buildNode or not to buildNode?
        #overwrite = kwargs.pop('overwrite', False)  # to overwrite existing project of same name
        super(Project, self).__init__(*args, **kwargs)   # call Node() constructor, passing extra args
        kwargs.pop('overwrite', False)  # remove kwarg's which were popped by Node()
        kwargs.pop('warn', False)
        if build: self.buildNode(  )    # Hopefully Node `pops` out any kwargs it uses.
        
        if kwargs:
            '''If there are unused key-word arguments'''
            ErrStr = "WARNING: Project(): Unrecognized keywords provided: {"
            for k in kwargs.iterkeys():
                ErrStr += "'" + k + "', "
            ErrStr += "}.    Continuing..."
            print ErrStr
        
    def buildNode(self, name=None, overwrite=False):
        '''Build the Fimmwave node of this Project.
        
        Parameters
        ----------
        name : string, optional
            Provide a name for this waveguide node.
        overwrite : { True | False }
            If True, will overwrite an already-open project with the same name in Fimmwave.  If False, will append timestamp (ms only) to supplied project name.
        '''
        
        if DEBUG(): print "Project.buildNode():"
        if name: self.name = name
        self.type = 'project'   # unused!
        
        ## Check if top-level (project) node name conflicts with one already in use:
        #AppSubnodes = fimm.Exec("app.subnodes")        # The pdPythonLib didn't properly handle the case where there is only one list entry to return.  Although we could now use this function, instead we manually get each subnode's name:
        N_nodes = int(  fimm.Exec("app.numsubnodes")  )
        SNnames = []    #subnode names
        for i in range(N_nodes):
            SNnames.append(  fimm.Exec(r"app.subnodes["+str(i+1)+"].nodename").strip()[:-2]  )   
            # trim whitespace via string's strip(), strip the two EOL chars '\n\x00' from end via indexing [:-2]
        
        ## NOTE: the following code is already run by the Node() constructor if called as wg_prj=Project('name'), but calling Project.buildNode(name, parent) doesn't run the node constructor, so I have to re-run the code here.  I think that's correct - either way we shouldn't have to code this twice.
        # check if node name is in the node list:
        sameprojname = np.where( np.array(SNnames) == np.array([self.name]) )[0]
        #if DEBUG(): print "Node.buildNode(): [sameprojname] = ", sameprojname, "\nSNnames= ", SNnames
        if len( sameprojname  ) > 0:
            '''if identically-named node was found'''
            if overwrite:
                '''delete the offending identically-named node'''
                print self.name + ".buildNode(): Overwriting existing Node #" + str(sameprojname) + ", `" + SNnames[sameprojname] + "`."
                sameprojname = sameprojname[0]+1
                fimm.Exec("app.subnodes["+str(sameprojname)+"].delete")
            else: 
                '''change the name of this new node'''
                print self.name + ".buildNode(): WARNING: Node name `" + self.name + "` already exists;"
                self.name += "." +str( get_next_refnum() )      #dt.datetime.now().strftime('.%f')   # add current microsecond to the name
                print "\tNode name changed to: ", self.name
            #end if(overwrite)
        else:
            #if DEBUG(): print "Node name is unique."
            pass
        #end if(self.name already exists) aka. len(sameprojname)
        
        '''Create the new node:     '''
        N_nodes = fimm.Exec("app.numsubnodes")
        node_num = int(N_nodes)+1
        fimm.Exec("app.addsubnode(fimmwave_prj,"+str(self.name)+")")
        self.num = node_num
        self.savepath = None
        self.built = True
    
    
    def savetofile(self, path=None, overwrite=False):
        '''savetofile(path): 
        Save the Project to a file.  Path is subsequently stored in `Project.savepath`. 
        
        Parameters
        ----------
        path : string, optional
            Relative (or absolute?) path to file.  ".prj" will be appended if it's not already present.
            If not provided, will assume the Project has been saved before, and will save to the same path (you should set `overwrite=True` in this case).
        overwrite : { True | False }, optional
            Overwrite existing file?  False by default.  Will error with "FileExistsError" if this is false & file already exists.
        '''
        
        if path == None:
            if self.savepath:
                path = self.savepath
            else:
                ErrStr = 'Project.savetofile(): path not provided, and project does not have `savepath` set (has never been saved before).  Please provide a path to save file.'
                raise ValueError(ErrStr)
        
        if path.split('.')[-1] != 'prj':    path = path + '.prj'    # append '.prj' if needed
        
        if os.path.exists(path) and overwrite: 
            print self.name + ".savetofile(): WARNING: File `" + os.path.abspath(path) + "` will be overwritten."
            fimm.Exec("app.subnodes[{"+str(self.num)+"}].savetofile(" + path + ")")
            self.savepath = os.path.abspath(path)
            print self.name + ".savetofile(): Project `" + self.name + "` saved to file at: ", os.path.abspath(self.savepath)
        elif os.path.exists(path) and not overwrite:
            raise IOError(self.name + ".savetofile(): File `" + os.path.abspath(path) + "` exists.  Use parameter `overwrite=True` to overwrite the file.")
        else:
            fimm.Exec("app.subnodes[{"+str(self.num)+"}].savetofile(" + path + ")")
            self.savepath = os.path.abspath(path)
            print self.name + ".savetofile(): Project `" + self.name + "` saved to file at: ", os.path.abspath(self.savepath)
        #end if(file exists/overwrite)
    #end savetofile()
    
    
#end class(Project)


def import_Project(filepath, name=None, overwrite=False, warn=True):
    '''Import a Project from a file.  
    
    filepath : string
        Path (absolute or relative?) to the FimmWave .prj file to import.
    
    name : string, optional
        Optionally provide a name for the new Project node in Fimmwave.  If omitted, the Project name save in the file will be used.
    
    overwrite : { True | False }, optional
        If True, will overwrite an already-open Fimmwave project that has the same name in Fimmwave.  If False, will append timestamp (ms only) to supplied project name.  False by default.
    
    warn : { True | False }, optional
        Print or suppress warnings when nodes will be overwritten etc.  True by default.
    
    '''
    '''For ImportDevice: Path should be path (string) to the FimmWave node, eg. 'Dev1' if Device withthat name is in the top-level of the project, or 'Dev1/SubDev' if the target Device is underneath another Device node.'''
    # Create Project object.  Set the "path", 'num', 'name' attributes of the project.
    # return a project object
    
    if DEBUG(): print "importProject():"
    
    if os.path.isfile(filepath):
        savepath = os.path.abspath(filepath)
    else:
        ErrStr = "FimmProp Project file does not exist at the specified path `%s`" %(path)
        raise IOError(ErrStr)
    
    
    # Open the project file, and 
    #   make sure the project name isn't already in the FimmWave node list (will pop a FimmWave error)
    if name is None:
        # Get name from the Project we're opening
        prjf = open(filepath)
        prjtxt = prjf.read()
        prjf.close()
    
        import re   # regex matching
        ''' In the file: 
        begin <fimmwave_prj(1.0)> "My Project Name"
        '''
        prjname_pattern = re.compile(     r'.*begin \<fimmwave_prj\(\d\.\d\)\> "(.*)".*'    )
        # perform the search:
        m = prjname_pattern.search(  prjtxt  )      # use regex pattern to extract project name
        # m will contain any 'groups' () defined in the RegEx pattern.
        if m:
            prjname = m.group(1)	# grab 1st group from RegEx
            if DEBUG(): print 'Project Name found:', m.groups(), ' --> ', prjname
        #groups() prints all captured groups
    else:
        prjname = name
    
    newprjname, newnodenum = checkNodeName( prjname )  # get modified nodename & nodenum of same-named Proj.
    nodestring = "app."
    if newprjname != prjname:
        '''Project with same name exists'''
        if overwrite:
            '''delete the offending identically-named node'''
            if warn: print "Overwriting existing Node #" + str(newnodenum) + ", '%s'." % prjname
            fimm.Exec(nodestring+"subnodes["+str(newnodenum)+"].delete")
            newprjname = prjname    #use orig name
    #end if(project already exists)
    
    
    
    '''Create the new node:     '''
    N_nodes = fimm.Exec("app.numsubnodes")
    node_num = int(N_nodes)+1
    '''app.openproject: FUNCTION - ( filename[, nodename] ): open the specified project with the specified node name'''
    fimm.Exec("app.openproject(" + str(filepath) + ', "'+ newprjname + '" )'  )   # open the .prj file
    
    prj = Project()     # new Project obj
    prj.type = 'project'  # unused!
    prj.num = node_num
    prj.built = True
    prj.savepath = savepath
    prj.name = striptxt(  fimm.Exec(  "app.subnodes[%i].nodename " % prj.num  )  )
    
    prj.origin = 'fimm'
    
    
    
    return prj
#end ImportProject()


'''
app.openproject(T:\MZI Encoder\MZI Encoder v8.prj,"")  <-- see if 2nd arg is NodeName, if so, could obviate issue with re-opening a project (name already exists)
app.subnodes[1].nodename
    MZI Encoder
    
app.subnodes[1].findnode(/SiN Slab)
    could not find node "/SiN Slab"
    
app.subnodes[1].findnode(SiN Slab)
app.subnodes[1].findnode(SiN Slab)
app.subnodes[1].filename
    T:\MZI Encoder\MZI Encoder v8.prj
    
    
app.openproject(T:\MZI Encoder\MZI Encoder v8.prj,"")
app.subnodes[1].delete()
app.openproject(T:\MZI Encoder\MZI Encoder v8.prj,"")
app.subnodes[1].writeblock()
    begin <fimmwave_prj(1.0)> "MZI Encoder"
      begin <pdVariablesNode(1.0)> "Variables 1"
        tCore = 0.06
        wCore = 1.25
        tUClad = 1
        
        ...
        ...
        ...
'''

class Material(object):
    """Create a new pyFimm Material with refractive index & k (loss coefficient):
        To produce a simple refractive-index type of material, pass the refractive index (float) as the first argument:
            >>> Silicon = pyfimm.Material( 3.569 )
        this assumes loss, k=0.  Pass a non-zero imaginary/absorption component (k) if desired:
            >>> Silicon = pyfimm.Material( 3.569 , 0.0012 )
        
        To utilize a wavelength-dependent model (without having to rebuild the structure each time), you must provide a fimmwave Material Database via
            >>> pyfimm.set_material_database('C:\FimmWave\matref.mat')
        and then pass a string as the first argument, like so:
            >>> Silicon = pyfimm.Material( 'Silicon' )
        choose the mole ratio in the second argument, 
            >>> Al20_Ga80_As = pyfimm.Material( 'AlGaAs', 0.20 )    # 20% Aluminum
        or, for quaternary material, mole-ratio x & y (aka. mx & my):
            >>> In_Ga51_As49_P = pyfimm.Material( 'InGaAsP', 0.51, 0.49 ) #51% Ga, 49% As
            
        mx & my can also be set with keyworded args for clarity, as so:
            >>> InGa51As49P = pyfimm.Material( 'InGaAsP', mx=0.51, my=0.49 )
        
        You will have to open the fimmwave material database file for details on the materials available & definition of the mole-ratio parameters (in one case they are actually wavelengths...).
        
        Called with no arguments, `Material()` returns a material like air with n=1.0, k=0.
        
        
        Material objects are subsequently used to create waveguides with these materials, like so:
        
            >>> Silicon = Material(3.4)     # set refractive index of Silicon material object
            >>> core = Silicon( 1.50 )      # call the Material object to return a Layer of given thickness
                Here, `core` is a Layer object with thickness 1.50 um & refractive index from the Silicon object, of 3.4
                
        Can also set the layer as the Confinement Factor area (cfseg), as so:
            >>> core = Silicon( 1.50, cfseg=True)    # sets this layer's `cfseg` flag
        """
    def __init__(self,*args, **kwargs):
        if len(args) == 0:
            '''Air by default'''
            self.type='rix'     #refractive index type
            self.n = 1.0
            self.k = 0.0
            self.mat=None
            self.mx=None
            self.my=None
        elif len(args) >= 1:
            if isinstance(args[0], str):
                # if 1st arg is a string:
                self.type='mat'     # use material database
                self.mat=args[0]    # material name
                self.mx = None
                self.my = None
                self.n = None
                self.k = None
            else:
                self.type='rix'     # refractive index type
                self.n = args[0]    # RIX index
                self.k = 0.0
                self.mat=None
                self.mx=None
                self.my=None
        
        if len(args) >= 2:
            if self.type=='mat':
                self.mx = args[1]   # mole ratio x
                self.my = None
            else:
                self.k = args[1]    # RIX loss - k coeff.
        
        if len(args) ==3:
            if self.type=='mat':
                self.my=args[2]     # mole ratio y
            else:
                raise ValueError("Invalid number of arguments for Refractive Index-type of material.")
        
        if len(args) >= 4:
            raise ValueError('Invalid number of input arguments to Material Constructor')

        # Allow some params to be set by keyword args, if not already set:
        if not self.mx: self.mx = kwargs.pop('mx', None)
        if not self.my: self.my = kwargs.pop('my', None)
        
        if kwargs:
            '''If there are unused key-word arguments'''
            ErrStr = "WARNING: Material(): Unrecognized keywords provided: {"
            for k in kwargs.iterkeys():
                ErrStr += "'" + k + "', "
            ErrStr += "}.    Continuing..."
            print ErrStr
    #end __init__
        
    def __str__(self):
        '''How to `print` this object'''
        if self.type == 'rix':
            return 'n = %1.4f' % self.n + '\n' + 'k = %1.4f' % self.k
        else:
            return 'Material = "%s" \n' %(self.mat) + "with mx=%s & my=%s." %(self.mx, self.my)

    def __call__(self,length, cfseg=False):
        '''Calling a Material object with one argument creates a Layer of passed thickness and refr.index of Material, and returns a list containing this new Layer. For example:
            >>> Silicon = Material(3.4) 
            >>> core = Silicon( 1.50 )  
                Here, core is a list containing one Layer object with thickness 1.50 um & refractive index from the Silicon object, of 3.4
        Can also set the layer as the Confinement Factor area (cfseg), as so:
            >>> core = Silicon( 1.50, cfseg=True)    # sets this layer as the cfseg
        '''
        
        # Always call Layer with 3 args, but CFseg is False by default.
        out = [   Layer(  self, length, cfseg  )   ]    # include cfseg 
        return out
    #end __call__
    
#end class(Material)



class Layer:
    """Layer( mat, thick, CFseg)
    Create new pyFimm Layer, a slab waveguide of some index and thickness.
    Usually not created manually, but instead returned when user passes a thickness to a Material object.  
    
    
    Parameters
    ----------
    mat : Material object
        Material object, provides n & k info
    thick : float
        Thickness of this layer
    CFseg : { True | False }
        Should this layer be considered in confinement factor (CF) calculations?  Sets the FimmWave `cfseg` bit.
    
    
    Examples
    --------
    Typically created by calling a Material object:
        >>> Silicon = Material( 3.44 )
    Call this Material object with a thickness applied, returns a Layer object:
        >>> Layer = Silicon( 0.150 )
    But we usually just pass this layer directly to the Slice constructor, eliminating the middle-man for simplicity:
        >>> CoreSlice = Slice(   SiO(5.0) + Silicon(0.150) + SiO(5.0)   )
        
    It's not recommended, but you can create a Layer by itself like so:
        >>> Layer() - empty class
        >>> Layer( Material )
        >>> Layer( Material, Thickness)
        >>> Layer( Material, Thickness, CFseg )"""
    
    def __init__(self,*args):
        if len(args) == 0:
            self.material = []
            self.thickness = 0
            self.cfseg = False
        elif len(args) == 1:
            self.material = args[0]
            self.thickness = 0
            self.cfseg = False
        elif len(args) == 2:
            '''This case is used when calling a Material object with one arg'''
            self.material = args[0]
            self.thickness = args[1]
            self.cfseg = False
        elif len(args) == 3:
            '''This case is used when calling a Material object with two args.'''
            self.material = args[0]
            self.thickness = args[1]
            self.cfseg = args[2]
        else:
            raise ValueError( 'Invalid number of input arguments to Layer Constructor' )

    def __str__(self):
        '''How to `print` this object'''
        mat = self.material
        return '%s' % mat + '\n' + 'thickness = %7.4f microns' % self.thickness + '\n' + 'cfseg = %s' % self.cfseg

    def __add__(self,other):
        '''Addition returns a list containing new Layer appended to this Layer'''
        return [self,other]
    
    def get_n(self):
        '''Return refractive index of Material in this Layer'''
        return self.material.n
    # alias for this function:
    n = get_n

    def get_k(self):
        '''Return imaginary refractive index (loss) of Material in this Layer'''
        return self.material.k
    # alias for this function:
    k = get_k 
        
    def set_cfseg(self):
        '''Set this Layer as a cfseg - area to include in confinement factor calculations.'''
        self.cfseg = True
        
    def unset_cfseg(self):
        '''UnSet this Layer as a cfseg - area won't be included in confinement factor calculations.'''
        self.cfseg = False
        
    def get_cfseg(self):
        '''Return cfseg status of this Layer as { True | False }.'''
        return self.cfseg
#end class(Layer)



class Slice:
    """
    Slice( [BunchOfLayers, WidthOfSlice, EtchDepth ] )
    
    pyFimm Slice object, a concatenation of multiple Layer objects (Materials of some thickness).
    Can accomodate an arbitrary number of Layers.
    This converts the 1-D Layers into a 2-D Slice.
    
    
    
    Parameters
    ----------
    BunchOfLayers : list
        A List containing all the Layers to be put into this Slice.  See examples.
    WidthOfSlice : float
        The width of this slice, in perpendicular direction as the Layer thicknesses.
        This is usually not provided directly here, but instead the width is usually defined when the Slice object is called with a width argument, while making a full rectangular Waveguide object.  See examples.
    EtchDepth : float, optional
        For rectangular waveguides, apply an etch depth to the layer, such that the removed ("etched") portion will be fill in with the material above it.
    
    
    Examples
    --------
    Material Objects return a Layer object when called with a thickness argument.
    Adding Layer objects together produces a List containing each Layer, so BunchOfLayers is actually created by adding a bunch of Material objects (with thicknesses as the argument) together.  
    For example, typical usage is as so:
    
    >>> SlabCore = <pyfimm>.Slice(  Material1(15.0) + Material2(0.75) + Material1(10.0)  )
    Creating an imaginary structure from bottom-to-top like so:
    
            top         
    --------------------
          Material1
        10.0 um thick
    --------------------
          Material2
       0.750 um thick
    --------------------
          Material1
        15.0 um thick
    --------------------
           bottom
    
    The Width is usually applied layer, when creating the rectangular Waveguide object, like so:
    
    >>> SlabClad = <pyfimm>.Slice(  Material1(15.0+0.75+10.0)   )
    >>> WG = <pyfimm>.Waveguide(  SlabClad(10.0) + SlabCore(2.0) + SlabClad(15.0)  )
    Creating a full 2-D Waveguide structure from left-to-right like so:
    
                                top         
    ---------------------------------------------------------
    |<---- 10.0um------>|<-----2.0um------>|<----15.0um---->|
    |                   |     Material1    |                |
    |                   |   10.0 um thick  |                |                
    |                   |------------------|                |
    |     Material1     |     Material2    |    Material1   |
    |      25.75um      |  0.750 um thick  |     25.75um    |
    |       thick       |------------------|      thick     |
    |                   |     Material1    |                |
    |                   |   15.0 um thick  |                |
    ---------------------------------------------------------
                               bottom
    
    Other uses:
    initialize an empty Slice object:
    >>> Slice()   
        
    Pass numerous layers (bottom to top) to concatenate them and make a 1-D Slice:
    
    >>> Slice( BunchOfLayers )   
    
    Also set the width of this slice, for use in 2-D profile construction:
    
    >>> Slice( BunchOfLayers, WidthOfSlice )
    
    Lastly, apply an etch to this slice:
    >>> Slice( BunchOfLayers, WidthOfSlice, EtchDepth )
    
    Applying an EtchDepth will remove the material from the top of the Slice (last Layer passed) down to EtchDepth, replacing it with the Material of the last Layer passed.  For this reason, it is often useful to add a 0-thickness Layer at the end of your BunchOfLayers, eg. air=Layer(1.0, 0.0)"""
    
    def __init__(self,*args):
        if len(args) == 0:
            self.layers = []
            self.width = 0.0
            self.etch = 0.0
        elif len(args) == 1:
            self.layers = []
            for lyr in args[0]:
                self.layers.append(lyr)
            self.width = 0.0
            self.etch = 0.0
        elif len(args) == 2:
            self.layers = []
            for lyr in args[0]:
                self.layers.append(lyr)
            self.width = args[1]
            self.etch = 0.0
        elif len(args) == 3:
            self.layers = []
            for lyr in args[0]:
                self.layers.append(lyr)
            self.width = args[1]
            self.etch = args[2]
        else:
            print 'Invalid number of input arguments to Slice Constructor'

    def __str__(self):
        '''How to `print` this object'''
        str = 'width = %7.4f \n' % self.width
        str += 'etch = %7.4f \n' % self.etch
        for i,lyr in enumerate(self.layers):
            if i == 0:
                str += 3*'*' + ' Bottom Layer: ' + 3*'*' + '\n%r' % (lyr) + '\n'
            elif i == (len(self)-1):
                str += 3*'*' + ' Top Layer: ' + 3*'*' + '\n%r' % (lyr) + '\n'
            else:
                str += 3*'*' + ' Middle Layer %i: ' % i + 3*'*' + '\n%r' % lyr + '\n'
        return str

    def __call__(self,width):
        '''Calling ThisSlice(Width) sets the Width of this Slice, and returns a list containing this Slice.'''
        self.width = width
        return [self]

    def __add__(self,other):
        '''Addition returns a list containing each Slice'''
        return [self,other]

    def __len__(self):
        '''len(ThisSlice) returns the number of Layers in ThisSlice'''
        return len(self.layers)

    def thickness(self):
        '''Return summed thickness of all Layers in this Slice'''
        thck = 0
        for lyr in self.layers:
            thck += lyr.thickness
        return thck

    def layer_thicknesses(self):
        '''Return list of thicknesses of each Layer in this Slice'''
        lyr_thck = []
        for lyr in self.layers:
            lyr_thck.append(lyr.thickness)
        return lyr_thck
#end class Slice



class Section:
    '''Section( WGobject, length)
    Section class applies a Length to a Waveguide object.
    This is so that a Device can reference the same WG multiple times, but with a different length each time.
    Usually not created manually, but instead returned when user passes a length to a WG (Waveguide or Circ) object.
    
    Parameters
    ----------
    WGobject : Waveguide or Circ object
        Waveguide or Circ object, previously built.
    length : float
        length of this WG, when inserted into Device.
        
    To Do:
    ------
    Ability to pass modesolver parameters for this waveguide.
    
    
    Examples
    --------
    Typically created by calling a WG (Waveguide or Circ) object while creating a Device:
        >>> Device1 = Device( WG1(10.5) + WG2(2.5) + WG3(10.5)  )
    
    '''
    
    def __init__(self, *args):
        if len(args) == 1:
            #if DEBUG(): print "Section: 1 args=\n", args
            self.WG = args[0]
            self.length = 0
        elif len(args) == 2:
            #if DEBUG(): print "-- Section: 2 args=\n", args
            self.WG = args[0]
            self.length = args[1]
        else:
            raise ValueError("Invalid number of arguments to Section().")
    
    def __str__(self):
        '''How to `print` this object.'''
        string='Section object (of pyFIMM module).'
        string += '\nlength = %7.4f \n' % self.length
        #if self.WG.name: string += 'WG object: `' + self.WG.name + '`, with '
        string += 'WG type ' + str(type(self.WG)) + ' and structure:\n' + str(self.WG)
        return string
    
    
    def __add__(self,other):
        '''Addition returns a list containing new Section appended to this Section'''
        if DEBUG(): print "Section__Add__: \n", [self,other]
        return [self,other]
    
    def get_length(self):
        '''Return the length of this Section.'''
        return self.length
    
#end class Section







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