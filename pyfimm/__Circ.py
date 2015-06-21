'''Circ class, part of pyFIMM.
Objects & functions needed for cylindrical calculations.'''

#from pylab import *     # must kill these global namespace imports!
#from numpy import *
from __pyfimm import *      # access the main module's classes & modesolver functions

from __globals import *         # import global vars & FimmWave connection object
# DEBUG() variable is also set in __globals

#from __Waveguide import *   # not needed?
from __Mode import *        # import Mode class

#from __pyfimm import DEBUG()        # Value is set in __pyfimm.py

from numpy import inf       # infinity, for hcurv/bend_radius


class Circ(Node):
    """pyFimm Circ object, 2-D Cylindrical-coordinate version of Waveguide (a fimmWave FWG waveguide, eg. optical fiber).  
    When a Thickness is supplied (in the cylindrical Z direction), this becomes a 3D structure.
    This inherits from the pyFIMM Node objects.
    
    
    Parameters
    ----------
    layers : list
        List containing the Layer objects used to generate this Circ.
    thickness : float, optional
        Apply a 3D length to this waveguide, in the direction of propagation. 
        
    
    Attributes
    ----------
    type : {'cyl_waveguide'}
        Currently = 'cyl_waveguide'.    May be deprecate as it is unused.
    
    length : float
        Apply a 3D length to this waveguide, in the direction of propagation. 
    
    layers : list
        List containing all the layers the Waveguide is constructed with.  The layers are ordered beginning from the innermost to the outermost.
    
    bend_radius : float
        Bend Radius of the waveguide.  The default value of `inf` indicates a straight waveguide.
        Defined from the center of the waveguide cross-section to the axis of the bend.
        Positive value means WG bends to the LEFT (so Right-Hand boundaries will see the radiatiing bend modes, if any).  Negative value bends the opposite way.    

    modes : list
        lists the modes calc'd for this waveguide (after Waveguide.calc()  )
        
    built : { True | False }
        Has this node been built in FimmWave yet?
    
    nodestring : string
        The fimmwave string pointing to this waveguide's node.  eg. "app.subnodes[1].subnodes[3]"
        Does not have a trailing period.
    
    
    Methods
    -------
    
    This is a partial list - see `dir(pf.Circ)` to see all methods.
    Please see help on a specific function via `help(pf.Circ)` for detailed up-to-date info on accepted arguments etc.
    
    mode(modenum)
        modenum: int
            Returns the specified Mode object.  Mode(0) is usually the fundamental mode, depending on the solver options.
    
    get_radius()
        Return total radius of this Waveguide, by adding up radius of each contained Layer.
    
    get_layer_radii()
        Return the thickness of each layer in this Waveguide, as list.
        
    buildNode( [name=, parentNode=] )
        Build the Fimmwave node of this Fiber/Cylindrical (FWG) waveguide.
    
    get_buildNode_str(nodestr [, obj=None, target=None])
        Return the fimmwave commands needed to build this waveguide node.  This command does not create the new waveguide node first (ie. it does not run `app.subnodes[1].addsubnode(rwguideNode, WGname)`  )
        So you must create the appropriate type of waveguide node first, and then issue the commands returned by this func. The massive multi-line string includes all the modesolver settings needed to calculate the waveguide afterwards.
    
    get_solver_str(nodestr ...)
        Returns just the MOLAB mode-solver configuration as a fimmwave-executable string.
    
    set_autorun()
        Set the fimmwave "autorun" flag which allows FimmProp to calc the modes when needed.
        
    unset_autorun():
        Unset the fimmwave "autorun" flag.
    
    set_material_database( PathString )
        Not recommended - it is safer to use a global material file, and have that file `include` other material files.  FimmProp Devices only support a single global materials file.
        
        PathString : string
            Path to a FimmWave material database (*.mat) for this waveguide node, if different from the globally set one (see `set_material_database()` ).
    
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
    Create a Circ by calling it (instancing it) with Materials called with a radius.
    The first Material is at the center (r=0), and construction proceeds from the inside to the outer radius.
    
    >>> DBRLo = Circ(  AlGaAs(5.0)  )   # 5.00 radius circle
    >>> DBRHi = Circ(  GaAs(5.0)  )
    
    >>> CurrentAperture = Circ(  AlGaAs(3.0) + AlOx(2.0)  ) 
    3.0 um radius of AlGaAs in the center, clad by 2um of AlOx.
    
    >>> CurrentAperture.buildNode( name='Current Aperture', parentNode=wg_prj )
    >>> CurrentAperture.calc()
    >>> CurrentAperture.mode(0).plot()      # plot the mode!
    
    """


    def __init__(self,*args):
        if len(args) >= 1:
            self.type = 'cyl_waveguide'
            self.name = None
            self.autorun = True
            self.built=False
            self.length = 0.0
            self.__wavelength = get_wavelength()    # get global wavelength
            self.layers = []
            for lyr in args[0]:
                self.layers.append(lyr)     # re-create a list of layers
            self.length = 0
            self.modes = []
            self.bend_radius = inf      # inf = straight WG
            self.__materialdb = None
        else:
            raise ValueError('Invalid number of input arguments to Circ()')
        if len(args) == 2:
            self.length = args[1]   # can pass length as 2nd arg if desired


    def __str__(self):
        '''How to `print` this object
        TO DO:  reproduce the Layer.__repr__ string here, to have it print Radius= instead of Thickness='''
        str=""
        if self.name: str += "Name: '"+self.name+"'\n"
        str = 'Radius = %7.4f \n' % self.get_radius()
        for i,lyr in enumerate(self.layers):
            if i == 0:
                str += 3*'*' + ' Innermost Layer: ' + 3*'*' + '\n%s' % (lyr) + '\n'
            elif i == (len(self)-1):
                str += 3*'*' + ' Outermost Layer: ' + 3*'*' + '\n%s' % (lyr) + '\n'
            else:
                str += 3*'*' + ' Middle Layer %i: ' % i + 3*'*' + '\n%s' % lyr + '\n'
        return str


    #def __call__(self,length):
    #    '''Calling ThisCirc(thick) sets the Thickness of this Circ, and returns a list containing this Slice.'''
    #    self.length = length
    #    return [self]
    def __call__(self,*args):
        '''Calling a WG object with one argument creates a Section of passed length, and returns a list containing this new WG. For example:
            Usually passed directly to Device as so:
            >>> Device(  Circ1(10.5) + Circ2(1.25) + Circ3(10.5)  )
        '''
        if len(args) == 1:
            l = args[0]     # set thickness from 1st arg
        else:
            raise ValueError("Invalid Number of Arguments to Waveguide().")
        
        # Always call WG with 1 args
        out = [   Section(  self, l  )   ]    # include cfseg 
        return out

    def __add__(self,other):
        '''Addition returns a list containing each Circ'''
        return [self,other]

    def __len__(self):
        '''len(ThisCirc) returns the number of Layers in ThisCirc'''
        return len(self.layers)


    def get_radius(self):
        '''Return summed Radius of all Layers in this Circ - for compatibility with Slice'''
        thck = 0
        for lyr in self.layers:
            thck += lyr.thickness
        return thck
        
    def radius():
        '''Backwards compatibility only.  Should Instead get_radius().'''
        print "Deprecation Warning:  radius():  Use get_radius() instead."
        return get_radius()


    def layer_radii(self):
        '''Return list of Radii of each Layer in this Circ - for compatibility with Slice'''
        lyr_thck = []
        for lyr in self.layers:
            lyr_thck.append(lyr.thickness)
        return lyr_thck

    def mode(self,modeN):
        '''Circ.mode(int): Return the specified pyFimm Mode object for this waveguide. Fundamental mode is mode(0).'''
        return Mode(self, modeN,"app.subnodes[{"+str(self.parent.num)+"}].subnodes[{"+str(self.num)+"}].evlist.")


    def calc(self):
        '''Calculate/Solve for the modes of this Waveguide'''
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
            asnumeric : boolean, optional
                A True value will cause the output to be numeric, rather than string.  See help(set_joint_type) for the numerical/string correlations.  False by default.
                (FYI, `asnumeric=True` is used in Device.buildNode()  )
        '''
        try:
            self.__jointtype    # see if variable exists
        except AttributeError:
            # if the variable doesn't exist yet.
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
    ####    Cylindrical Waveguide Node Construction ####
    ####################################################
        

    def buildNode(self, name=None, parent=None, overwrite=False, warn=True):
        '''Build the Fimmwave node of this cylindrical (FWG) waveguide.
        
        Parameters
        ----------
        name : string, optional
            Provide a name for this waveguide node.
            
        parent : Node object, optional
            Provide the parent (Project/Device) Node object for this waveguide.
        
        overwrite : { True | False }, optional
            Overwrite existing node of same name?  Defaults to False, which will rename the node if it has the same name as an existing node.
        
        warn : {True | False}, optional
            Print notification if overwriting a node?  True by default.
        
        '''
        if name: self.name = name
        if parent: self.parent = parent
        
        nodestring="app.subnodes["+str(self.parent.num)+"]"
        self._checkNodeName(nodestring, overwrite=overwrite, warn=warn)     # will alter the node name if needed
        
        N_nodes = fimm.Exec("app.subnodes["+str(self.parent.num)+"].numsubnodes")
        node_num = int(N_nodes+1)
        self.num = node_num
        
        # build FWG
        wgString = "app.subnodes["+str(self.parent.num)+"].addsubnode(fwguideNode,"+str(self.name)+")"+"\n"
        
        self.nodestring = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"]"
        fimm.Exec(  wgString + self.get_buildNode_str(self.nodestring, warn=warn)  ) 
        
        self.built = True
    #end buildNode()
    
    
    def get_buildNode_str(self, nodestr, obj=None, target=None, warn=True):
        '''Return the node construction string for either a standalone waveguide or device.
        This is for a Cylindrical/Fiber (FWG) waveguide.
        The new Waveguide subnode should be created BEFORE calling this function, so that you can pass the correct node string.
    
        Parameters
        ----------
        nodestr : str
            The entire base-string to address the necessary node.  For example:
            >>> nodestr = "app.subnodes[1].subnodes[2]"
            the subnode referenced should be the NEW subnode to be created (ie. one higher than previously in existence).  In normal operation, the new subnode has already been created by WG.buildnode().
        
        obj : Circ object, optional
            Defaults to `self`.  Can pass another object instead, to get the buildNode string for that.
        
        target : { 'wglens' | 'taper' }, optional
            Omits certain parameters from being set depending on target.  Used for building tapers.
        '''
        
        '''
        newnodestr = ""
        nsplit = nodestr.split('.')
        
        ### Remove last node component, to create new subnode
        for strang in nsplit[0:-1] :
            newnodestr += strang + '.'
        if DEBUG(): print "newnodestr: \n%s"%newnodestr, "nodestr: \n%s"%nodestr
        
        
        if target == 'waveguide':
            newnodestr2 = "app.subnodes["+str(self.parent.num)+"]"
            nodestr2 = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"]"
            if DEBUG(): print "newnodestr2: \n%s"%newnodestr2, "nodestr2: \n%s"%nodestr2
        '''
        
        if not obj: obj=self
        
        
        # build FWG Node
        if DEBUG(): print "Circ: "+self.name+".__get_buildNode_str(): "
        
        
        # check for custom material DB in this WG node.
        if not self.__materialdb:
            '''Use global material DB if this WG doesn't have a custom one set.'''
            matDB = get_material_database()
        else:
            matDB = self.__materialdb
            #if DEBUG(): print "Using custom matDB: `%s`"%matDB
        
        
        wgString=""     # The fimmwave string to return
        
        wgString += nodestr + ".deletelayer(2)   \n"    # FWG always starts with 2 layers, delete the 2nd one.
        
        if matDB: 
            #if DEBUG(): print "setting MaterBase file to: '%s'"%matDB
            wgString += nodestr + ".setmaterbase(" + matDB + ")  \n" 
        
        layerN = 1
        for lyr in obj.layers:
            if DEBUG(): print "Layer ", layerN, "; radius:", lyr.thickness
            
            if layerN > 1: wgString += nodestr + ".insertlayer("+str(layerN)+")  \n"
            wgString += nodestr + ".layers[{"+str(layerN)+"}].size = "+str(lyr.thickness)+"\n"
            
            if lyr.material.type == 'rix':
                wgString += \
                nodestr + ".layers[{"+str(layerN)+"}].nr11 = "+str(lyr.n())+"\n"+ \
                nodestr + ".layers[{"+str(layerN)+"}].nr22 = "+str(lyr.n())+"\n"+ \
                nodestr + ".layers[{"+str(layerN)+"}].nr33 = "+str(lyr.n())+"\n"
            elif lyr.material.type == 'mat':
                if DEBUG(): print "Layer %i: mx="%(layerN), lyr.material.mx, " // my=", lyr.material.my
                wgString +=   nodestr + ".layers[{"+str(layerN)+"}].setMAT(" + str(lyr.material.mat) + ") \n"
                if lyr.material.mx:   wgString +=  nodestr + ".layers[{"+str(layerN)+"}].mx = "+str(lyr.material.mx)+"\n"
                if lyr.material.my:   wgString +=  nodestr + ".layers[{"+str(layerN)+"}].my = "+str(lyr.material.my)+"\n"
    
            if lyr.cfseg:
                wgString += nodestr + ".layers[{"+str(layerN)+"}].cfseg = 1   \n"
    
            layerN += 1
        #end for(obj.layers)
        

        # Set PML layer:
        if get_circ_pml() is None:
            '''PML width is 0.0 by default, defined here'''
            wgString += nodestr + ".bc.pmlpar = {0.0}"+"\n"
        else:
            wgString += nodestr + ".bc.pmlpar = {"+str( get_circ_pml() )+"}"+"\n"

        
        # build boundary conditions - metal by default
        if get_circ_boundary() is None:
            '''Default to Electric Wall/metal'''
            if warn: print self.name + ".buildNode(): circ_boundary: Using electric wall boundary."
            wgString += nodestr + ".bc.type = 1"+"\n"
        else:
            if get_circ_boundary().lower() == 'metal' or get_circ_boundary().lower() == 'electric wall':
                wgString += nodestr + ".bc.type = 1"+"\n"
            elif get_circ_boundary().lower() == 'magnetic wall':
                wgString += nodestr + ".bc.type = 2"+"\n"
            elif get_circ_boundary().lower() == 'periodic':
                wgString += nodestr + ".bc.type = 3"+"\n"
            elif get_circ_boundary().lower() == 'transparent':
                wgString += nodestr + ".bc.type = 4"+"\n"
            elif get_circ_boundary().lower() == 'impedance':
                wgString += nodestr + ".bc.type = 5"+"\n"
            else:
                print self.name + ".buildNode(): Invalid input to set_circ_boundary()"
        
        
        wgString += self.get_solver_str(nodestr, obj=obj, target=target)

        
        #if DEBUG(): print "__get_buildNode_Str(): wgString=\n", wgString
        
        return wgString
    #end __buildNode()
    
    
    
    def get_solver_str(self, nodestr, obj=None, target=None):
        ''' Return only the Solver ('svp') and mode solver (MOLAB, 'mpl') params for creating this node.
        Used for building Tapers, when the WG is already built otherwise.'''
        if not obj: obj=self

        #if DEBUG(): print "Circ.get_solver_str()... "
        
        wgString = ""
        
        # set solver parameters
        if target == 'wglens' or target == 'taper':
            '''hcurv/bend_radius is set separately for Taper or WGLens, since they could have a different curvature from their base WG object.'''
            pass
        else:
            nodestr = nodestr + ".evlist"     #WG nodes set their solver params under this subheading
            if obj.bend_radius == 0:
                obj.bend_radius = inf
                if warn: print self.name + ".buildNode(): Warning: bend_radius = 0.0 --> inf (straight waveguide)"
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
        
        
        if get_solver_speed()==1: 
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
                raise ValueError( 'Invalid horizontal_symmetry. Please use: none, ExSymm, or EySymm')

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
                raise ValueError( 'Inalid horizontal_symmetry. Please use: none, ExSymm, or EySymm')

        wgString += nodestr + ".mlp.maxnmodes={"+str( get_N() )+"}"+"\n"

        wgString += nodestr + ".mlp.nx={"+str( get_NX() )+"}"+"\n"
        nx_svp = get_NX()

        wgString += nodestr + ".mlp.ny={"+str( get_NY() )+"}"+"\n"
        ny_svp = get_NY()

        wgString += nodestr + ".mlp.mintefrac={"+str( get_min_TE_frac() )+"}"+"\n"
        
        wgString += nodestr + ".mlp.maxtefrac={"+str( get_max_TE_frac())+"}"+"\n"
        
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
            print  self.name + '.buildNode(): Using Default Mode Solver: "Vectorial FDM Real"  '
            wgString += nodestr + ".svp.solvid=192"+"\n"
            solverString = nodestr + ".svp.buff=V1 "+str(n1d_svp)+" "+str(0)+" "+str( get_N() )+" "+str( 1 )+" "+str( get_Np() )+" "+"\n"
        else:
            if get_mode_solver().lower() == 'Vectorial SMF'.lower():
                wgString += nodestr + ".svp.solvid=50"+"\n"
                solverString = "\n"
            elif get_mode_solver().lower() == 'SemiVecTE SMF'.lower():
                wgString += nodestr + ".svp.solvid=18"+"\n"
                solverString = "\n"
            elif get_mode_solver().lower() == 'SemiVecTM SMF'.lower():
                wgString += nodestr + ".svp.solvid=34"+"\n"
                solverString = "\n"
            elif get_mode_solver().lower() == 'Vectorial Gaussian'.lower():
                wgString += nodestr + ".svp.solvid=53"+"\n"
                solverString = "\n"
            elif get_mode_solver().lower() == 'SemiVecTE Gaussian'.lower():
                wgString += nodestr + ".svp.solvid=21"+"\n"
                solverString = "\n"
            elif get_mode_solver().lower() == 'SemiVecTM Gaussian'.lower():
                wgString += nodestr + ".svp.solvid=37"+"\n"
                solverString = "\n"
            elif get_mode_solver().lower() == 'Vectorial GFS Real'.lower():
                wgString += nodestr + ".svp.solvid=68"+"\n"
                solverString = nodestr + ".svp.buff=V1 "+str( get_Nm()[0] )+" "+str( get_Nm()[1] )+" "+str( get_Np()[0] )+" "+str( get_Np()[1] )+" "+"\n"
            elif get_mode_solver().lower() == 'Scalar GFS Real'.lower():
                wgString += nodestr + ".svp.solvid=4"+"\n"
                solverString = nodestr + ".svp.buff=V1 "+str( get_Nm()[0] )+" "+str( get_Nm()[1] )+" "+str( get_Np()[0] )+" "+str( get_Np()[1] )+" "+"\n"
            elif get_mode_solver().lower() == 'Vectorial FDM real'.lower():
                wgString += nodestr + ".svp.solvid=192"+"\n"
                solverString = nodestr + ".svp.buff=V1 "+str(n1d_svp)+" "+str( get_Nm()[0] )+" "+str( get_Nm()[1] )+" "+str( get_Np()[0] )+" "+str( get_Np()[1] )+" "+"\n"
            elif get_mode_solver().lower() == 'Vectorial FDM complex'.lower():
                wgString += nodestr + ".svp.solvid=200"+"\n"
                solverString = nodestr + ".svp.buff=V1 "+str(n1d_svp)+" "+str( get_Nm()[0] )+" "+str( get_Nm()[1] )+" "+str( get_Np()[0] )+" "+str( get_Np()[1] )+" "+"\n"
            else:
                print self.name + '.buildNode(): Invalid Cylindrical Mode Solver. Please see `help(pyfimm.set_mode_solver)`, and use one of the following options :'
                print '    Finite-Difference Method solver: "vectorial FDM real" , "vectorial FDM complex",'
                print '    General Fiber Solver: "vectorial GFS real" , "scalar GFS real",'
                print '    Single-Mode Fiber solver: "Vectorial SMF" , "SemivecTE SMF" , "SemivecTM SMF",'
                print '    Gaussian Fiber Solver (unsupported): "Vectorial Gaussian" , "SemivecTE Gaussian" , "SemivecTM Gaussian".'
                raise ValueError("Invalid Modesolver String: " + str(get_mode_solver()) )
        
        # Set wavelength:
        wgString += self.nodestring + ".evlist.svp.lambda = " + str( self.get_wavelength() ) + "   \n"
        
        wgString += solverString
        
        return wgString
    #end __get_solver_str()
    
    

    def __buildNode2(self, name=None, parentNode=None):
        '''Build the Fimmwave node of this cylindrical (FWG) waveguide.
        
        NOTE: This function has been deprecated, in preference of the new buildNode, which uses 
            the more extensible get_buildNodeStr() function.
        
        Parameters
        ----------
        name : string, optional
            Provide a name for this waveguide node.
        parent : Node object, optional
            Provide the parent (Project/Device) Node object for this waveguide.
        '''
        if name: self.name = name
        if parentNode: self.parent = parentNode
        N_nodes = fimm.Exec("app.subnodes["+str(self.parent.num)+"].numsubnodes")
        node_num = int(N_nodes+1)
        self.num = node_num        
        self.BuildCylNode() 
    #end buildNode2()

    def __BuildCylNode(self):
        '''Build the Node for Cylindrical Coords (Circ's).
        
        NOTE: This function has been deprecated, in preference of the new BuildCylNode, which uses 
            the more extensible get_buildNodeStr() function.
            
        To DO
        -----
        Add PML setting per-WG?  Or just do global PML like Jared's? I like global (manual might say all PMLs should be the same)
        Currently only supports Step Index:
            Allow Gaussian profile, which takes { Radius (um), Sigma (um), neff }
            Spline {splineNseg (int), cornerpoint (bool)}...
        '''
        # build FWG
        if DEBUG(): print "BuildCylNode(): "
        
        wgString = "app.subnodes["+str(self.parent.num)+"].addsubnode(fwguideNode,"+str(self.name)+")"+"\n"
        
        wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].deletelayer(2)   \n"    # FWG always starts with 2 layers, delete the 2nd one.
        
        layerN = 1
        for lyr in self.layers:
            if DEBUG(): print "BuildCylNode(): layer ", layerN, "; radius:", lyr.thickness, "; n:", lyr.n()
            if layerN > 1: wgString += "app.subnodes["+str(self.parent.num)+"].subnodes[{"+str(self.num)+"}].insertlayer("+str(layerN)+")  \n"
            wgString += \
            "app.subnodes["+str(self.parent.num)+"].subnodes[{"+str(self.num)+"}].layers[{"+str(layerN)+"}].size = "+str(lyr.thickness)+"\n"+ \
            "app.subnodes["+str(self.parent.num)+"].subnodes[{"+str(self.num)+"}].layers[{"+str(layerN)+"}].nr11 = "+str(lyr.n())+"\n"+ \
            "app.subnodes["+str(self.parent.num)+"].subnodes[{"+str(self.num)+"}].layers[{"+str(layerN)+"}].nr22 = "+str(lyr.n())+"\n"+ \
            "app.subnodes["+str(self.parent.num)+"].subnodes[{"+str(self.num)+"}].layers[{"+str(layerN)+"}].nr33 = "+str(lyr.n())+"\n"

            if lyr.cfseg:
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes[{"+str(self.num)+"}].layers[{"+str(layerN)+"}].cfseg = "+str(1)+"\n"

            layerN += 1
        #end for(self.layers)
        

        # Set PML layer:
        if get_circ_pml() is None:
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].bc.pmlpar = {0.0}"+"\n"
        else:
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].bc.pmlpar = {"+str( get_circ_pml() )+"}"+"\n"

        
        # build boundary conditions - metal by default
        if get_circ_boundary() is None:
            print "Using electric wall boundary."
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].bc.type = 1"+"\n"
        else:
            if get_circ_boundary().lower() == 'metal' or get_circ_boundary().lower() == 'electric wall':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].bc.type = 1"+"\n"
            elif get_circ_boundary().lower() == 'magnetic wall':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].bc.type = 2"+"\n"
            elif get_circ_boundary().lower() == 'periodic':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].bc.type = 3"+"\n"
            elif get_circ_boundary().lower() == 'transparent':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].bc.type = 4"+"\n"
            elif get_circ_boundary().lower() == 'impedance':
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].bc.type = 5"+"\n"
            else:
                print('Invalid input to set_circ_boundary()')
        
        
        # set solver parameters
        if self.bend_radius == 0:
            hcurv = 0
        else:
            hcurv = 1.0/self.bend_radius
        wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.hcurv={"+str(hcurv)+"}"+"\n"

        #autorun & speed:
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
                print 'Inalid horizontal_symmetry. Please use: none, ExSymm, or EySymm'

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
                print 'Inalid horizontal_symmetry. Please use: none, ExSymm, or EySymm'

        wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.maxnmodes={"+str( get_N() )+"}"+"\n"

        wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.nx={"+str( get_NX() )+"}"+"\n"
        nx_svp = get_NX()

        wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.ny={"+str( get_NY() )+"}"+"\n"
        ny_svp = get_NY()

        wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.mintefrac={"+str( get_min_TE_frac() )+"}"+"\n"
        
        wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.maxtefrac={"+str(max_TE_frac())+"}"+"\n"
        
        if get_min_EV() is None:
            '''Default to -1e50'''
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.evend={-1e+050}"+"\n"
        else:
            wgStrint += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.mlp.evend={"+str(get_min_EV())+"}"+"\n"
        
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

        if get_mode_solver() is None:
            print 'Using Default Mode Solver: "Vectorial FDM Real"  '
            wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=192"+"\n"
            solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V1 "+str(n1d_svp)+" "+str(0)+" "+str( get_N() )+" "+str( 1 )+" "+str( get_Np() )+" "+"\n"
        else:
            if get_mode_solver().lower() == 'Vectorial SMF'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=50"+"\n"
                solverString = "\n"
            elif get_mode_solver().lower() == 'SemiVecTE SMF'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=18"+"\n"
                solverString = "\n"
            elif get_mode_solver().lower() == 'SemiVecTM SMF'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=34"+"\n"
                solverString = "\n"
            elif get_mode_solver().lower() == 'Vectorial Gaussian'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=53"+"\n"
                solverString = "\n"
            elif get_mode_solver().lower() == 'SemiVecTE Gaussian'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=21"+"\n"
                solverString = "\n"
            elif get_mode_solver().lower() == 'SemiVecTM Gaussian'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=37"+"\n"
                solverString = "\n"
            elif get_mode_solver().lower() == 'Vectorial GFS Real'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=68"+"\n"
                solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V1 "+str( get_Nm()[0] )+" "+str( get_Nm()[1] )+" "+str( get_Np()[0] )+" "+str( get_Np()[1] )+" "+"\n"
            elif get_mode_solver().lower() == 'Scalar GFS Real'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=4"+"\n"
                solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V1 "+str( get_Nm()[0] )+" "+str( get_Nm()[1] )+" "+str( get_Np()[0] )+" "+str( get_Np()[1] )+" "+"\n"
            elif get_mode_solver().lower() == 'Vectorial FDM real'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=192"+"\n"
                solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V1 "+str(n1d_svp)+" "+str( get_Nm()[0] )+" "+str( get_Nm()[1] )+" "+str( get_Np()[0] )+" "+str( get_Np()[1] )+" "+"\n"
            elif get_mode_solver().lower() == 'Vectorial FDM complex'.lower():
                wgString += "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.solvid=200"+"\n"
                solverString = "app.subnodes["+str(self.parent.num)+"].subnodes["+str(self.num)+"].evlist.svp.buff=V1 "+str(n1d_svp)+" "+sstr( get_Nm()[0] )+" "+str( get_Nm()[1] )+" "+str( get_Np()[0] )+" "+str( get_Np()[1] )+" "+"\n"
            else:
                print 'Invalid Cylindrical Mode Solver. Please see `help(pyfimm.set_mode_solver)`, and use one of the following options :'
                print 'Finite-Difference Method solver: "vectorial FDM real" , "vectorial FDM complex",'
                print 'General Fiber Solver: "vectorial GFS real" , "scalar GFS real",'
                print 'Single-Mode Fiber solver: "Vectorial SMF" , "SemivecTE SMF" , "SemivecTM SMF",'
                print 'Gaussian Fiber Solver (unsupported): "Vectorial Gaussian" , "SemivecTE Gaussian" , "SemivecTM Gaussian".'
                raise ValueError("Invalid Modesolver String: " + str(get_mode_solver()) )

        wgString += solverString
        fimm.Exec(wgString)
        
        self.built=True
    #end buildCyl()
    
    
    
    
