'''Various smaller Classes, part of pyFIMM.
This module is imported by pyfimm.py


Included here are the following classes:
Node    (Inherited by all objects that are actual fwNodes)
Project & import_project()
Material
Layer   (Waveguide/Circ)
Slice   (Waveguide)
Section (Device)

Also some Node-specific functions such as strip_txt(), check_node_name() etc.

'''

from __globals import *         # import global vars & FimmWave connection object
# DEBUG() variable is also set in __globals, & numpy as np & pyplot as plt

#from __pyfimm import *      # import the main module (should already be imported)
#  NOTE: shouldn't have to duplicate the entire pyfimm file here!  Should just import the funcs we need...

import os.path      # for path manipulation
import datetime as dt   # for date/time strings
import random       # random number generators


####################################################
# Node-Specific Functions
####################################################

def strip_txt(FimmString):
    '''Remove the EOL characters from FimmWave output strings.'''
    junkchars = '\n\x00'    # characters to remove
    if isinstance(FimmString, str):
        if FimmString.endswith(junkchars): FimmString = FimmString.strip( junkchars )     # strip off FimmWave EOL/EOF chars.
    return FimmString.strip()   # strip whitespace on ends

# Alias for the same function:
strip_text = striptxt = strip_txt

def strip_array(FimmArray):
    '''Remove EOL & 'None' elements of a returned list or array.'''
    print "WARNING: strip_array Incomplete!"
    if  isinstance( FimmArray,  list ):
        if  FimmArray[0]  is None:  FimmArray = FimmArray[1:]     # omit 1st 'None' element
    return FimmArray

def eval_string(fpStr):
    '''Check if a string is numeric, and if so, return the numeric value (as int, float etc.).  If the string is not numeric, the original string is returned.
    This mainly handles the security issues of running `eval()` on random strings returned by Fimmprop.'''
    # convert numbers:
    # only unicode str's have the .isnumeric() method
    if unicode(fpStr).isnumeric(): 
        return eval(fpStr)
    else:
        return fpStr
#end eval_string()

