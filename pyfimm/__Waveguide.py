'''Waveguide class, part of pyFIMM.'''

#from pylab import *     # must kill these global namespace imports!
#from numpy import *


from __globals import *         # import global vars & FimmWave connection object


from __pyfimm import *       # import the main module (should already be imported), includes many 'rect' classes/funcs
from __Mode import Mode            # import Mode class
from numpy import inf           # infinity, for hcurv/bend_radius


class Waveguide(Node):
    """pyFimm Waveguide object, a collection of concatenated Slices.  
    
    Waveguide is an 'RWG' cartesian-coordinate waveguide (eg. rectangular channel, ridge etc.).
    
    Waveguide is a 2-D index profile if called with just one argument (a summation of Slices).
    When a Length is supplied, this becomes a 3D structure.
    This inherits from the pyFIMM Node object.
    
    
    Parameters
    ----------
    layers : list
        List containing the Slice objects used to generate this Waveguide.
    
    thickness : float, optional
        Apply a 3D length to this waveguide, in the direction of propagation. 
    
    name : string, optional
        If building the node at creation, supply a name for this node.
    
    parentNode : string, optional
        If building the node at creation, provide the parent (Project/Device) Node object for this waveguide.
       
        
    Attributes
    ----------
    type : {'rect_waveguide'}
        Currently = 'rect_waveguide'.  May be deprecate as it is unused.
    
    length : float
        Apply a 3D length to this waveguide, in the direction of propagation. 
    
    slices : list
        List containing all the Slices the Waveguide is constructed with.
    
    etched_slices : list
        Contains Slices with any specified etch depths applied.
        etched_slices[i] = Slice(slc.layers,slc.width,slc.etch)
    
    bend_radius : float
        Bend Radius of the waveguide.  The default value of `inf` indicates a straight waveguide.
        Defined from the center of the waveguide cross-section to the axis of the bend.
        Positive value means WG bends to the LEFT (so Right-Hand boundaries will see the radiatiing bend modes, if any).  Negative value bends the opposite way.
    
    built : { True | False }
        Has this node been built in FimmWave yet?
    
    nodestring : string
        The fimmwave string pointing to this waveguide's node.  eg. "app.subnodes[1].subnodes[3]"
        Omits the trailing period.

    
    
    Methods
    -------
    
    This is a partial list - see `dir(pf.Waveguide)` to see all methods.
    Please see help on a specific function via `help(pf.Waveguide)` for detailed up-to-date info on accepted arguments etc.
    
    mode(modenum)
        modenum: int
            Returns the specified Mode object.  Mode(0) is usually the fundamental mode, depending on the solver options.
            Subsequent Mode functions can be called, such as
                >>> ThisWaveguide.mode(0).plot('Ez')
    
    get_width()
        Return total width of this Waveguide, by adding up width of each contained Slice.
    
    get_slice_widths()
        Return widths of each Slice in this Waveguide, as list.
        
    buildNode( [name=, parentNode=] )
        Build the node of this Ridge/Rectangular (RWG) waveguide in FimmWave. Sends all the FimmWave commands for this waveguide node, including modesolver parameters.
    
    get_buildNode_str(nodestr [, obj=None, target=None])
        Return the fimmwave commands needed to build this waveguide node.  This command does not create the new waveguide node first (ie. it does not run `app.subnodes[1].addsubnode(rwguideNode, WGname)`  )
        So you must create the appropriate type of waveguide node first, and then issue the commands returned by this func.
        The massive multi-line string includes all the modesolver settings needed to calculate the waveguide afterwards.
                
        Parameters
        ----------
        nodestr : string
            Supply the string pointing to the new WG node to build under, for example `app.subnodes[1].subnodes[1]`
            After a WG has been built, this parameter is available via the variable  `WG_Object.nodestring`
        
        Returns
        -------
        wgString : fimmwave command string
    
    
    set_autorun()
        Set the fimmwave "autorun" flagm which allows FimmProp to calc the modes when needed.
        
    unset_autorun():
        Unset the fimmwave "autorun" flag.
    
    set_material_database( PathString )
        Not recommended - it is safer to use a global material file, and have that file `include` other material files.  FimmProp Devices only support a single global materials file.
        PathString : string
            Path to a FimmWave material database (*.mat) for this waveguide node, if different from the globally set one (see `set_material_database()` )
    
    get_material_database()
        Returns path to FimmWave material database (*.mat) for this waveguide node, if set.
    
    unset_material_database()
        Unsets a custom material database for this waveguide node, such that the globally set one (see `set_material_database()` ) will be used instead.
    
    set_joint_type(type)
        Set the type of FimmProp joint to use after this waveguide has been inserted into a Device.
    
    get_joint_type(type)
        Get the type of FimmProp joint to use after this waveguide has been inserted into a Device. 
    
    set_wavelength( wl )
        Set the wavelength of this guide.
    
    get_wavelength()
        Return the wavelength of this guide.
    
    Examples
    --------
    Create the Waveguide like so:
    >>> wg = Waveguide(  slice1(1.5) + slice2(0.50) + slice3(1.5)  )
    
    or
    MySlices = slice1(1.5) + slice2(0.50) + slice3(1.5)
    >>> wg = Waveguide( MySlices, WG_Length )    # WG_Length in microns
    
    or, *after* creating the Waveguide, apply a length by calling with one arg:
    >>> wg( WG_Length ) 
    
    Then build the FimmWave node & calculate the modes:
    >>> wg.set_parent('wg_prj')
    >>> wg.name = 'Fimmwave RWG'
    >>> wg.buildNode()          # Sends all the FimmWave commands to generate the waveguide.
    >>> wg.calc()
    
    or build the node in one line:
    >>> wg.buildNode( name='Fmmwave RWG', parentNode=wg_prj )
    >>> wg.calc()       # calculate modes
    
    """
    
    def __init__(self,*args):
        if len(args) >= 1:
            self.type = 'rect_waveguide'    # not currently used
            self.autorun = True
            self.name = None
            self.built=False
            self.length = 0.0
            self.__wavelength = get_wavelength()    # get global wavelength
            self.modes = []
            self.slices = args[0]
            self.etched_slices = []
            self.bend_radius = inf      # Default to inf -straight.  Defined from center of WG slice.
            self.__materialdb = None
            
            # apply Etch Depths for each Slice
            for slc in args[0]:
                etchDepth = slc.etch
                if etchDepth > slc.thickness():
                    etchDepth = slc.thickness()
                elif etchDepth < 0:
                    etchDepth = 0

                if etchDepth != 0:
                    etched_layer_array = []
                    for nn in range(0,len(slc)):
                        if slc.thickness() - sum(slc.layer_thicknesses()[0:nn+1]) > etchDepth:
                            etched_layer_array += [slc.layers[nn]]
                        else:
                            top_layer = Layer(slc.layers[len(slc)-1].material,etchDepth,False)
                            etched_layer = Layer(slc.layers[nn].material,sum(slc.layer_thicknesses()[nn:len(slc)])-etchDepth,slc.layers[nn].cfseg)
                            etched_layer_array += [etched_layer]
                            etched_layer_array += [top_layer]
                            self.etched_slices.append(Slice(etched_layer_array,slc.width,slc.etch))
                            break
                elif etchDepth == 0:
                    if slc.layer_thicknesses()[len(slc)-1] == 0.0:
                        del slc.layers[len(slc)-1]
                    self.etched_slices.append(Slice(slc.layers,slc.width,slc.etch))
                
        if len(args) ==2:
            self.length = args[1]   # apply passed length
    #end init()

    def __str__(self):
        '''What to display if the Waveguide is `print`ed.'''
        string = ""
        if self.name: string += "Name: '"+self.name+"'\n"
        for n,slc in enumerate(self.etched_slices):
            if n ==0:
                string += 5*'-' + ' Leftmost Slice: ' + 5*'-' + '\nwidth = %7.4f \n' % slc.width
            elif n == (len(self.etched_slices)-1):
                string += 5*'-' + ' Rightmost Slice: ' + 5*'-' + '\nwidth = %7.4f \n' % slc.width
            else:
                string += 5*'-' + ' Middle Slice %i: ' % n + 5*'-' + '\nwidth = %7.4f \n' % slc.width
            
            for i,lyr in enumerate(slc.layers):
                if i == 0:
                    string += 3*'*' + ' Bottom Layer: ' + 3*'*' + '\n%s' % lyr + '\n'
                elif i == (len(slc.layers)-1):
                    string += 3*'*' + ' Top Layer: ' + 3*'*' + '\n%s' % lyr + '\n'
                else:
                    string += 3*'*' + ' Middle Layer %i: ' % i + 3*'*' + '\n%s' % lyr + '\n'
        return string

    def __len__(self):
        return len(self.slices)

    
    def __call__(self,length):
        '''Calling a WG object with one argument creates a Section of passed length, and returns a list containing this new Section.
            Usually passed directly to Device as so:
            >>> NewDevice = pyfimm.Device(  WG1(10.5) + WG2(1.25) + WG3(10.5)  )
            
            Parameters
            ----------
            length : float
                Pass a length (microns). This will be applied to the returned Section Object, which will also contain a reference to this waveguide object.
        '''

        # Instantiate a Section obj with 2 args
        out = [   Section(  self, length  )   ]
        return out

    def __add__(self,other):
        '''Additions will tack on each waveguide, presumably in the propagation direction, for contatenating multiple waveguides.  Returns a list of all Waveguide objects.'''
        '''CHECK THIS "presumably" statement!!!'''
        return [self,other]

    def get_width(self):
        '''Return total width of this Waveguide, by adding up width of each contained Slice.'''
        wdth = 0.0
        for slc in self.slices:
            wdth += slc.width
        return wdth
    
    def width(self):
        '''Backwards compatibility only.  Should Instead get_width().'''
        print "Deprecation Warning:  width():  Use get_width() instead."
        return get_width()

    def get_slice_widths(self):
        '''Return widths of each Slice in this Waveguide.'''
        slc_wdths = []
        for slc in self.slices:
            slc_wdths.append(slc.width)
        return slc_wdths
    
    def slice_widths(self):
        '''Backwards compatibility only.  Should Instead get_slice_widths().'''
        print "Deprecation Warning:  slice_widths():  Use get_slice_widths() instead."
        return get_slice_widths(self)
    
    

    
    def mode(self,modeN):
        '''Waveguide.mode(int): Return the specified pyFimm Mode object for this waveguide.'''
        return Mode(self, modeN,"app.subnodes[{"+str(self.parent.num)+"}].subnodes[{"+str(self.num)+"}].evlist.")


    def calc(self):
        '''Calculate/Solve for the modes of this Waveguide.  Build the node if needed.'''
        if not self.built: self.buildNode()
        fimm.Exec("app.subnodes[{"+str(self.parent.num)+"}].subnodes[{"+str(self.num)+"}].evlist.update")

    def set_autorun(self):
        '''FimmProp Device will automatically calculate modes as needed.'''
        self.autorun = True
        
    def unset_autorun(self):
        '''FimmProp Device will Not automatically calculate modes as needed.'''
        self.autorun = False

    def set_material_database(self, path):
        '''Set a material database for this waveguide node (overrides the global setting of `pyfimm.set_material_database(path)` ).'''
        self.__materialdb = str(path)
    
    def get_material_database(self):
        '''Returns a custom material database for this waveguide node.'''
        return self.__materialdb
    
    def unset_material_database(self):
        '''Clears the custom material database for this waveguide node.  The global setting `pyfimm.set_material_database(path)` will be used instead.'''
        self.__materialdb = None
    
    def set_joint_type(self, jtype, jointoptions=None):
        '''Set the joint type after (on right side of) this waveguide, if used in a Device.
        type : { 'complete' | 'special complete' | 'normal fresnel' | 'oblique fresnel' }, case-insensitive
        synonyms for 'complete' are { 0 }, and is also the default if unset.
        synonyms for 'special complete' are { 3 | 'special' }
        synonyms for 'normal fresnel' are { 1 | 'fresnel' }
        synonyms for 'oblique fresnel' are { 2 }
        
        jointoptions : Dictionary{} of options.  Allows for the Device.buildnode() to set various joint options, such as angle etc.  Please see help(Device) for what the possible options are.
        '''
        if isinstance(jtype, str): jtype=jtype.lower()   # make lower case
        if jtype == 0 or jtype == 'complete':
            self.__jointtype = 0
        if jtype == 1 or jtype == 'normal fresnel' or jtype == 'fresnel':
            self.__jointtype = 1
        if jtype == 2 or jtype == 'oblique fresnel':
            self.__jointtype = 2
        if jtype == 3 or jtype == 'special complete' or jtype == 'special':
            self.__jointtype = 3
        
        if isinstance(jointoptions, dict):
            self.__jointoptions=jointoptions
        elif jointoptions!=None:
            ErrStr = "set_joint_type(): `jointoptions` should be a dictionary.  See help(Device) for the available options."
            raise ValueError(ErrStr)
    #end set_joint_type()
    
    def get_joint_type(self, *args):
        '''get_joint_type( [asnumeric] )
        Get the joint type that will be placed between this waveguide and the next, when inserted into a Device.  
            asnumeric : { True | False }, optional
                A True value will cause the output to be numeric, rather than string.  See help(set_joint_type) for the numerical/string correlations.  False by default.
                (FYI, `asnumeric=True` is used in Device.buildNode()  )
        '''
        try:
            self.__jointtype    # see if variable exists
        except AttributeError:
            # if the variable doesn't exist yet:
            if DEBUG(): print "unset " + self.name + ".__jointtype --> 'complete'   "
            self.__jointtype = 0
        
        if len(args) == 0:      asnumeric = False   # output as string by default
        if len(args) == 1:      asnumeric = args[0]
        if len(args) > 1:    raise ValueError("get_joint_type(): Too many arguments provided.")
        
        if asnumeric:
            out= self.__jointtype
        else:
            if self.__jointtype == 0:
                out= 'complete'
            elif self.__jointtype == 1:
                out= 'normal fresnel'
            elif self.__jointtype == 2:
                out= 'oblique fresnel'
            elif self.__jointtype == 3:
                out= 'special complete'
        #if DEBUG(): print "get_joint_type(): ", out
        return out
    #end get_joint_type()
    
    
    def set_wavelength(self, wl):
        '''Set the wavelength for the waveguide.  The object use this wavelength in their MOLAB options.
        Note that, after building, the object's wavelength (`WGobj.get_wavelength()` ) can be different from the global pyFIMM wavelength (`pyFIMM.get_wavelength`).
        The global setting (`pyFIMM.set_wavelength()`) is acquired when the object is first created.
        
        Parameters
        ----------
        wl : float
            The wavelength in micrometers.
        '''
        
        if self.built:
            self.__wavelength = float(wl)
            fimm.Exec(  self.nodestring + ".evlist.svp.lambda = " + str(self.__wavelength) + "   \n"  )
        else:
            self.__wavelength = float(wl)
    
    
    def get_wavelength(self):
        '''Return the wavelength (float) for this specific Device (may be different from the global pyFIMM wavelength in `pyFIMM.get_wavelength()` after the guide is built).'''
        return self.__wavelength
    
    
    
    
    
    
    ####################################################
    ####    Rectangular Waveguide Node Construction ####
    ####################################################
    
    def buildNode(self, name=None, parent=None, overwrite=False, warn=True):
        '''Build the Fimmwave node of this Ridge/Rectangular (RWG) waveguide.
        
        Parameters
        ----------
        name : string, optional
            Provide a name for this waveguide node.

        parent : Node object, optional
            provide the parent (Project/Device) Node object for this waveguide.
        
        overwrite : { True | False }, optional
            Overwrite existing node of same name?  Defaults to False, which will rename the node if it has the same name as an existing node.
        
        warn : {True | False}, optional
            Print notification if overwriting a node?  True by default.
        
        '''
        if name: self.name = name
        if parent: self.parent = parent
        if DEBUG(): print "Waveguide.buildNode(): self.parent.num=", self.parent.num
        
        nodestring="app.subnodes["+str(self.parent.num)+"]"
        self._checkNodeName(nodestring, overwrite=overwrite, warn=warn)     # will alter the node name if needed
        
        N_nodes = fimm.Exec("app.subnodes["+str(self.parent.num)+"].numsubnodes")
        node_num = int(N_nodes+1)
        self.num = node_num    
        
        # make RWG node:
        #wgString = "app.subnodes["+str(self.parent.num)+"].addsubnode(rwguideNode,"+str(self.name)+")"+"\n"
        wgString = self.parent.nodestring + ".addsubnode(rwguideNode,"+str(self.name)+")"+"\n"
        
        self.nodestring = self.parent.nodestring + ".subnodes["+str(self.num)+"]"
        
        fimm.Exec(  wgString + self.get_buildNode_str(self.nodestring, warn=warn)  ) 
        #self.BuildRectNode()  
          
        self.built=True
    #end buildNode()
    
    
    def get_buildNode_str(self, nodestr, obj=None, target=None, warn=True):
        '''Return the node construction string for either a standalone waveguide or device.
        This is for a Rectangular/Planar (RWG) waveguide.
        The new Waveguide subnode should be created BEFORE calling this function, so that you can pass the correct node string.
    
        Parameters
        ----------
        nodestr : str
            The entire base-string to address the necessary node.  For example:
                >>> nodestr = "app.subnodes[1].subnodes[2]"
            the subnode referenced should be the NEW subnode to be created (ie. one higher than previously in existence).  In normal operation, the new subnode has already been created by WG.buildnode().
        
        warn : bool
            Print warnings about default values etc.?
        
        obj : Circ object, optional
            Defaults to `self`.  Can pass another object instead, to get the buildNode string for that
        
        target : { 'wglens' | 'taper' }, optional
            Omits certain parameters from being set depending on target.  Used for building tapers.
        '''
        
        if not obj: obj=self
        
        # build RWG Node
        if DEBUG(): print "Waveguide: "+self.name+".__get_buildNode_str(): "
        
        
        # check for custom material DB in this WG node.
        if not self.__materialdb:
            '''Use global material DB if this WG doesn't have a custom one set.'''
            matDB = get_material_database()
        else:
            matDB = self.__materialdb
            #if DEBUG(): print "Using custom matDB: `%s`"%matDB
        
        
        
        wgString=""     # the string to return
        
        
        if matDB: 
            #if DEBUG(): print "setting MaterBase file to: '%s'"%matDB
            wgString += nodestr + ".setmaterbase(" + matDB + ")  \n"
        
        
        sliceN = 1
        for slc in obj.slices:
            wgString += nodestr + ".insertslice({"+str(sliceN)+"})"+"\n"
            wgString += nodestr + ".slices[{"+str(sliceN)+"}].width = "+str(slc.width)+"\n"
            wgString += nodestr + ".slices[{"+str(sliceN)+"}].etch = "+str(slc.etch)+"\n"
            wgString += (len(slc.layers)-1)*(nodestr + ".slices[{"+str(sliceN)+"}].insertlayer(1)"+"\n")
            layerN = 1
            for lyr in slc.layers:
                wgString += nodestr + ".slices[{"+str(sliceN)+"}].layers[{"+str(layerN)+"}].size = "+str(lyr.thickness)+"\n"
                
                if lyr.material.type == 'rix':
                    wgString +=  nodestr + ".slices[{"+str(sliceN)+"}].layers[{"+str(layerN)+"}].nr11 = "+str(lyr.n())+"\n"+ \
                        nodestr + ".slices[{"+str(sliceN)+"}].layers[{"+str(layerN)+"}].nr22 = "+str(lyr.n())+"\n"+ \
                        nodestr + ".slices[{"+str(sliceN)+"}].layers[{"+str(layerN)+"}].nr33 = "+str(lyr.n())+"\n"
                elif lyr.material.type == 'mat':
                    if DEBUG(): print "Layer %i: mx="%(layerN), lyr.material.mx, " // my=", lyr.material.my
                    wgString +=   nodestr + ".slices[{"+str(sliceN)+"}].layers[{"+str(layerN)+"}].setMAT(" + str(lyr.material.mat) + ") \n"
                    if lyr.material.mx:   wgString +=  nodestr + ".slices[{"+str(sliceN)+"}].layers[{"+str(layerN)+"}].mx = "+str(lyr.material.mx)+"\n"
                    if lyr.material.my:   wgString +=  nodestr + ".slices[{"+str(sliceN)+"}].layers[{"+str(layerN)+"}].my = "+str(lyr.material.my)+"\n"
                
                if lyr.cfseg:
                    wgString += nodestr + ".slices[{"+str(sliceN)+"}].layers[{"+str(layerN)+"}].cfseg = "+str(1)+"\n"
                
                
                layerN += 1
            sliceN += 1
        #end for(slices)

        # build boundary conditions - metal by default
        if get_left_boundary() is None:
            '''Default to Electric Wall/metal'''
            if warn: print self.name + ".buildNode(): Left_Boundary: Using electric wall boundary."
            wgString += nodestr + ".lhsbc.type = 1"+"\n"
        else:
            if get_left_boundary().lower() == 'metal' or get_left_boundary().lower() == 'electric wall':
                wgString += nodestr + ".lhsbc.type = 1"+"\n"
            elif get_left_boundary().lower() == 'magnetic wall':
                wgString += nodestr + ".lhsbc.type = 2"+"\n"
            elif get_left_boundary().lower() == 'periodic':
                wgString += nodestr + ".lhsbc.type = 3"+"\n"
            elif get_left_boundary().lower() == 'transparent':
                wgString += nodestr + ".lhsbc.type = 4"+"\n"
            elif get_left_boundary().lower() == 'impedance':
                wgString += nodestr + ".lhsbc.type = 5"+"\n"
            else:
                print self.name + ".buildNode(): Invalid input to set_left_boundary()"
                
        if get_right_boundary() is None:
            '''Default to Electric Wall/metal'''
            wgString += nodestr + ".rhsbc.type = 1"+"\n"
        else:
            if get_right_boundary().lower() == 'metal' or get_right_boundary().lower() == 'electric wall':
                wgString += nodestr + ".rhsbc.type = 1"+"\n"
            elif get_right_boundary().lower() == 'magnetic wall':
                wgString += nodestr + ".rhsbc.type = 2"+"\n"
            elif get_right_boundary().lower() == 'periodic':
                wgString += nodestr + ".rhsbc.type = 3"+"\n"
            elif get_right_boundary().lower() == 'transparent':
                wgString += nodestr + ".rhsbc.type = 4"+"\n"
            elif get_right_boundary().lower() == 'impedance':
                wgString += nodestr + ".rhsbc.type = 5"+"\n"
            else:
                print self.name + ".buildNode(): Invalid input to set_right_boundary()"

        if get_bottom_boundary() is None:
            '''Default to Electric Wall/metal'''
            wgString += nodestr + ".botbc.type = 1"+"\n"
        else:
            if get_bottom_boundary().lower() == 'metal' or get_bottom_boundary().lower() == 'electric wall':
                wgString += nodestr + ".botbc.type = 1"+"\n"
            elif get_bottom_boundary().lower() == 'magnetic wall':
                wgString += nodestr + ".botbc.type = 2"+"\n"
            elif get_bottom_boundary().lower() == 'periodic':
                wgString += nodestr + ".botbc.type = 3"+"\n"
            elif get_bottom_boundary().lower() == 'transparent':
                wgString += nodestr + ".botbc.type = 4"+"\n"
            elif get_bottom_boundary().lower() == 'impedance':
                wgString += nodestr + ".botbc.type = 5"+"\n"
            else:
                print self.name + ".buildNode(): Invalid input to set_bottom_boundary()"

        if get_top_boundary() is None:
            '''Default to Electric Wall/metal'''
            wgString += nodestr + ".topbc.type = 1"+"\n"
        else:
            if get_top_boundary().lower() == 'metal' or get_top_boundary().lower() == 'electric wall':
                wgString += nodestr + ".topbc.type = 1"+"\n"
            elif get_top_boundary().lower() == 'magnetic wall':
                wgString += nodestr + ".topbc.type = 2"+"\n"
            elif get_top_boundary().lower() == 'periodic':
                wgString += nodestr + ".topbc.type = 3"+"\n"
            elif get_top_boundary().lower() == 'transparent':
                wgString += nodestr + ".topbc.type = 4"+"\n"
            elif get_top_boundary().lower() == 'impedance':
                wgString += nodestr + ".topbc.type = 5"+"\n"
            else:
                print self.name + ".buildNode(): Invalid input to set_top_boundary()"

        if get_x_pml() is None:
            '''Default to 0.0'''
            wgString += nodestr + ".lhsbc.pmlpar = {0.0}"+"\n"+ \
                        nodestr + ".rhsbc.pmlpar = {0.0}"+"\n"
        else:
            wgString += nodestr + ".lhsbc.pmlpar = {"+str(get_x_pml())+"}"+"\n"+ \
                        nodestr + ".rhsbc.pmlpar = {"+str(get_x_pml())+"}"+"\n"

        if get_y_pml() is None:
            '''Default to 0.0'''
            wgString += nodestr + ".topbc.pmlpar = {0.0}"+"\n"+ \
                        nodestr + ".botbc.pmlpar = {0.0}"+"\n"
        else:
            wgString += nodestr + ".topbc.pmlpar = {"+str(get_y_pml())+"}"+"\n"+ \
                        nodestr + ".botbc.pmlpar = {"+str(get_y_pml())+"}"+"\n"

        
        
        wgString += self.get_solver_str(nodestr, obj=obj, target=target)
        
        
        #fimm.Exec(wgString)
        
        return wgString

    #end get_buildNodeStr()
    
    
    
    def get_solver_str(self, nodestr, obj=None, target=None):
        ''' Return only the Solver ('svp') and mode solver (MOLAB, 'mpl') params for creating this node.
        Used for building Tapers, when the WG is already built otherwise.'''
        if not obj: obj=self

        #if DEBUG(): print "Waveguide.get_solver_str()... "
        
        wgString = ""
        
        # set solver parameters
        if target == 'wglens' or target == 'taper':
            '''hcurv/bend_radius is set separately for Taper or WGLens, since they could have a different curvature from their base WG object.'''
            pass
        else:
            nodestr = nodestr + ".evlist"     #WG nodes set their solver params under this subheading
            if obj.bend_radius == 0:
                obj.bend_radius = inf
                if warn: print self.name + ".buildNode(): Warning: bend_radius changed from 0.0 --> inf (straight waveguide)"
                hcurv = 0
            elif obj.bend_radius == inf:
                hcurv = 0
            else:
                hcurv = 1.0/obj.bend_radius
            wgString += nodestr + ".svp.hcurv={"+str(hcurv)+"}"+"\n"
        #end if(WGlens/Taper)
        
        
        #autorun & speed:
        if self.autorun: 
            wgString += nodestr + ".mlp.autorun=1"+"\n"
        else:
            wgString += nodestr + ".mlp.autorun=0"+"\n"
        
        
        if get_solver_speed(): 
            wgString += nodestr + ".mlp.speed=1"+"\n"    #0=best, 1=fast
        else:
            wgString += nodestr + ".mlp.speed=0"+"\n"    #0=best, 1=fast


        if get_horizontal_symmetry() is None:
            wgString += nodestr + ".svp.hsymmetry=0"+"\n"
        else:
            if get_horizontal_symmetry() == 'none':
                wgString += nodestr + ".svp.hsymmetry=0"+"\n"
            elif get_horizontal_symmetry() == 'ExSymm':
                wgString += nodestr + ".svp.hsymmetry=1"+"\n"
            elif get_horizontal_symmetry() == 'EySymm':
                wgString += nodestr + ".svp.hsymmetry=2"+"\n"
            else:
                print self.name + ".buildNode(): Invalid horizontal_symmetry. Please use: none, ExSymm, or EySymm"

        if get_vertical_symmetry() is None:
            wgString += nodestr + ".svp.vsymmetry=0"+"\n"
        else:
            if get_vertical_symmetry() == 'none':
                wgString += nodestr + ".svp.vsymmetry=0"+"\n"
            elif get_vertical_symmetry() == 'ExSymm':
                wgString += nodestr + ".svp.vsymmetry=1"+"\n"
            elif get_vertical_symmetry() == 'EySymm':
                wgString += nodestr + ".svp.vsymmetry=2"+"\n"
            else:
                print self.name + ".buildNode(): Invalid vertical_symmetry. Please use: none, ExSymm, or EySymm"

        if get_N() is None:
            '''Default to 10'''
            wgString += nodestr + ".mlp.maxnmodes={10}"+"\n"
        else:
            wgString += nodestr + ".mlp.maxnmodes={"+str(get_N())+"}"+"\n"

        if get_NX() is None:
            '''Default to 60'''
            wgString += nodestr + ".mlp.nx={60}"+"\n"
            nx_svp = 60
        else:
            wgString += nodestr + ".mlp.nx={"+str(get_NX())+"}"+"\n"
            nx_svp = get_NX()

        if get_NY() is None:
            '''Default to 60'''
            wgString += nodestr + ".mlp.ny={60}"+"\n"
            ny_svp = 60
        else:
            wgString += nodestr + ".mlp.ny={"+str(get_NY())+"}"+"\n"
            ny_svp = get_NY()

        if get_min_TE_frac() is None:
            '''Default to 0.0'''
            wgString += nodestr + ".mlp.mintefrac={0}"+"\n"
        else:
            wgString += nodestr + ".mlp.mintefrac={"+str(get_min_TE_frac())+"}"+"\n"
        
        if get_max_TE_frac() is None:
            '''Default to 100.0'''
            wgString += nodestr + ".mlp.maxtefrac={100}"+"\n"
        else:
            wgString += nodestr + ".mlp.maxtefrac={"+str(get_max_TE_frac())+"}"+"\n"
        
        if get_min_EV() is None:
            '''Default to -1e50'''
            wgString += nodestr + ".mlp.evend={-1e+050}"+"\n"
        else:
            wgStrint += nodestr + ".mlp.evend={"+str(get_min_EV())+"}"+"\n"
        
        if get_max_EV() is None:
            '''Default to +1e50'''
            wgString += nodestr + ".mlp.evstart={1e+050}"+"\n"
        else:
            wgStrint += nodestr + ".mlp.evend={"+str(get_max_EV())+"}"+"\n"

        if get_RIX_tol() is None:
            rix_svp = 0.010000
        else:
            rix_svp = get_RIX_tol()

        if get_N_1d() is None:
            n1d_svp = 30
        else:
            n1d_svp = get_N_1d()

        if get_mmatch() is None:
            mmatch_svp = 0
        else:
            mmatch_svp = get_mmatch()

        if get_mode_solver() is None:
            print  self.name + '.buildNode(): Using default mode solver: "vectorial FDM real"  '
            wgString += nodestr + ".svp.solvid=71"+"\n"
            solverString = nodestr + ".svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
        else:
            if get_mode_solver().lower() == 'vectorial FDM real'.lower():
                wgString += nodestr + ".svp.solvid=71"+"\n"
                solverString = nodestr + ".svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif get_mode_solver().lower() == 'semivecTE FDM real'.lower():
                wgString += nodestr + ".svp.solvid=23"+"\n"
                solverString = nodestr + ".svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif get_mode_solver().lower() == 'semivecTM FDM real'.lower():
                wgString += nodestr + ".svp.solvid=39"+"\n"
                solverString = nodestr + ".svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif get_mode_solver().lower() == 'vectorial FDM complex'.lower():
                wgString += nodestr + ".svp.solvid=79"+"\n"
                solverString = nodestr + ".svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif get_mode_solver().lower() == 'semivecTE FDM complex'.lower():
                wgString += nodestr + ".svp.solvid=31"+"\n"
                solverString = nodestr + ".svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif get_mode_solver().lower() == 'semivecTM FDM complex'.lower():
                wgString += nodestr + ".svp.solvid=47"+"\n"
                solverString = nodestr + ".svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif get_mode_solver().lower() == 'vectorial FMM real'.lower():
                wgString += nodestr + ".svp.solvid=65"+"\n"
                solverString = nodestr + ".svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            elif get_mode_solver().lower() == 'semivecTE FMM real'.lower():
                wgString += nodestr + ".svp.solvid=17"+"\n"
                solverString = nodestr + ".svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            elif get_mode_solver().lower() == 'semivecTM FMM real'.lower():
                wgString += nodestr + ".svp.solvid=33"+"\n"
                solverString = nodestr + ".svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            elif get_mode_solver().lower() == 'vectorial FMM complex'.lower():
                wgString += nodestr + ".svp.solvid=73"+"\n"
                solverString = nodestr + ".svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            elif get_mode_solver().lower() == 'semivecTE FMM complex'.lower():
                wgString += nodestr + ".svp.solvid=25"+"\n"
                solverString = nodestr + ".svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            elif get_mode_solver().lower() == 'semivecTM FMM complex'.lower():
                wgString += nodestr + ".svp.solvid=41"+"\n"
                solverString = nodestr + ".svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            else:
                ErrStr = self.name + '.buildNode(): Invalid Modesolver String for Rectangular Waveguide (RWG): ' + str(get_mode_solver()) 
                ErrStr += '\n Please see `help(pyfimm.set_mode_solver)`, and use one of the following:'
                ErrStr += '\n   vectorial FDM real, semivecTE FDM real,semivecTM FDM real, '
                ErrStr += '\n   vectorial FDM complex, semivecTE FDM complex , semivecTM FDM complex, '
                ErrStr += '\n   vectorial FMM real, semivecTE FMM real, semivecTM FMM real, '
                ErrStr += '\n   vectorial FMM complex, semivecTE FMM complex, or semivecTM FMM complex'
                raise ValueError( ErrStr )
        
        # Set wavelength:
        wgString += self.nodestring + ".evlist.svp.lambda = %f \n"%(self.get_wavelength() )
        
        wgString += solverString
        
        return wgString
        
        
    
    ########################################
    ####    Old Deprecated Functions    ####
    
    
    def __buildNode2(self, name=None, parentNode=None):
        '''Build the Fimmwave node of this Ridge/Rectangular (RWG) waveguide.
        
        NOTE: This function has been replaced with a `buildNode` func. which uses the more extensible get_buildNode_str().
        
        Parameters
        ----------
        name : string, optional
            Provide a name for this waveguide node.
        parent : Node object, optional
            provide the parent (Project/Device) Node object for this waveguide.'''
        if name: self.name = name
        if parentNode: self.parent = parentNode
        if DEBUG(): print self.name + ".buildNode(): self.parent.num=", self.parent.num
        
        N_nodes = fimm.Exec("app.subnodes["+str(self.parent.num)+"].numsubnodes")
        node_num = int(N_nodes+1)
        self.num = node_num        
        self.BuildRectNode()    
        self.built=True
    #end buildNode2()
    
    
    def __BuildRectNode(self):
        '''Build the Node for Rectangular Coords (Slices).
        
        NOTE: Not used anymore, replaced with get_buildNode_str()
        '''
        # build RWG
        wgString = "app.subnodes["+str(self.parent.num)+"].addsubnode(rwguideNode,"+str(self.name)+")"+"\n"
        sliceN = 1
        for slc in self.slices:
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes[{"+str(self.num)+"}].insertslice({"+str(sliceN)+"})"+"\n"
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes[{"+str(self.num)+"}].slices[{"+str(sliceN)+"}].width = "+str(slc.width)+"\n"
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes[{"+str(self.num)+"}].slices[{"+str(sliceN)+"}].etch = "+str(slc.etch)+"\n"
            wgString += (len(slc.layers)-1)*("app.subnodes["+str(self.parent.num)+"].subnodes[{"+str(self.num)+"}].slices[{"+str(sliceN)+"}].insertlayer(1)"+"\n")
            layerN = 1
            for lyr in slc.layers:
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes[{"+str(self.num)+"}].slices[{"+str(sliceN)+"}].layers[{"+str(layerN)+"}].size = "+str(lyr.thickness)+"\n"+ \
                            "app.subnodes["+str(self.parent.num)+"].subnodes[{"+str(self.num)+"}].slices[{"+str(sliceN)+"}].layers[{"+str(layerN)+"}].nr11 = "+str(lyr.n())+"\n"+ \
                            "app.subnodes["+str(self.parent.num)+"].subnodes[{"+str(self.num)+"}].slices[{"+str(sliceN)+"}].layers[{"+str(layerN)+"}].nr22 = "+str(lyr.n())+"\n"+ \
                            "app.subnodes["+str(self.parent.num)+"].subnodes[{"+str(self.num)+"}].slices[{"+str(sliceN)+"}].layers[{"+str(layerN)+"}].nr33 = "+str(lyr.n())+"\n"
                
                if lyr.cfseg:
                    wgString += "app.subnodes["+str(self.parent.num)+"].subnodes[{"+str(self.num)+"}].slices[{"+str(sliceN)+"}].layers[{"+str(layerN)+"}].cfseg = "+str(1)+"\n"
                
                
                layerN += 1
            sliceN += 1

        # build boundary conditions - metal by default
        if get_left_boundary() is None:
            '''Default to Electric Wall/metal'''
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].lhsbc.type = 1"+"\n"
        else:
            if left_boundary().lower() == 'metal' or left_boundary().lower() == 'electric wall':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].lhsbc.type = 1"+"\n"
            elif left_boundary().lower() == 'magnetic wall':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].lhsbc.type = 2"+"\n"
            elif left_boundary().lower() == 'periodic':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].lhsbc.type = 3"+"\n"
            elif left_boundary().lower() == 'transparent':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].lhsbc.type = 4"+"\n"
            elif left_boundary().lower() == 'impedance':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].lhsbc.type = 5"+"\n"
            else:
                print self.name + '.buildNode(): Invalid input to set_left_boundary()'
                
        if right_boundary() is None:
            '''Default to Electric Wall/metal'''
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].rhsbc.type = 1"+"\n"
        else:
            if right_boundary().lower() == 'metal' or right_boundary().lower() == 'electric wall':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].rhsbc.type = 1"+"\n"
            elif right_boundary().lower() == 'magnetic wall':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].rhsbc.type = 2"+"\n"
            elif right_boundary().lower() == 'periodic':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].rhsbc.type = 3"+"\n"
            elif right_boundary().lower() == 'transparent':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].rhsbc.type = 4"+"\n"
            elif right_boundary().lower() == 'impedance':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].rhsbc.type = 5"+"\n"
            else:
                print self.name + '.buildNode(): Invalid input to set_right_boundary()'

        if bottom_boundary() is None:
            '''Default to Electric Wall/metal'''
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].botbc.type = 1"+"\n"
        else:
            if bottom_boundary().lower() == 'metal' or bottom_boundary().lower() == 'electric wall':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].botbc.type = 1"+"\n"
            elif bottom_boundary().lower() == 'magnetic wall':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].botbc.type = 2"+"\n"
            elif bottom_boundary().lower() == 'periodic':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].botbc.type = 3"+"\n"
            elif bottom_boundary().lower() == 'transparent':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].botbc.type = 4"+"\n"
            elif bottom_boundary().lower() == 'impedance':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].botbc.type = 5"+"\n"
            else:
                print self.name + '.buildNode(): Invalid input to set_bottom_boundary()'

        if top_boundary() is None:
            '''Default to Electric Wall/metal'''
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].topbc.type = 1"+"\n"
        else:
            if top_boundary().lower() == 'metal' or top_boundary().lower() == 'electric wall':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].topbc.type = 1"+"\n"
            elif top_boundary().lower() == 'magnetic wall':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].topbc.type = 2"+"\n"
            elif top_boundary().lower() == 'periodic':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].topbc.type = 3"+"\n"
            elif top_boundary().lower() == 'transparent':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].topbc.type = 4"+"\n"
            elif top_boundary().lower() == 'impedance':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].topbc.type = 5"+"\n"
            else:
                print self.name + '.buildNode(): Invalid input to set_top_boundary()'

        if pml_x() is None:
            '''Default to 0.0'''
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].lhsbc.pmlpar = {0.0}"+"\n"+ \
                        "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].rhsbc.pmlpar = {0.0}"+"\n"
        else:
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].lhsbc.pmlpar = {"+str(pml_x())+"}"+"\n"+ \
                        "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].rhsbc.pmlpar = {"+str(pml_x())+"}"+"\n"

        if pml_y() is None:
            '''Default to 0.0'''
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].topbc.pmlpar = {0.0}"+"\n"+ \
                        "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].botbc.pmlpar = {0.0}"+"\n"
        else:
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].topbc.pmlpar = {"+str(pml_y())+"}"+"\n"+ \
                        "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].botbc.pmlpar = {"+str(pml_y())+"}"+"\n"
            
        # set solver parameters
        if self.bend_radius == 0:
            '''Default to 0.0 -straight'''
            hcurv = 0
        else:
            hcurv = 1.0/self.bend_radius
        wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.hcurv={"+str(hcurv)+"}"+"\n"

        wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.autorun=0"+"\n"
        wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.speed=0"+"\n"


        if horizontal_symmetry() is None:
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.hsymmetry=0"+"\n"
        else:
            if horizontal_symmetry() == 'none':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.hsymmetry=0"+"\n"
            elif horizontal_symmetry() == 'ExSymm':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.hsymmetry=1"+"\n"
            elif horizontal_symmetry() == 'EySymm':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.hsymmetry=2"+"\n"
            else:
                print self.name + '.buildNode(): Invalid horizontal_symmetry. Please use: none, ExSymm, or EySymm'

        if vertical_symmetry() is None:
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.vsymmetry=0"+"\n"
        else:
            if vertical_symmetry() == 'none':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.vsymmetry=0"+"\n"
            elif vertical_symmetry() == 'ExSymm':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.vsymmetry=1"+"\n"
            elif vertical_symmetry() == 'EySymm':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.vsymmetry=2"+"\n"
            else:
                print self.name + '.buildNode(): Invalid vertical_symmetry. Please use: none, ExSymm, or EySymm'

        if N() is None:
            '''Default to 10'''
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.maxnmodes={10}"+"\n"
        else:
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.maxnmodes={"+str(N())+"}"+"\n"

        if get_NX() is None:
            '''Default to 60'''
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.nx={60}"+"\n"
            nx_svp = 60
        else:
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.nx={"+str(NX())+"}"+"\n"
            nx_svp = get_NX()

        if get_NY() is None:
            '''Default to 60'''
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.ny={60}"+"\n"
            ny_svp = 60
        else:
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.ny={"+str(NY())+"}"+"\n"
            ny_svp = get_NY()

        if min_TE_frac() is None:
            '''Default to 0.0'''
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.mintefrac={0}"+"\n"
        else:
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.mintefrac={"+str(min_TE_frac())+"}"+"\n"
        
        if max_TE_frac() is None:
            '''Default to 100.0'''
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.maxtefrac={100}"+"\n"
        else:
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.maxtefrac={"+str(max_TE_frac())+"}"+"\n"
        
        if min_EV() is None:
            '''Default to -1e50'''
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.evend={-1e+050}"+"\n"
        else:
            wgStrint += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.evend={"+str(min_EV())+"}"+"\n"
        
        if max_EV() is None:
            '''Default to +1e50'''
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.evstart={1e+050}"+"\n"
        else:
            wgStrint += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.evend={"+str(max_EV())+"}"+"\n"

        if RIX_tol() is None:
            rix_svp = 0.010000
        else:
            rix_svp = RIX_tol()

        if N_1d() is None:
            n1d_svp = 30
        else:
            n1d_svp = N_1d()

        if mmatch() is None:
            mmatch_svp = 0
        else:
            mmatch_svp = mmatch()

        if mode_solver() is None:
            print 'Using default mode solver: "vectorial FDM real"  '
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=71"+"\n"
            solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
        else:
            if get_mode_solver().lower() == 'vectorial FDM real'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=71"+"\n"
                solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif get_mode_solver().lower() == 'semivecTE FDM real'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=23"+"\n"
                solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif get_mode_solver().lower() == 'semivecTM FDM real'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=39"+"\n"
                solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif get_mode_solver().lower() == 'vectorial FDM complex'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=79"+"\n"
                solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif get_mode_solver().lower() == 'semivecTE FDM complex'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=31"+"\n"
                solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif get_mode_solver().lower() == 'semivecTM FDM complex'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=47"+"\n"
                solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif get_mode_solver().lower() == 'vectorial FMM real'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=65"+"\n"
                solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            elif get_mode_solver().lower() == 'semivecTE FMM real'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=17"+"\n"
                solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            elif get_mode_solver().lower() == 'semivecTM FMM real'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=33"+"\n"
                solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            elif get_mode_solver().lower() == 'vectorial FMM complex'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=73"+"\n"
                solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            elif get_mode_solver().lower() == 'semivecTE FMM complex'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=25"+"\n"
                solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            elif get_mode_solver().lower() == 'semivecTM FMM complex'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=41"+"\n"
                solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            else:
                print 'Invalid Rectangular Mode Solver. Please see `help(pyfimm.set_mode_solver)`, and use one of the following:'
                print 'vectorial FDM real, semivecTE FDM real,semivecTM FDM real, '
                print 'vectorial FDM complex, semivecTE FDM complex , semivecTM FDM complex, '
                print 'vectorial FMM real, semivecTE FMM real, semivecTM FMM real, '
                print 'vectorial FMM complex, semivecTE FMM complex, or semivecTM FMM complex'
                raise ValueError("Invalid Modesolver String: " + str(get_mode_solver()) )

        wgString += solverString
        fimm.Exec(wgString)

    #end buildRect()