#end class Slice



############################################
####        Cylindrical Functions       ####
############################################

############################################
####        Mode Solver Parameters      ####
############################################

def set_circ_pml( w ):
    '''Set with of PML (Perfectly Matched Layer) for cylindrical waveguides.'''
    global global_circ_pml
    global_circ_pml = w
    
def get_circ_pml():
    '''Get width of cylindrical PML (Perfectly Matched Layer).  '''
    global global_circ_pml
    try:
        global_circ_pml
    except NameError:
        global_circ_pml = None
    return global_circ_pml

def set_pml_circ(w):
    '''Backwards compatibility only.  Should instead use set_circ_pml.'''
    print "Deprecation Warning:  set_pml_circ():  Use set_circ_pml() instead."
    set_circ_pml(w)
    
def get_pml_circ():
    '''Backwards compatibility only.  Should instead use get_circ_pml.'''
    print "Deprecation Warning:  get_pml_circ():  Use get_circ_pml() instead."
    return get_circ_pml()


def set_circ_boundary(type):
    '''Set boundary type of cylindrical waveguide.
    Default value, if unset, is 'electric wall'.
    
    Parameters
    ----------
    type : string { 'electric wall' | 'magnetic wall' | 'periodic' | 'transparent' | 'impedance' }
    '''
    possibleArgs = ['electric wall' , 'metal', 'magnetic wall' , 'periodic' , 'transparent' , 'impedance']
    exists = len(   np.where(  np.array( type ) == np.array( possibleArgs)  )[0]   )
    if not exists: raise ValueError("Allowed arguments are: 'electric wall' (aka. 'metal') | 'magnetic wall' | 'periodic' | 'transparent' | 'impedance' ")
    type=type.lower()
    if type == 'metal':
        type = 'electric wall' 
        print "set_circ_boundary('metal'): setting `type` to synonym 'electric wall'."
    global global_CBC
    global_CBC = type.lower()

