'''Tapered waveguide classes, part of pyFIMM.'''

from __pyfimm import *       # import the main module (should already be imported), includes many 'rect' classes/funcs

from __globals import *         # import global vars & FimmWave connection object

from __Mode import *            # import Mode class
from __Waveguide import *       # import Waveguide class
from __Circ import *            # import Circ class

#from __pyfimm import DEBUG()        # Value is set in __pyfimm.py

from numpy import inf              # infinity, for hcurv/bend_radius
import numpy as np              # math


class Taper(Node):
    """Taper( LHS, RHS, [Length, Method] )
    
    pyFimm Taper object, a way of forming waveguides that vary in Z.  
    The taper takes a "start" waveguide and "end" waveguide and varies between the two over the Z length.  Internally, FimmProp slices it up and creates new waveguides at each slice with slight variation as specified.
    
    This inherits from the pyFIMM Node object.
    
    
    Parameters
    ----------
    LHS : Waveguide or Circ object
        WG node to begin the taper with.
    
    RHS : Waveguide or Circ object
        WG node to begin the taper with. 
    
    length : float, optional
        length of the lens.  May be omitted, and instead set when Called as part of Device construction.
    
    method : { 'full' }, optional
        Defaults to 'full'
    
    Methods
    -------
    
    This is a partial list - see `dir(Taper)` to see all methods.
    Please see help on a specific function via `help(Taper)` for detailed up-to-date info on accepted arguments etc.
    
    """
    def __init__(self,*args):
        if len(args) >=1:
            self.autorun = True     # unused?
            self.name=None     # unused?
            self.built=False     # unused?
            self.length=0.0     # unused?
            self.__materialdb = None     # unused?
    
        if len(args) == 2:
            self.type = 'taper'
            self.lhs = args[0].name
            self.rhs = args[1].name
            self.length = 1
            self.method = 'full'
        elif len(args) == 3:
            self.type = 'taper'
            self.lhs = args[0].name
            self.rhs = args[1].name
            self.length = args[2]
            self.method = 'full'
        elif len(args) == 4:
            self.type = 'taper'
            self.lhs = args[0].name
            self.rhs = args[1].name
            self.length = args[2]
            self.method = args[3]
        else:
            'Invalid number of inputs to Taper()'

    def __call__(self,width):
        '''Replace with Section() returned?'''
        self.length = width
        return [self]

    def __add__(self,other):
        return [self,other]
    
    def set_joint_type(self, jtype, jointoptions=None):
        '''Set the joint type after this waveguide, if used in a Device.
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
    
    
    def buildNode(self):
        '''This may not make sense - only able to be built in a FimmProp Device.'''
        print "Warning: Tapers & WGLenses are only built within a FimmProp Device, not as stand-alone components. Nothing done for Taper.buildNode()."
    
    def get_buildNode_str(self, nodestring):
        '''Return the string needed to build this Taper.'''
        pass

#end class Taper



class Lens(Node):
    '''Waveguide Lens, an element of a FimmProp Device.  See FimmProp Manual sec. 4.3.10.
    
    >>> NewLensObj = Lens(wgbase, radius [,optional kwargs] )
    >>> NewLensObj.set_diameter( 20.0 )
    >>> NewLensObj.set_type( 'polish' )
    >>> DeviceObj = <pyfimm>.Device(  WG1(100) + WG2(50.0) + NewLensObj(5.0)  )
    
    
    Parameters
    ----------
    wgbase : Waveguide or Circ object
        The lens will reference this WG object/node & deform it in the manner specified.
    
    radius : float, required
        Radius of curvature of this lens.
    
    
    Optional Keyworded Arguments
    ----------------------------
    
    side : { 'left' | 'right' }, optional
        Which side of the element should have the curvature/lens applied.  Defaults to curvature on the Right side.
    
    type : {'distortion' | 'polish convex' | 'polish concave'}, optional
        Which method to create taper with.  Defaults to 'distortion', which distorts the passed WG into a lens. Polish instead removes parts of the structure to create the curved surface, but all interfaces in the WG remain straight.
    
    diameter : float, optional
        Diameter to distort, if not the entire WG diameter.  This is the chord length of widest part of lens.  If omitted, will use d1 & d2
    
    d1 : float, optional
        distance from bottom of WG to leave undistorted, if `diameter` not specified.  Defaults to 0.
    
    d2 : float, optional
        distance from top of WG to leave undistorted, if `diameter` not specified.  Defaults to 0.
    
    etchDepth : float, optional
        For Rect. WG: specify an etch depth for regions outside the lens region.
    
    fill_index : float, optional
        For Rect. WG: specify refractive-index to fill etched regions with.
    
    minStepSizeFrac : float, optional
        Minimum integration step size.  Defaults to 0.01.
         
    tolerance : float, optional
        Integration tolerance. Defaults to 0.01.
    
    joint_method {'complete', 'special complete', 'normal fresnel', oblique fresnel'}, optional, case insensitive
        What type of joint/overlap calculation method to use in between the discretized (chopped-up) taper sections.
    
    integration_order : { 0 | 1 }
        Zero- or first-order integration.
    
    enableEVscan : { True | False}
        Enable mode scanner. True by default. 
    
    
    Methods
    -------
    
    This is a partial list - see `dir(Lens)` to see all methods.
    Please see help on a specific function via `help(Lens)` for detailed up-to-date info on accepted arguments etc.
    
    '''
    
    '''
    TO DO
    
    Make sure the 'length' attribute is passed on to the Section - for all inputs to Section.
    '''
    def __init__(self,wgbase, radius, **kwargs):
        #if len(args) >=0:
        #self.name=None     # unused?
        #self.length=0.0     # unused?
        #self.__materialdb = None     # unused?
        self.bend_radius = inf    # inf means straight
        self.built=False     
        self.autorun = True     
        
        #if len(args) == 1:
        self.type = 'wglens'    # unused!
        self.radius = radius     # radius of curvature of the taper
        self.wgbase = wgbase  # waveguide object
        if isinstance( self.wgbase, Circ):
            if len(self.wgbase.layers) < 2:
                ErrStr = "Circ objects must have 2 or more layers to be converted into lenses."
                raise UserWarning(ErrStr)
        #elif len(args) == 2:
        #    self.type = 'wglens'
        #    self.wgbase = wgbase
        #    self.length = args[1]
        #else:
        #    raise ValueError('Invalid number of inputs to WGLens().  See `help(pyfimm.WGLens)`.')
        
        # find keyworded args, with defaults provided:
        self.lens_type = str(  kwargs.pop( 'type', 'distortion')  ).lower()
        self.side = str(  kwargs.pop( 'side', 'right' )  ).lower()

        #self.R = kwargs.pop( 'radius', None )
        #if self.R: self.R = float(self.R)

        self.D =  kwargs.pop( 'diameter', None )
        if self.D != None: self.D = float(self.D)

        self.d1 =  kwargs.pop(  'd1', None )
        if self.d1 != None: self.d1 = float(self.d1)

        self.d2 =  kwargs.pop(  'd2', None )
        if self.d2 != None: self.d2 = float(self.d2)

        self.minSSfrac = float(  kwargs.pop(  'minStepSizeFrac', 0.01 )  )
        self.tolerance = float(  kwargs.pop( 'tolerance', 0.01 )  )
        
        self.etchdepth =  kwargs.pop( 'etchDepth', None )
        if self.etchdepth != None: self.etchdepth = float(self.etchdepth)

        self.fillRIX = kwargs.pop(  'fill_index', None ) 
        if self.fillRIX != None: self.fillRIX = float(self.fillRIX)
        
        self.joint_method = kwargs.pop(  'joint_method', None )
        self.int_method = kwargs.pop(  'integration_order', None )
        self.enableevscan = kwargs.pop(  'enableEVscan', True )
        
        #self.name = str(  kwargs.pop( 'name', 'WGlens' )
        #overwrite = bool( kwargs.pop( 'overwrite', False )
        #self._checkNodeName(
        #self.parent = kwargs.pop( 'parent', None )
        
        if kwargs:
            '''If there are unused key-word arguments'''
            ErrStr = "WARNING: Lens(): Unrecognized keywords provided: {"
            for k in kwargs.iterkeys():
                ErrStr += "'" + k + "', "
            ErrStr += "}.    Continuing..."
            print ErrStr
    #end __init__
    
    
    def __call__(self,):
        '''Calling a Taper object with one argument creates a Section of passed length, and returns a list containing this new Section.
            Usually passed directly to Device in the list of WG's as so:
            >>> Device(  WG1(10.5) + Lens1() + WG3(10.5)  )
            or 
            >>> Device(  WG1(50.0) + Taper1(200.0) + WG3(75.0)  )
        '''
        
        # Always call Section with 1 args
        out = [   Section(  self, self.get_length()  )   ]
        return out
    
    
    def __add__(self,other):
        '''If addition used, return list with this dev prepended'''
        return [self,other]
    
    
    def get_length(self):
        '''Return the length in Z of this lens'''
        # TO DO: match up this result with fimmwave's length result
        if isinstance( self.wgbase, Waveguide):
            w = self.wgbase.get_width()
        elif isinstance( self.wgbase, Circ):
            w = 2 * self.wgbase.get_radius()
        r = self.radius
        return r - r*np.sin(  np.arccos(w/2/r)  )
    
    def set_diameter(self, diam):
        '''Set diameter, D'''
        self.D = diam
    
    def get_diameter(self):
        '''Get diameter, D'''
        return self.D
    
    def set_type(self, type):
        '''Type of Lens. 
        
        Parameters
        ----------
        type : { 'distortion', 'polish convex', 'polish concave' }
            Which method to create taper with.  Defaults to 'distortion', which distorts the passed WG into a lens. Polish instead removes parts of the structure to create the curved surface, but all interfaces in the WG remain straight.
        '''
        self.lens_type = type
    
    def get_type(self):
        '''Return the Lens type, one of: { 'distortion', 'polish convex', 'polish concave' }'''
        return self.lens_type
    
    def set_joint_type(self, jtype, jointoptions=None):
        '''Set the joint type after this waveguide, if used in a Device.
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
            
            Examples
            --------
            >>> Waveguide1.get_joint_type()
            >   'complete'
            
            >>> Waveguide1.get_joint_type( True )
            >   0
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
    
    
    ''' 
    *********************
    ****    TO DO   *****
    *********************
    Still need to implement get/set:
    set_side, set_... d1, d2, etchDepth, fill_index, joint_method etc.'''
    
    
    #############################
    ####    Node Builders    ####
    #############################
    
    def buildNode(self):
        '''This does not make sense - only able to be built/inserted in a FimmProp Device.'''
        print "Warning: Tapers & WGLenses are only built as part of a FimmProp Device, not as stand-alone components. Nothing done for WGLens.buildNode()."
    
    
    def get_buildNode_str(self, nodestring):
        '''Return the string needed to build this node.  
        `nodestring` should be the full FimmProp nodestring to reference the element in the Device, eg. 
            "app.subnodes[1].subnodes[3].cdev.eltlist[5]"
            '''
        
        if isinstance( self.wgbase, Waveguide ):
            type='rect'         # these 'types' are currently unused
        elif isinstance( self.wgbase, Circ ):
            type='cyl'
        else:
            ErrStr = "Unsupported object passed for basis waveguide of Lens, with type `%s`.  "%(type(self.wgbase) + "Please pass a Waveguide or Circ object.")
            raise ValueError(ErrStr)
        
        fpstring = ""
        
        fpstring += nodestring + ".svp.lambda=" + str( get_wavelength()  ) + "   \n"
        
        if self.bend_radius == 0:
            self.bend_radius = inf
            print "Warning: bend_radius changed from 0.0 --> inf (straight waveguide)"
            hcurv = 0
        elif self.bend_radius == inf:
            hcurv = 0
        else:
            hcurv = 1.0/self.bend_radius
        #hcurv = 1/self.bend_radius
        fpstring += nodestring + ".svp.hcurv=" + str(hcurv) + "   \n"
        
        fpstring += self.wgbase.get_solver_str(nodestring, target='wglens')
        
        # which side of element should be lensed:
        if self.side == 'left':
            i = 0
        elif self.side == 'right':
            i = 1
        else:
            ErrStr = 'Invalid side for lens; please use "left" or "right" (default).'
            raise ValueError(ErrStr)
        fpstring += nodestring + ".which_end = " +str(i) + "   \n"
        
        
        # which type of lens
        if self.lens_type.lower() == 'distortion':
            i = 0
        elif self.lens_type.lower() == 'polish convex':
            i = 1
        elif self.lens_type.lower() == 'polish concave':
            i = 2
        else:
            ErrStr = 'Invalid option for lens type; please use "distortion" (default) or "polish convex" or "polish concave".'
            raise ValueError(ErrStr)
        fpstring += nodestring + ".lens_type = " +str(i) + "   \n"
        
        
        if self.D:
            fpstring += nodestring + ".D = " +str(self.D) + "   \n"
        
        if self.d1:
            fpstring += nodestring + ".d1 = " +str(self.d1) + "   \n"
        
        if self.d2:
            fpstring += nodestring + ".d2 = " +str(self.d2) + "   \n"
        
        if self.etchdepth:
            fpstring += nodestring + ".etchdepth = " +str(self.etchdepth) + "   \n"
        
        if self.fillRIX:
            fpstring += nodestring + ".fillrix = " +str(self.fillRIX) + "   \n"
        
        # discretization options:
        fpstring += nodestring + ".minSTPfrac = " +str(self.minSSfrac) + "   \n"
        fpstring += nodestring + ".tolerance = " +str(self.tolerance) + "   \n"
        
        if self.joint_method:
            if self.joint_method.lower() == 'complete':
                fpstring += nodestring + ".joint_method = " +str(0) + "   \n"
            elif self.joint_method.lower() == 'special complete':
                fpstring += nodestring + ".joint_method = " +str(3) + "   \n"
            elif self.joint_method.lower() == 'normal fresnel':
                fpstring += nodestring + ".joint_method = " +str(1) + "   \n"
            elif self.joint_method.lower() == 'oblique fresnel':
                fpstring += nodestring + ".joint_method = " +str(2) + "   \n"
            else:
                ErrStr = "Invalid option for Taper Joint Method `%s`" %self.joint_method
                raise ValueError(ErrStr)
        
        if self.int_method:
            fpstring += nodestring + ".int_method = " +str(self.int_method) + "   \n"
        
        if self.enableevscan == False:
            i=0
        else:
            i=1
        fpstring += nodestring + ".enableevscan = " +str(i) + "   \n"
        
        fpstring += nodestring + ".R = " +str(self.radius) + "   \n"
        
        return fpstring
#end class WGLens
    
    
    