#end Waveguide class







'''
###################################################
#           Global Mode Solver Parameters         #
#            For rectangular waveguides           #
###################################################
'''

def set_x_pml(pml_x):
    '''Set length of Perfectly-Matched Layer in X (horizontal) direction.'''
    global global_horizontal_pml
    global_horizontal_pml = pml_x

def set_pml_x(w):
    '''Backwards compatibility only.  Should instead use set_x_pml.'''
    print "Deprecation Warning:  set_pml_x():  Use set_x_pml() instead."
    set_x_pml(w)

def get_x_pml():
    '''Get length of Perfectly-Matched Layer in horizontal direction (X). Returns None if not set.'''
    global global_horizontal_pml
    try:
        global_horizontal_pml
    except NameError:
        global_horizontal_pml = None
    return global_horizontal_pml

def get_pml_x():
    '''Backwards compatibility only.  Should instead use get_circ_pml.'''
    print "Deprecation Warning:  get_pml_x():  Use get_x_pml() instead."
    return get_x_pml()

def pml_x():
    '''Backwards compatibility only. 
    Please use get_***() instead.'''
    print "DeprecationWarning: Use get_x_pml() instead."
    return get_x_pml()



def set_y_pml(pml_y):
    '''Set length of Perfectly-Matched Layer in Y (vertical) direction.'''
    global global_vertical_pml
    global_vertical_pml = pml_y