def get_circ_boundary():
    '''Get boundary type for cylindrical waveguides.
    See `help(pyfimm.set_circ_boundary)` for more info.
    
    Returns
    -------
    type : string { 'electric wall' | 'magnetic wall' | 'periodic' | 'transparent' | 'impedance' }
    '''
    global global_CBC
    try:
        global_CBC
    except NameError:
        global_CBC = None
    return global_CBC
    
#def circ_boundary():
#    '''Backwards compatibility only.  Should Instead get_circ_boundary().'''
#    print "Deprecation Warning:  circ_boundary():  Use get_circ_boundary() instead."
#    return get_circ_boundary()

def get_Nm():
    '''For General Fiber Solver (GFS) or Fibre FDM solver, set (min,max) of m-order (azimuthal/axial quantum number) modes to solve for. 
    This is the Theta mode number - how many nodes/how fast the fields vary in the Theta direction.
    m goes from 0 -> infinity.
    
    See "GFS Fibre Solver"/"buff" params or Sec. 5.7.3 in fimmwave manual.
    
    Returns
    -------
    nm : 2-element tuple
        (nm_min, nm_max): min & max m-order.  Defaults to (0,1) if unset.'''
    global global_Nm
    try:
        global_Nm
    except NameError:
        global_Nm = (0,1)       # the default value
    return (global_Nm[0],global_Nm[1])