def check_node_name( name, nodestring="app", overwrite=False, warn=True ):
    ''' See if the node name already exists in FimmWave, and return a modified project name (with random numbers appended) if it exists.
    
    Parameters
    ----------
    name : string
        The name to check.  `name` will be checked against all the node-names at the specified level.
    
    nodestring : string, optional
        Specifies the node to check for an existing node name.  Defaults to "app.", which means you're checking top-level Project names.  If, instead, `nodestring = app.subnodes[1].` then you're checking node names within the 1st project in FimmWave.
    
    warn : { True | False }, optional
        Print a warning if the node name exists?  Defaults to True.
    
    overwrite : { True | False }, optional
        If True, will try to delete an already-loaded Fimmwave project that has the same name in Fimmwave.  Will only delete the node if it is the last in the node list (This prevents breaking pyFIMM references to FimmWave Projects). Otherwise, the new FimmWave node will have it's name changed. If False, will append random digits to supplied project name and return it in `nodename`.  False by default.
    
    Returns
    -------
    nodename : str
        New name for the node.  If the original `name` existed in the specified node list, `nodename` will have random digits appended to the name.  Otherwise, it will be left untouched, and be identical to the provided `name`.  Thus, if `nodename != name` then the node `name` already exists in the FimmWave node list.  The modified name will have the form `OrigNodeName.123456`.
    
    sameprojnum : int
        Node Number of the offending identically-named node.  
        Thus the FimmWave command `nodestring + ".subnodes[ nodenum ].delete` will delete the existing node with the same name.
        
        
    Examples
    --------
    Get modified nodename & nodenum of same-named Proj, delete/rename existing node if needed.
    >>> nodestring = "app"
    >>> newprjname, samenodenum = check_node_name( prjname, nodestring=nodestring, overwrite=False, warn=True )  
    Create the new node with returned name, which was modified if needed:
    >>> fimm.Exec(    "app.addsubnode(fimmwave_prj," + str(  newprjname  ) + ")"    )
    
    Do the same, but with `overwrite=True`, ensuring that the name we specify will be used.
    >>> prjname = "My New Project"
    >>> check_node_name( prjname, nodestring="app", overwrite=True )  
    >>> fimm.Exec(    "app.addsubnode(fimmwave_prj," + str(  prjname  ) + ")"    )
    
    '''
    N_nodes = int(  fimm.Exec(nodestring+".numsubnodes()")  )
    SNnames = []    #subnode names
    for i in range(N_nodes):
        SNnames.append(  strip_txt(  fimm.Exec(nodestring+r".subnodes["+str(i+1)+"].nodename()")  )  )   
        # trim whitespace via string's strip(), strip the two EOL chars '\n\x00' from end via indexing [:-2]
    # check if node name is in the node list:
    sameprojidx = np.where( np.array(SNnames) == np.array([name]) )[0]
    #if DEBUG(): print "Node._checkNodeName(): [sameprojname] = ", sameprojname, "\nSNnames= ", SNnames
    if len( sameprojidx  ) > 0:
        '''if identically-named node was found'''
        if warn: print "WARNING: Node name `" + name + "` already exists;"
        sameprojname = SNnames[sameprojidx]
        sameprojidx = sameprojidx[0]+1  # FimmWave index to the offending node
        if overwrite:
            if sameprojidx == N_nodes:
                '''It is the last node entry, so delete the offending identically-named node'''
                if warn: print "node '%s'.buildNode(): Deleting existing Node # %s"%(name,str(sameprojidx)) + ", `%s`."%(sameprojname)
                fimm.Exec( nodestring + ".subnodes[%i].delete()"%(sameprojidx) )
            else:
                '''It is not the last entry in the node list, so we can't delete it without breaking other pyFIMM references.'''
                # change the name of offending node:
                newname = name + "." +str( get_next_refnum() )
                if warn: print "node '%s'.buildNode(): Renaming existing Node #"%(name)  +  str(sameprojidx) + ", `%s` --> `%s`."%(sameprojname, newname)
                fimm.Exec( nodestring + ".subnodes[%i].rename( "%(sameprojidx) + newname + " )"  )
        else:
            '''change the name of this new node'''
            name += "." +str( get_next_refnum() )       #dt.datetime.now().strftime('.%f')   # add current microsecond to the name
            if warn: print "\tNew Node name changed to: ", name
    else:
        if DEBUG(): print "Node name `%s` is unique." % name
        pass
    return name, sameprojidx
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
#end get_next_refnum()