def set_pml_x(w):
    '''Backwards compatibility only.  Should instead use set_y_pml.'''
    print "Deprecation Warning:  set_pml_y():  Use set_y_pml() instead."
    set_y_pml(w)

def get_y_pml():
    '''Get length of Perfectly-Matched Layer in vertical direction (Y). Returns None if not set.'''
    global global_vertical_pml
    try:
        global_vertical_pml
    except NameError:
        global_vertical_pml = None
    return global_vertical_pml

def get_pml_y():
    '''Backwards compatibility only.  Should instead use get_y_pml.'''
    print "Deprecation Warning:  get_pml_y():  Use get_y_pml() instead."
    return get_y_pml()

def pml_y():
    '''Backwards compatibility only. 
    Please use get_***() instead.'''
    print "DeprecationWarning: Use get_y_pml() instead."
    return get_y_pml()



def set_top_boundary(bndry):
    '''Set boundary type of top side of rectangular waveguide.
    
    Parameters
    ----------
    bndry : string { 'metal' | 'magnetic wall' | 'periodic' | 'transparent' | 'impedance' }
    '''
    possibleArgs = ['metal' , 'magnetic wall' , 'periodic' , 'transparent' , 'impedance']
    exists = len(   np.where(  np.array( type ) == np.array( possibleArgs)  )[0]   )
    if not exists: raise ValueError("Allowed arguments are: 'metal' | 'magnetic wall' | 'periodic' | 'transparent' | 'impedance' ")
    global global_TBC
    global_TBC = bndry