def set_Nm(nm):
    '''For General Fiber Solver (GFS) or Fibre FDM solver, set (min,max) of m-order (azimuthal/axial quantum number) modes to solve for. 
    This is the Theta mode number - how many nodes/how fast the fields vary in the Theta direction.
    m goes from 0 -> infinity.
    
    See "GFS Fibre Solver"/"buff" params or Sec. 5.7.3 in fimmwave manual.
    
    Parameters
    ----------
    nm : integer, OR tuple/list (any iterable) of 2 integers
        (min_nm, max_nm): min & max m-orders to solve.  Defaults to (0,1)
    
    
    Examples
    --------
    >>> set_Nm(0)
        Solve only for m-order=0, which has no nulls in the theta direction.
    >>> set_Nm( [0,10] )
        Solve for m-orders 0-10.
    '''
    if isinstance(nm, int): 
        nm = list([nm]) # convert an integer to list
    else:
        nm = [int(x) for x in nm]   # make sure all args convert to integer, and generate list
    
    if len(nm) == 1: nm.append(nm[0])   # set second element to same val as first
    if len(nm) != 2: raise ValueError("`nm` must have two indices: (nm_min, nm_max)")    # check args for errors
    if (nm[0] < 0) or (nm[1] < 0):
        ErrStr = "set_Nm(): m-order must be 0 or greater."
        raise ValueError(ErrStr)
    global global_Nm
    global_Nm = nm