####################################################
# Classes
####################################################
class Node(object):
    """class Node: creates an internal representaiton of a Fimmwave node
        Node() - Creates TimeStamped Node Name, Number 0, No Parent or Children
        Node('NameOfNode')
        Node('NameOfNode', NodeNumber)
        Node('NameOfNode', NodeNumber, ParentNodeObject)
        Node('NameOfNode', NodeNumber, ParentNodeObject, Children)
    
        If 'NameOfNode' already exists, the name will be modified by adding a random number to the end as ".123456".
        The modified name can be found in the variable: `Node.name`
        if the keyword argument `overwrite=True` is provided, then an existing Node with the same name would be deleted upon building."""
    def __init__(self,*args, **kwargs):
        if len(args) >= 0:
            self.name = 'Fimmwave Node ' + dt.datetime.now().strftime("%Y-%m-%d %H.%M.%S")
            self.num = 0
            self.parent = None
            self.children = []
            self.type = None
            self.savepath = None
            self.nodestring = None
        
        if len(args) == 1:
            self.name = args[0]
        elif len(args) == 2:
            self.name = args[0]
            self.num = args[1]
        elif len(args) == 3:
            self.name = args[0]
            self.num = args[1]
            self.parent = args[2]
        elif len(args) == 4:
            self.name = args[0]
            self.num = args[1]
            self.parent = args[2]
            self.children = args[3]
        elif len(args) >= 5:
            print 'Invalid number of input arguments to Node()'
        
        
        #overwrite = kwargs.pop('overwrite', False)  # to overwrite existing project of same name
        #warn = kwargs.pop('warn', True)     # display warning is overwriting?
        
        """
        ## Check if top-level node name conflicts with one already in use:
        #AppSubnodes = fimm.Exec("app.subnodes")        # The pdPythonLib didn't properly handle the case where there is only one list entry to return.  Although we could now use this function, instead we manually get each subnode's name:
        N_nodes = int(  fimm.Exec("app.numsubnodes()")  )
        SNnames = []
        for i in range(N_nodes):
            SNnames.append(  fimm.Exec(r"app.subnodes["+str(i+1)+"].nodename()").strip()[:-2]  )   
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
                fimm.Exec("app.subnodes["+str(sameprojname)+"].delete()")
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
        '''Check for duplicate node name, overwrite if desired.
        
        nodestring : string
            string to reference the FimmWave node, omitting trailing period.  eg. 
                app.subnodes[1].subnodes[3]
        
        overwrite : { True | False }, optional
        
        warn : { True | False }, optional
            '''
        ## Check if top-level node name conflicts with one already in use:
        #AppSubnodes = fimm.Exec("app.subnodes")        # The pdPythonLib didn't properly handle the case where there is only one list entry to return.  Although we could now use this function, instead we manually get each subnode's name:
        N_nodes = int(  fimm.Exec(nodestring+".numsubnodes()")  )
        SNnames = []    #subnode names
        for i in range(N_nodes):
            SNnames.append(  fimm.Exec(nodestring+r".subnodes["+str(i+1)+"].nodename()").strip()[:-2]  )   
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
                fimm.Exec(nodestring+".subnodes["+str(sameprojname)+"].delete()")
            else: 
                '''change the name of this new node'''
                if warn: print "WARNING: Node name `" + self.name + "` already exists;"
                self.name += "." +str( get_next_refnum() )  # add numbers to the name
                print "\tNode name changed to: ", self.name
            #end if(overwrite)
        else:
            #if DEBUG(): print "Node name is unique."
            pass
        #end if(self.name already exists aka. len(sameprojname) )
        
    
    def set_parent(self, parent_node):
        self.parent = parent_node
        parent_node.children.append(self)
        
    def delete(self):
        fimm.Exec(  "%s.delete()"%(self.nodestring)  )
        
    
    def Exec(self, string, vars=[]):
        '''Send raw command referencing this Node.
        For example:
            MyWaveGuide.Exec( "findorcreateview()" )   # to make FimmWave show the Waveguide window
        Note the initial period `.` is not needed.
        
        Internally, this can replace the older syntax of 
            fimm.Exec(  self.nodestring + '.findorcreateview()'  )
            fimm.Exec(  '%s.findorcreateview()'%(self.nodestring)  )
        with the simpler
            self.Exec(  'findorcreateview()'  )
        
        See `help(pyfimm.Exec)` for additional info.
        '''
        if self.built:
            out = fimm.Exec( self.nodestring + "." + string,   vars)
        else:
            raise UserWarning(  "Node is not built yet, can't reference this Node yet!  Please run `MyNode.Build()` first."  ) 
        if isinstance(out, list): out = strip_array(out)
        if isinstance(out, str):  out = strip_text(out)
        return out
#end class Node

            
            
class Project(Node):
    """Return a new Fimmwave Project.
    Project inherits from the Node class. 
    DEPRECATED: Arguments are passed to the Node class constructor - type help('pyFIMM.Node') for available arguments.
    The Project node is only built in FimmWave when you call `ProjectObj.buildNode()`.
    
    Please type `dir(ProjectObj)` or `help(ProjectObj)` to see all the attributes and methods available.
    
    
    Parameters
    ----------
    name : string
        Set the fimmwave name for this node.
    
    buildNode : { True | False }, optional
        build the project node right away?  Requires than a name is passed.
    
    overwrite : { True | False }, optional
        Only valid if `buildNode=True`. If True, will delete a project already open in FimmWave with the same name if it's the last project in the FimmWave list, otherwise will rename the offending Project (retaining desired name of this new Project).  If False, and a similarly-named Project exists in FimmWave, will modify the supplied project name. 
        The modified name is created by adding a random number to the end, such as "NewNodeName.123456", and can be found in the variable: `ProjectObj.name`.
    
    
    Attributes
    ----------
    
    Once ProjectObj.buildNode() has been called, the following attributes are available (they are set to `None` beforehand):
    
    name : string, name of the FimMWave Node
    
    num : int, number of this node in FimmWave
    
    nodestring : string, to access this node in FimmWave.  Eg. `app.subnodes[5]`, omitting trailing period `.`.
    
    savepath : string, the path to file for the project.
    
    origin : { 'pyfimm' | 'fimmwave' }
        Indicates whether this Device was built using pyFIMM, or was constructed in FimmWave & imported via `import_device()`.
    
    """
    
    def __init__(self, name=None, buildNode=False, overwrite=False, warn=True , *args, **kwargs):
        
        #build = kwargs.pop('buildNode', False)  # to buildNode or not to buildNode?
        #overwrite = kwargs.pop('overwrite', False)  # to overwrite existing project of same name
        
        super(Project, self).__init__(name)   # call Node() constructor, passing extra args
        ## Node('NameOfNode', NodeNumber, ParentNodeObject, Children)
        
        self.built = False
        self.num = self.nodestring = self.savepath = None
        if name: self.name = name
        
        #kwargs.pop('overwrite', False)  # remove kwarg's which were popped by Node()
        #kwargs.pop('warn', False)
        
        if buildNode: self.buildNode(overwrite=overwrite, warn=warn  )    # Hopefully Node `pops` out any kwargs it uses.
        
        if kwargs:
            '''If there are unused key-word arguments'''
            ErrStr = "WARNING: Project(): Unrecognized keywords provided: {"
            for k in kwargs.iterkeys():
                ErrStr += "'" + k + "', "
            ErrStr += "}.    Continuing..."
            print ErrStr
    
    def buildNode(self, name=None, overwrite=False, warn=True):
        '''Build the Fimmwave node of this Project.
        
        Parameters
        ----------
        name : string, optional
            Provide a name for this waveguide node.
            If `name` is not provided as an argument here, it should be pset via `MyProj.name = "NewName"` before calling `buildNode()`.
        
        overwrite : { True | False }, optional
            If True, will delete a project already open in FimmWave with the same name if it's the last project in the FimmWave list, otherwise will rename the offending Project (retaining desired name of this new Project).  If False, and a similarly-named Project exists in FimmWave, will modify the supplied project name. 
        The modified name is created by adding a random number to the end, such as "NewNodeName.123456", and can be found in the variable: `ProjectObj.name`.
        '''
        
        if DEBUG(): print "Project.buildNode():"
        if name: self.name = name
        self.type = 'project'   # unused!
        
        
        """ Deprecated - using check_node_name() instead.
        ## Check if top-level (project) node name conflicts with one already in use:
        #AppSubnodes = fimm.Exec("app.subnodes")        # The pdPythonLib didn't properly handle the case where there is only one list entry to return.  Although we could now use this function, instead we manually get each subnode's name:
        N_nodes = int(  fimm.Exec("app.numsubnodes()")  )
        SNnames = []    #subnode names
        for i in range(N_nodes):
            SNnames.append(  fimm.Exec(r"app.subnodes["+str(i+1)+"].nodename()").strip()[:-2]  )   
            # trim whitespace via string's strip(), strip the two EOL chars '\n\x00' from end via indexing [:-2]
        
        # check if node name is in the node list:
        sameprojidx = np.where( np.array(SNnames) == np.array([self.name]) )[0]
        if DEBUG(): print "Node '%s'.buildNode(): [sameprojname] = " % self.name, sameprojidx, "\nSNnames= ", SNnames
        
        if len( sameprojidx  ) > 0:
            '''if identically-named node was found'''
            if overwrite:
                '''delete the offending identically-named node'''
                print self.name + ".buildNode(): Overwriting existing Node #" + str(sameprojidx) + ", `" + SNnames[sameprojidx] + "`."
                sameprojidx = sameprojidx[0]+1
                fimm.Exec("app.subnodes["+str(sameprojidx)+"].delete()")
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
        """
        
        nodestring = "app"     # the top-level
        self.name, samenodenum = check_node_name( self.name, nodestring=nodestring, overwrite=overwrite, warn=warn )  # get modified nodename & nodenum of same-named Proj, delete/rename existing node if needed.
        
        
        '''Create the new node:     '''
        N_nodes = fimm.Exec("app.numsubnodes()")
        node_num = int(N_nodes)+1
        fimm.Exec("app.addsubnode(fimmwave_prj,"+str(self.name)+")")
        self.num = node_num
        self.nodestring = "app.subnodes[%i]" % self.num
        self.savepath = None
        self.built = True
    #end buildNode()
    
    
    def save_to_file(self, path=None, overwrite=False):
        '''savetofile(path): 
        Save the Project to a file.  Path is subsequently stored in `Project.savepath`. 
        
        Parameters
        ----------
        path : string, optional
            Relative (or absolute?) path to file.  ".prj" will be appended if it's not already present.
            If not provided, will assume the Project has been saved before, and will save to the same path (you should set `overwrite=True` in this case).
            
        overwrite : { True | False }, optional
            Overwrite existing file?  False by default.  Will error with "FileExistsError" if this is False & file already exists.
        '''
        
        if path == None:
            if self.savepath:
                path = self.savepath
            else:
                ErrStr = self.name + '.savetofile(): path not provided, and project does not have `savepath` set (has never been saved before).  Please provide a path to save file.'
                raise ValueError(ErrStr)
        
        if not path.endswith('.prj'):    path = path + '.prj'    # append '.prj' if needed
        
        if os.path.exists(path) and overwrite: 
            print self.name + ".savetofile(): WARNING: File `" + os.path.abspath(path) + "` will be overwritten."
            fimm.Exec("app.subnodes[{"+str(self.num)+"}].savetofile(" + path + ")")
            self.savepath = os.path.abspath(path)
            print self.name + ".savetofile(): Project `" + self.name + "` saved to file at: ", os.path.abspath(self.savepath)
        elif os.path.exists(path) and not overwrite:
            raise IOError(self.name + ".savetofile(): File `" + os.path.abspath(path) + "` exists.  Use parameter `overwrite=True` to overwrite the file.")
        else:
            fimm.Exec(   "%s.savetofile"%(self.nodestring) + "(%s)"%(path)   )
            self.savepath = os.path.abspath(path)
            print self.name + ".savetofile(): Project `" + self.name + "` saved to file at: ", os.path.abspath(self.savepath)
        #end if(file exists/overwrite)
    #end savetofile()
    
    def set_variables_node(self, fimmpath):
        '''Set the Variables Node to use for all nodes in this Project.  pyFIMM only supports the use of a single Variables node, even though FimmWave allows you to have numerous variables.  Local variables (within a Waveguide or Device node) are not supported.
        
        Use MyProj.set_variable() / get_variable() to set/get variable values.
        
        Parameters
        ----------
        fimmpath : string, required
        The FimmProp path to the Variable node, within this project.  This takes the form of something like "My Variables" if the Variables node named "My Variables" is at the top-level of the FimmProp Project, or "NodeName/My Variables" is the Variables node is under another Node.
        '''
        self.variablesnode = Variables( self, fimmpath )
    
#end class(Project)


# Note!  Project.import_device() is added in the file __Device.py, to avoid cyclic imports!


class Variables(Node):
    '''Variables( project, fimmpath )
    A class to reference a FimmProp Variables node.
    Used as a child to a Project object.
    
    The Variable's parent Project should have been created in pyFIMM beforehand.  To grab a Variable node from a file, use `newprj = pyFIMM.import_project()` to generate the Project from a file, and then call `newprj.set_variables_node()`.
    
    Parameters
    ----------
    project : pyFIMM Project object, required
        Specify the pyFIMM Project from which to acquire the Device.

    fimmpath : string, required
        The FimmProp path to the Variable node, within this project.  This takes the form of something like "My Variables" if the Variables node named "My Variables" is at the top-level of the FimmProp Project, or "NodeName/My Variables" is the Variables node is under another Node.
    
    Please use `dir(VarObj)` or `help(VarObj)` to see all the attributes and methods available.  A partial list is shown here:
    
    Attributes
    ----------
    VarObj.origin : { 'fimmwave' }
        This indicates that this Node was Not constructed by pyFIMM, and so has a slightly lacking set of attributes (detailed further in this section).  A python-constructed pyFIMM object has the value 'pyfimm'.
        
    Methods
    -------
    VarObj.get_all():  Return a Dictionary of all variables in the node.
    
    VarObj.add_var( 'VarName', value=VarValue ): Add a new variable and optionally set it's value.
    
    VarObj.get_var( 'VarName' ): Return the value of a specific variable.
    
    VarObj.set_var( 'VarName', Value ):  Set the value of a variable in the FimmWave node.
    
    '''
    def __init__(self, *args):
        '''If no args, return empty object
        if two args, assuem they are (projectobj, fimmpath)'''
        if len(args) == 0:
            '''no args provided'''
            self.parent=None
            self.origin=None
            self.name=None
            self.num=None
            self.nodestring=None
            self.built=None
            
        elif len(args) == 2:
            '''2 args: ProjectObj, fimmpath
            This is the standard usage'''
            project = args[0]
            if not isinstance(project, Project): raise ValueError("1st argument should be a pyFIMM Project object!")
            fimmpath = str(  args[1]  )
            self.parent=project
            self.origin = 'fimmwave'
            self.name = fimmpath.split('/')[-1]      # get the last part of the path
            self.num = None
        
            varname = "Vars_%i" %(  get_next_refnum()  )  # generate dev reference name
            # create fimmwave reference to the Device:
            fpStr = "Ref& %s = "%(varname) + project.nodestring + '.findnode("%s")'%(fimmpath)
            if DEBUG(): print fpStr
            ret = fimm.Exec( fpStr )
            ret = strip_txt( ret )
            if DEBUG(): print "\tReturned:\n%s"%(ret)
            self.nodestring = varname    # use this to reference the node in Fimmwave

            ret = strip_txt(  fimm.Exec( '%s.objtype'%(self.nodestring) )  )
            if ret != 'pdVariablesNode':
                ErrStr = "The referenced node `%s` is not a FimmProp Variables node or couldn't be found!\n\t"%(fimmpath) + "FimmWave returned object type of:\n\t`%s`."%(ret)
                raise ValueError(ErrStr)
            
            self.built=True
        else:
            ErrStr = "Invalid number of arguments to Variables.__init__().  Got:\n\t%s"%(args)
            raise ValueError(  ErrStr  )
        #end if( number of args )
    #end Variables.init()
    
    def add_var(self, varname, value=None):
        '''Add a variable to the Variables Node.
        
        varname : str, required
            The name for this variable.
        
        value : will be converted to string, optional
            If provided, will subsequently set the variable value with `VarObj.set_var( )`.
        '''
        self.Exec( 'addvariable("%s")'%(varname)  )
        self.set_var( varname, value )
    
    def set_var(self, varname, value):
        '''Set the value of a fimmwave variable.
         varname : str, required
            The name for this variable.
        
        value : str or numeric, required
            Set the variable value.
            '''
        self.Exec(  'setvariable("%s","%s")'%(varname, value)  )
    
    def get_var(self, varname):
        '''Return the value of a single variable as evaluated by FimmWave.  
        If the variable is a formula, fimmwave will return the final value resulting from evaluating the formula. All results are converted to a numeric type, unless the variable contains a statement that FimmWave is unable to evaluate, in which case the statement is returned as a string.'''
        fpStr = self.Exec(  'getvariable("%s")'%(varname)  )   
        return eval_string( fpStr )
        
    def get_all(self):
        '''Return all available variables as a dictionary.  This will interrogate FimmWave to get all currently defined variables in the node.  
    A dictionary will be returned, with all numeric variables being converted to numbers, while references/formulae will be returned as strings.'''
        fpStr = self.Exec( 'writeblock()' )
        fpStr = [  x.strip() for x in   fpStr.splitlines()[1:-1]  ]
        if DEBUG(): print "Variables in '%s':\n\t%s"%(self.name, fpStr )
        
        out={}  # dictionary to output
        for line in fpStr:
            key = line.split(' = ')[0]
            val = line.split(' = ')[-1]
            out[key] = eval_string( val )
        
        return out
        
"""
## FimmWave code for Variables Nodes:
app.subnodes[4].addsubnode(pdVariablesNode,"Variables 1")
app.subnodes[4].subnodes[2].findorcreateview()
app.subnodes[4].subnodes[2].addvariable(a)
app.subnodes[4].subnodes[2].setvariable(a,"999")
app.subnodes[4].subnodes[2].getvariable("a")
    999