def get_top_boundary():
    '''Get boundary type of top side of waveguides.
    
    Returns
    -------
    type : string { 'metal' | 'magnetic wall' | 'periodic' | 'transparent' | 'impedance' }
    '''
    global global_TBC
    try:
        global_TBC
    except NameError:
        global_TBC = None
    return global_TBC

def top_boundary():
    '''Backwards compatibility only.  Should Instead get_top_boundary().'''
    print "Deprecation Warning:  top_boundary():  Use get_top_boundary() instead."
    return get_top_boundary()



def set_bottom_boundary(bndry):
    '''Set boundary type of bottom side of rectangular waveguide.
    
    Parameters
    ----------
    bndry : string { 'metal' | 'magnetic wall' | 'periodic' | 'transparent' | 'impedance' }
    '''
    possibleArgs = ['metal' , 'magnetic wall' , 'periodic' , 'transparent' , 'impedance']
    exists = len(   np.where(  np.array( type ) == np.array( possibleArgs)  )[0]   )
    if not exists: raise ValueError("Allowed arguments are: 'metal' | 'magnetic wall' | 'periodic' | 'transparent' | 'impedance' ")
    global global_BBC
    global_BBC = bndry

def get_bottom_boundary():
    '''Get boundary type of top side of waveguides.
    
    Returns
    -------
    type : string { 'metal' | 'magnetic wall' | 'periodic' | 'transparent' | 'impedance' }
    '''
    global global_BBC
    try:
        global_BBC
    except NameError:
        global_BBC = None
    return global_BBC
    