def get_Np():
    '''For General Fiber Solver (GFS) or Fibre FDM solver, set (min,max) number of p-order (polarization number) modes to solve for.  Use set_N() to determine m-order (axial quantum number) modes. 
    
    See Sec. 5.7.3 of the FimmWave manual.
    
    Returns
    -------
    np : 2-element tuple
        (np_min, np_max): min & max p-order.  Defaults to (1,2) if unset.'''
    global global_Np
    try:
        global_Np
    except NameError:
        global_Np = (1,2)       # the default value
    return (global_Np[0],global_Np[1])

def set_Np(np):
    '''For General Fiber Solver (GFS) or Fibre FDM solver, set max number of p-order (axial/azimuthal quantum number) modes to solve for.
    This is the main polarization number, `p`. For GFS, p=1 means selecting mode with Ex=0, while p=2 means Ey=0.
    For Semi-Vectorial GFS, `p` can also be 3 or 4 if m>=1 (see manual for info).
    
    See Sec. 5.7.3 of the FimmWave manual, or `help(pyfimm.set_mode_solver)` as some cylindrical mode solvers have constraints on the p-order.
    
    Parameters
    ----------
    np : integer, OR tuple/list (any iterable) of 2 integers
        (min_np, max_np): min & max p-orders to solve.  Defaults to (1,2) if unset.
    
    Examples
    --------
    >>> set_Np(1)
        Solve only for 1st p-order, which is main E-field in Ey I think.
    >>> set_Np( [1,4] )
        Solve for p-orders 1-4.
    '''
    if isinstance(np, int): 
        np = list([np]) # convert an integer to list
    else:
        np = [int(x) for x in np]   # make sure all args convert to integer, and generate list
        
    if len(np) == 1: np.append(np[0])   # set second element to same val as first
    if len(np) != 2: raise ValueError("`np` must have two indices: (np_min, np_max)")    # check args for errors
    if (np[0] < 1) or (np[1] > 4):
        ErrStr = "set_Np(): p-order must be betwen 1 and 4."
        raise ValueError(ErrStr)
    global global_Np
    global_Np = np