"""

    
#end class(Variables)



def import_project(filepath, name=None, overwrite=False, warn=True):
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
    # Create Project object.  Set the "savepath", 'num', 'name' attributes of the project.
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
        # Get name from the Project file we're opening
        prjf = open(filepath)
        prjtxt = prjf.read()    # load the entire file
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
    
    
    nodestring = "app"
    newprjname, samenodenum = check_node_name( prjname, nodestring=nodestring, overwrite=overwrite, warn=warn )  # get modified nodename & nodenum of same-named Proj, delete/rename existing node if needed.
    
    """
    if newprjname != prjname:
        '''Project with same name exists'''
        if overwrite:
            '''delete the offending identically-named node'''
            if warn: print "Overwriting existing Node #" + str(samenodenum) + ", '%s'." % prjname
            fimm.Exec(nodestring+".subnodes["+str(samenodenum)+"].delete()")
            newprjname = prjname    #use orig name
    #end if(project already exists)
    """
    
    
    '''Create the new node:     '''
    N_nodes = fimm.Exec("app.numsubnodes()")
    node_num = int(N_nodes)+1
    if DEBUG(): print "import_project(): app.subnodes ", N_nodes, ", node_num = ", node_num
    '''app.openproject: FUNCTION - ( filename[, nodename] ): open the specified project with the specified node name'''
    fimm.Exec("app.openproject(" + str(filepath) + ', "'+ newprjname + '" )'  )   # open the .prj file
    
    prj = Project(prjname)     # new Project obj
    prj.type = 'project'  # unused!
    prj.num = node_num
    prj.built = True
    prj.savepath = savepath
    prj.nodestring = "app.subnodes[%i]"%(prj.num)
    prj.name = strip_txt(  fimm.Exec(  "%s.nodename() "%(prj.nodestring)  )  )
    prj.origin = 'fimmwave'
    
    
    
    return prj
#end ImportProject()

# Alias to the same function:
import_Project = import_project

'''
## FimmWave commands for opening a project file:
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
    Section class applies a Length to a Waveguide object.  This object is only used when creating a new pyFIMM Device object, and is usually invisible to the end-user.
    This is so that a Device can reference the same WG multiple times, but with a different length each time.
    Usually not created manually, but instead returned when user passes a length to a WG (Waveguide or Circ) object.
    
    Parameters
    ----------
    WGobject : Waveguide, Circ or Device object
        Waveguide, Circ or Device object, previously built.
        
    length : float
        length of this WG, when inserted into Device.  Required for Waveguide or Circ objects, not required for Device objects.
        
    To Do:
    ------
    Ability to pass modesolver parameters for this waveguide.
    
    
    Examples
    --------
    Typically created by calling a WG (Waveguide or Circ) object while creating a Device:
        >>> Device1 = Device( WG1(10.5) + WG2(2.5) + WG3(10.5)  )
    
    '''
    
    def __init__(self, *args):
        if len(args) == 0:
            '''return empty object'''
            self.WG = None
            self.length = None
        if len(args) == 1:
            '''Only Waveguide/Device passed.  Device.__call__ uses this case'''
            #if DEBUG(): print "Section: 1 args=\n", args
            self.WG = args[0]
            try:
                self.length = self.WG.get_length()
            except AttributeError:
                ErrStr = "Section.__init__(): The specified Waveguide/Device has no method `get_length()`.  Please pass a Waveguide, Circ or Device (or similar, eg. Lens) object that has a length.\n\tGot args = " + str(args)
                raise AttributeError(ErrStr)
        elif len(args) == 2:
            '''WG & length passed.  Waveguide/Circ.__call__ use this case.'''
            #if DEBUG(): print "-- Section: 2 args=\n", args
            self.WG = args[0]
            self.length = args[1]
        else:
            raise ValueError( "Invalid number of arguments to Section().  args=" + str(args) )
        
        
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