def bottom_boundary():
    '''Backwards compatibility only.  Should Instead get_bottom_boundary().'''
    print "Deprecation Warning:  bottom_boundary():  Use get_bottom_boundary() instead."
    return get_bottom_boundary()



def set_left_boundary(bndry):
    '''Set boundary type of left side of rectangular waveguide.
    
    Parameters
    ----------
    bndry : string { 'metal' | 'magnetic wall' | 'periodic' | 'transparent' | 'impedance' }
    '''
    possibleArgs = ['metal' , 'magnetic wall' , 'periodic' , 'transparent' , 'impedance']
    exists = len(   np.where(  np.array( type ) == np.array( possibleArgs)  )[0]   )
    if not exists: raise ValueError("Allowed arguments are: 'metal' | 'magnetic wall' | 'periodic' | 'transparent' | 'impedance' ")
    global global_LBC
    global_LBC = bndry

def get_left_boundary():
    '''Get boundary type of top side of waveguides.
    
    Returns
    -------
    type : string { 'metal' | 'magnetic wall' | 'periodic' | 'transparent' | 'impedance' }
    '''
    global global_LBC
    try:
        global_LBC
    except NameError:
        global_LBC = None
    return global_LBC
    
def left_boundary():
    '''Backwards compatibility only.  Should Instead get_left_boundary().'''
    print "Deprecation Warning:  left_boundary():  Use get_left_boundary() instead."
    return get_left_boundary()



def set_right_boundary(bndry):
    '''Set boundary type of right side of rectangular waveguide.
    
    Parameters
    ----------
    bndry : string { 'metal' | 'magnetic wall' | 'periodic' | 'transparent' | 'impedance' }
    '''
    possibleArgs = ['metal' , 'magnetic wall' , 'periodic' , 'transparent' , 'impedance']
    exists = len(   np.where(  np.array( type ) == np.array( possibleArgs)  )[0]   )
    if not exists: raise ValueError("Allowed arguments are: 'metal' | 'magnetic wall' | 'periodic' | 'transparent' | 'impedance' ")
    global global_RBC
    global_RBC = bndry

def get_right_boundary():
    '''Get boundary type of top side of waveguides.
    
    Returns
    -------
    type : string { 'metal' | 'magnetic wall' | 'periodic' | 'transparent' | 'impedance' }
    '''
    global global_RBC
    try:
        global_RBC
    except NameError:
        global_RBC = None
    return global_RBC
    
def right_boundary():
    '''Backwards compatibility only.  Should Instead get_right_boundary().'''
    print "Deprecation Warning:  right_boundary():  Use get_right_boundary() instead."
    return get_right_boundary()


