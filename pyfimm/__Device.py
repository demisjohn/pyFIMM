'''Device class, part of pyFIMM.'''

from __globals import *         # import global vars & FimmWave connection object
# DEBUG() variable is also set in __globals, & numpy as np & pyplot as plt

from __pyfimm import *      # import the main module (should already be imported)
#  NOTE: shouldn't have to duplicate the entire pyfimm file here!  Should just import the funcs we need...

from __Waveguide import Waveguide   # rectangular waveguide class
from __Circ import Circ        # cylindrical (fiber) waveguide class
from __Tapers import Taper,Lens      # import Taper/WGLens classes
from __Mode import Mode     # import Mode class


## Moved to __globals.py:
#import numpy as np      # array math etc.
#import matplotlib.pyplot as plt     # plotting - to get a new figure



class Device(Node):
    """Device( elements )
    The Device class constructs a FIMMProp Device, for propagating through multiple waveguides.
    A Device Node contains multiple waveguide components (with lengths or paths) stitched together.
    By default the waveguides are joined by the Simple Joint type, and parameters are inherited from the Device node.
    Inherits from the Node class - see help on pyFIMM.Node for member functions/properties.
    
    Please type `dir(DeviceObj)` or `help(DeviceObj)` to see all the attributes and methods available.
    
    
    Parameters
    ----------
    elements : List of { Waveguide object | Circ objects }
    
    
    Attributes
    ----------
    elements : list
        List containing Waveguide, Circ, Taper or other waveguide-type objects.  The Device is constructed from left-to-right starting at elements[0].
        You can interrogate these element objects as well, eg. DeviceObject.elements[0].length = 2.50 etc. 
    
    name : string
        Name of this Device in fimmwave Node.
        
    built : { True | False }
        Whether or not this Device has been built in Fimmwave via buildNode().
    
    origin : { 'pyfimm' | 'fimmwave' }
        Indicates whether this Device was built using pyFIMM, or was constructed in FimmWave & imported via `import_device()`.
    
    After Device.buildNode() has been called, the following become available:
    
    num : int
        FimmWave Node number for this device
    
    nodestring : string
        String used to access this Device node in fimmwave, for example: "app.subnodes[1].subnodes[3]"
    
    elementpos : list
        List containing integers, indicating position (eltlist[position]) that each element was inserted into in the fimmwave Device.
    
    jointpos : list
        List containing integers, indicating position (eltlist[position]) of the simple joints in the fimmwave Device.
    
    
    Methods
    -------
    
    This is a partial list - see `dir(pf.Device)` to see all methods.
    Please see help on a specific function via `help(pf.Device)` for detailed up-to-date info on accepted arguments etc.
    
    set_input_field( vector , side=None)
        Set the input field with a vector specifying the amplitudes (complex) of each mode to launch.
        vector should be a list with same length as `get_N()`, number of modes.
        side specifies which side to launch on, 'left' or 'right'
        set_inc_field() is a synonym.
    
    set_joint_type(type)
        Set the type of FimmProp joint to use between all waveguides in this Device.
    
    get_joint_type(type)
        Get the type of FimmProp joint to use between all waveguides in this Device.
    
    
    Examples
    --------
    Call Device similar to Slice() or Waveguide():
    >>> dev1 = Device(  WG1(100.0) + WG_Air(10.0) + WG2(100.0)  )
    This concatenates the structure WG1 (elongated by 100um) to WG_Air (10um long) and WG2 (100um long).
    The waveguide types can be any pyFIMM supported type, such as Waveguide (rectangular coords), or Circ (cylindrical coords).
    
    Mode solver options are available for each type.
    
    To Do:
    ------
    - Add support for Tapers/WGLenses
    - Add support for Input/Output ports, eg. Device( IOPort1() + WG1(100.0) + IOPort2() )
    - Input Device objects (one nesting layer only) and construct node from constituent elements of each Device object.
    - add suport for Paths (eg. non-straight WG's) - Done, use `import_device()`
    
    """
    def __init__(self,*args):
        #if DEBUG(): print "Device Constructor: args=\n", args
        if DEBUG(): print "Device Constructor: " 
        if DEBUG() and len(args) > 0:  print str( len(args[0]) )  + " elements passed."
        self.origin = 'pyfimm'   # Device was constructed in pyFIMM
        self.name = None
        self.calculated= False   # has this Device been calculated yet?
        self.built=False        # has the Dev been build in FimmProp?
        self.input_field_left = None     # input fields
        self.input_field_right = None
        self.__wavelength = get_wavelength()    # get global wavelength
        self.__inc_field = None     # incident/input field - DEPRECATED
        self.elementpos = []    # positions in eltlist[] of each element/joint
        self.jointpos = []

        if len(args) == 1:
            self.lengths = []
            self.elements = []
            for i in range(len(args[0])):
                '''a [list] of Section objects is passed (created by the __add__ method of the Section class).
                each Section object has the attribute SectionObj.WG which is the original Waveguide/Circ object.
                the `length` attribute is set in the Section when the WGobj is called with an argument (the __call__ method of the WG Object).'''
                self.elements.append( args[0][i].WG )
                self.lengths.append( args[0][i].get_length() )
                #if DEBUG(): print "\nElements=\n", self.elements, "\nLengths=\n", self.lengths
        elif len(args) == 0:
            self.lengths = []
            self.elements = []
        else:
            raise ValueError('Invalid number of arguments to Device()')
    
    def __str__(self):
        '''How to `print()` this object'''
        string=""
        if self.name: string += "Name: '"+self.name+"'\n"
        string += 'Total Length = %7.4f \n' % self.get_length()
        for i,el in enumerate(self.elements):
            if i == 0:
                string += 6*'*' + ' Left-Hand Section ' + 6*'*' + '\nlength = %7.4f \n' % self.lengths[i] + '\n%s' % (el) + '\n'
            elif i == (len(self.elements)-1):
                string += 6*'*' + ' Right-Hand Section ' + 6*'*' + '\nlength = %7.4f \n' % self.lengths[i] + '\n%s' % (el) + '\n'
            else:
                string += 6*'*' + ' Middle Section %i ' % i + 6*'*' + '\nlength = %7.4f \n' % self.lengths[i] + '\n%s' % (el) + '\n'
        return string
    #end __str__
    
    
    def __len__(self):
        '''Number of elements in this Device.'''
        return len(self.elements)    
    
    def __call__(self):
        '''Calling a Device object creates a Section of passed length, and returns a list containing this new Section.
            Usually passed directly to Device as so:
            >>> NewDevice = pyfimm.Device(  DeviceObj() + WG2(1.25) + WG3(10.5)  )
        '''
        # Instantiate a Section obj with 1 args
        out = [   Section(  self  )   ]
        return out
    
    def __add__(self, other):
        '''To Do: Allow devices to be added together, concatenating their elements.'''
        raise Error("Device addition currently unsupported.")
    
    def get_origin(self):
        '''Return 'pyfimm' if this Device was constructed in pyFIMM, or 'fimm' if the Device was constructed in FimmProp.
        Dev's constructed in pyFIMM will have a list of elements, which reference pyFIMM waveguide objects etc.  Dev's constructed in FimmProp will not have such properties, but can take advantage of FimmProp's GUI construction, etch/grow paths and other functionality not achievable in pyFIMM.'''
        return self.origin
    
    def get_length(self):
        '''Return summed lengths of contained elements - total length of this Device.'''
        return np.sum(self.lengths)
    
    def set_length(self,element_num,length):
        '''Set the length of a particular element in the Device.  (Elements are counted from the left-most side first, starting at #1.)  
            element_num : int
                The element to modify.
            length : float
                The new length of the selected element.
        '''
        #prj_num = self.parent.num
        #node_num = self.num
        #app.subnodes[{"+ str(prj_num) +"}].subnodes[{"+ str(node_num) +"}]
        fimm.Exec( self.nodestring + ".cdev.eltlist[{"+ str(int(element_num)) +"}].length={"+ str(float(length)) +"}" )
    
    
    def calc(self, zpoints=3000, zmin=0.0, zmax=None, xcut=0.0, ycut=0.0):
        '''Calculate the fields (E, H, P, I, Refr.Index) along Z in the Device.
        You should do this before using `get_fields()`, `get_refractive_index()` or `plot()` or similar functions, or set the `calc=True` option in those functions.
        This function doesn't return anything, but just causes Fimmwave to internally calculate these parameters.
        
        Parameters
        ----------
        xcut, ycut = float, optional
            x & y coords at which to cut the Device along Z.  Both default to 0.
        
        zpoints = integer, optional
            Number of points to acquire in the field.  Defaults to 3000.
        
        zmin, zmax = float, optional
            min & max z-coorinates. Defaults to 0-->Device Length (plot entire Device).
        
        '''
        #prj_num = self.parent.num
        #node_num = self.num
        #"app.subnodes[{"+ str(prj_num) +"}].subnodes[{"+ str(node_num) +"}]."
        if not zmax: zmax = self.get_length()
        fimm.Exec(self.nodestring + ".calczfield("+ str(zpoints) +","+ str(zmin) +", "+ str(zmax) +","+ str(xcut) +","+ str(ycut) +",1)"    +"\n")
        self.calculated=True
    #end calc()
    
    
    def set_joint_type(self, jtype, jointoptions=None):
        '''Set the joint type to use between each element of this Device.  This option, if set, overrides each element's own options for the joint type (set by `element.set_joint_type()`).
        
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
        Get the joint type that will be placed between each waveguide in this Device.  
        
            asnumeric : boolean, optional
                A True value will cause the output to be numeric, rather than string.  See help(set_joint_type) for the numerical/string correlations.  False by default.
                (FYI, `asnumeric=True` is used in Device.buildNode()  )
        
        Returns
        -------
        The joint type as a string, or as integer if `asnumeric` was True.
        If unset, returns `None` (regardless of `asnumeric`), in which case the element's settings for joint-type will be used (`element.get_joint_type()`).
        '''
        try:
            self.__jointtype    # see if variable exists
        except AttributeError:
            # if the variable doesn't exist yet.
            if DEBUG(): print "unset " + self.name + ".__jointtype --> None   "
            self.__jointtype = None
        
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
            elif self.__jointtype == None:
                out= None
        #if DEBUG(): print "get_joint_type(): ", out
        return out
    #end get_joint_type()
    
    def unset_joint_type(self):
        '''Unset the Device-level joint type, so each element's settings will be used instead.
        `DeviceObj.get_joint_type()` will consequently return `None`.'''
        self.__jointtype = None
    
    def set_wavelength(self, wl):
        '''Set the wavelength for the entire Device.  Elements will all use this wavelength in their MOLAB options.
        Note that, after building, the Device wavelength (`DeviceObj.get_wavelength()` ) can be different from the global pyFIMM wavelength (`pyFIMM.get_wavelength`).
        The global setting (`pyFIMM.set_wavelength()`) is acquired when the object is first created.
                
        Parameters
        ----------
        wl : float
            The wavelength in micrometers.
        '''
        
        if self.built:
            self.__wavelength = float(wl)
            fimm.Exec(  self.nodestring + ".lambda = " + str(self.__wavelength) + "   \n"  )
        else:
            self.__wavelength = float(wl)
    
    
    def get_wavelength(self):
        '''Return the wavelength (float) for this specific Device (may be different from the global pyFIMM wavelength in `pyFIMM.get_wavelength()` after the Device is built).'''
        return self.__wavelength
    
    
    def set_input(self,mode_vector, side=None, normalize=False, warn=True):
        '''Set input ("incident") field vector - takes a list with amplitude coefficients (complex) for each mode number, as entered into the "Vector" mode of the "View > Set Input" menu of a FimmWave Device.
        `set_inc_field()` is an alias to this function.
        
        Parameters
        ----------
        mode_vector : array-like or integer
            To set the input as a vector (list of mode amplitudes), pass a List of complex amplitudes for each mode's excitation amplitude/phase.  Length of amplitude-list must equal the number of lateral modes, get_N() (ie. every mode of the waveguide should have a specified amplitude).
            To set the input as just a modenumber, pass an integer.
            To turn off an input, pass `None`.
        
        side : { 'left' | 'right' }, required, case-insensitive
            Which side to inject fields into.  The string "LHS" (left-hand side) or "RHS" (right-hand side) should be used. Synonyms for "LHS" are "left" and "L", and correspondingly for "RHS" the synonyms are "right" and "R".
            Defaults to 'LHS' for backwards compatibility.
        
        normalize : boolean, optional
            Tell fimmwave to normalize the input vector (just sets the "normalize" flag in the `Set Input` Window).  Default = False.
        
        warn : Boolean
            Print warning messages?  True by default.
        
        
        Use `get_input_field()` to return the currently set input for the Device.
        
        
        Examples
        --------
        For a device names 'Dev1', with set_N() set to 5 (five modes calculated), set the input field to inject only the first mode, into the right-hand side of the device, as so:
            >>> Dev1.set_input_field( [1,0,0,0,0], side='right')
        To turn off the input on the left side, do:
            >>> Dev1.set_input_field( [0,0,0,0,0], side='left')
        or, equivalently:
            >>> Dev1.set_input_field(   numpy.zeros( pyFIMM.get_N() )   , side='left')
        
        '''
        
        if side == None:
            side='lhs'  # default value if unset
            if warn: print "WARNING: Device '%s'.set_input_field():"%self.name + " set to Left-Hand-Side input, since unspecified."
        else:
            side = side.lower().strip()     # make lower case, strip whitespace
        
        if (side == 'lhs') or (side == 'left') or (side == 'l'):
            sidestr = 'lhs'
            self.input_field_left = mode_vector
        elif (side == 'rhs') or (side == 'right') or (side == 'r'):
            sidestr = 'rhs'
            self.input_field_right = mode_vector
        else:
            ErrStr = "Device '%s'.set_input_field(): "%self.name + "Unsupported side passed: `" + str(side) + "`.  \n\tPlease use 'Left' or 'Right', or see `help(pyfimm.Device.set_input_field)`."
            if DEBUG(): print "side.lower() = ", side.lower()
            raise ValueError(ErrStr)

        '''
        prj_num = self.parent.num
        node_num = self.num
        '''
        
        fpString = ''
        
        if mode_vector == None:
            # if `None` was passed, Turn off input on this side by setting input = Mode 0
            mode_vector = int(0)
        
        if isinstance(mode_vector, int):
            # an integer was passed, so set to mode component
            fpString += self.nodestring + "." + sidestr + "input.inputtype=1" + "\n"    # mode number input
            fpString += self.nodestring + "." + sidestr + "input.cpt=" + str(mode_vector - 1) + "\n"
            if sidestr == 'lhs': 
                self.input_field_left = mode_vector - 1
            elif sidestr == 'rhs':
                self.input_field_right = mode_vector - 1
        else:
            # assume an array-like was passed, so set the input as a vector

            ampString = str(mode_vector[0].real)+","+str(mode_vector[0].imag)
            for ii in range( 1, get_N() ):
                ampString += ","+str(mode_vector[ii].real)+","+str(mode_vector[ii].imag)
            
            fpString = self.nodestring + "." + sidestr + "input.inputtype=2" + "\n"     # vector input
            fpString += self.nodestring + "." + sidestr + "input.setvec(" + ampString + ")   \n"
        #end isinstance(mode_vector)
        
        if normalize:
            fpString += self.nodestring + "." + sidestr + "input.normalise=1  \n"
        else:
            fpString += self.nodestring + "." + sidestr + "input.normalise=0  \n"
        
        fimm.Exec(fpString)
    #end set_input_field()
    
    
    # Alias for the same function:
    set_inc_field = set_input
    set_input_vector = set_input
    
    def set_input_field(self):
        '''DEPRECATED: Perhaps you mean to use `set_input()`.'''
        raise NameError("DEPRECATED: Perhaps you mean to use `set_input()`, which accepts a field vector or mode number.")
    
    def get_input(self):
        '''Return the input field vector. 
        Returns a list, like so [<Left-hand field> , <Right-hand field>].  
        If a side has no input field, it will contain only the value `None`.
        If <Left-hand field> is itself a list, then the input type is a vector, while if an integer is returned, then the input type is just a mode number.  You can check for whether the returned type is a vector as so
            >>> input_field = Dev1.get_input_field()[0]
            >>> left_field = Dev1.get_input_field()[0]  # get the left-
            >>> isinstance(  left-field ,  int  )      # returns True
        
        Examples
        --------
        Dev.set_input_field( [1,0,0], side='left')  # vector-type input
        Dev.get_input_field()
        >>> [ [1,0,0], None ]
        # Which indicates that there is no Right-hand input, and the left-hand input launches only the 1st mode.
        '''
        
        
        """
        # Obsolete - FimmProp can't return the current Vector input, so just using internal values
        Ltype = fimm.Exec(  self.nodestring + ".lhsinput.inputtype"  )
        if Ltype==1:
            '''mode number'''
            self.input_field_left = fimm.Exec(  self.nodestring + ".lhsinput.cpt"  )
        elif Ltype == 2:
            self.input_field_left = fimm.Exec(  self.nodestring + ".lhsinput.getvec"  )
        else:
            raise self.name + ".get_input_field [left]: Unsupported input field type.  Only Mode number & Vector are supported."
        Rtype = fimm.Exec(  self.nodestring + ".lhsinput.inputtype"  )
        if Rtype==1:
            '''mode number'''
            self.input_field_right = fimm.Exec(  self.nodestring + ".lhsinput.cpt"  )
        elif Rtype == 2:
            self.input_field_right = fimm.Exec(  self.nodestring + ".lhsinput.getvec"  )  <<--- doesn't exist
        else:
            raise self.name + ".get_input_field [right]: Unsupported input field type.  Only Mode number & Vector are supported."
        """
            
        out=[]
        if np.all( np.array(self.input_field_left)  == 0 ):
            out.append(None)
        else:
            out.append( self.input_field_left )
        
        if np.all( np.array(self.input_field_right)  == 0 ):
            out.append(None)
        else:
            out.append( self.input_field_right )
            
        return out
    #end get_input_field()
    
    # Alias for the same function:
    get_inc_field = get_input
    get_input_vector = get_input
    
    
    def get_output_vector(self, side='right', direction='right'):
        '''Return the output field vector, for a given input field vector (`set_input_field()`).
        FimmProp calculates the scattering matrix of the Device and `propagates` the input field vectors (see `DeviceObj.set_input_field()` ) through the device, resulting in the output mode vector.
        This function does not currently output the 2D field profile, but only a field vector, which can be used to calculate the output field profile using the mode basis set and the field vector as the coefficients of each mode.
        
        Parameters
        ----------
        side : { 'left' | 'right' }, case-insensitive, optional
            Which side to inject fields into.  The string "left" (left-hand side) or "right" (right-hand side) should be used. Synonyms for "LHS" are "left" and "L", and correspondingly for "RHS" the synonyms are "right" and "R".
            Defaults to 'right' side for convenience.
            
          direction = string { 'fwd', 'bwd' }, case insensitive, optional
            Which propagation direction to return vectors for.  Defaults to 'right'.
            "forward" & "backwards" correspond with propagation in the +z & -z directions, respectively.
            Synonyms for 'fwd' include 'forward', 'f', 'right', 'r', '+z'.
            Synonyms for 'bwd' include 'backward', 'b', 'left', 'l', '-z'.
            Defaults to 'right' (forward) for convenience.
        
        Returns
        -------
        Vect : list
            List of length `get_N()`, with complex values corresponding to each mode in the basis-set.
        '''
        
        side = side.lower().strip()     # make lower case, strip whitespace
        if (side == 'lhs') or (side == 'left') or (side == 'l'):
            #sidestr = 'lhs'
            sidenum = 0     #LHS
        elif (side == 'rhs') or (side == 'right') or (side == 'r'):
            #sidestr = 'rhs'
            sidenum = 1     #RHS
        else:
            ErrStr = "get_output_field(): Unsupported side passed: `" + side + "`.  \n\tPlease use 'Left' or 'Right', or see `help(pyfimm.Device.set_inc_field)`."
            if DEBUG(): print "side.lower() = ", side.lower()
            raise ValueError(ErrStr)
        
        
        direction = direction.strip().lower()   # make lower case, strip whitespace
        '''Always returning vectors, so dirnum 0-Tot, 1-fwd, 2-bwd ignored - only needed for getting XY field profile.'''
        if direction=='fwd' or direction=='forwards' or direction=='forward' or direction=='f' or direction=='right' or direction=='r' or direction=='+z':
            dirstr = 'fwd'
            #dirnum = 1
        elif direction=='bwd' or direction=='backwards' or direction=='backward' or direction=='b' or direction=='left' or direction=='l' or direction=='-z':
            dirstr = 'bwd'
            #dirnum = 2
        else:
            ErrStr = "Device.get_output_field(): Unrecognized `direction` passed: `%s`.\n\t"%(direction) +   "Please use 'Left' or 'Right', or see `help(pyfimm.Device.set_inc_field)`. "
            raise ValueError(ErrStr)
        
        dirnum = 3  # calculate field vectors, as opposed to output field
        
        prj_num = self.parent.num
        node_num = self.num
        
        #app.subnodes[{"+str(prj_num)+"}].subnodes[{"+str(node_num)+"}]
        fpString = self.nodestring + ".calcoutputfield(" + str(dirnum) + "," + str(sidenum) + ")   " +"\n"
        fimm.Exec(fpString)
        
        #app.subnodes[{"+str(prj_num)+"}].subnodes[{"+str(node_num)+"}]
        fpString = self.nodestring + "." + dirstr + "coeffs()   " +"\n"
        out = fimm.Exec(fpString)
        return out[0][1:]   # strip the useless matrix chars `None` & `EOL` that FimmWave returns
    #end get_output_vector()
    
    
    def get_input_field(self, component='I', mode_vector=None, side='left', include_pml=True):
        '''Return the input field.  Useful for viewing what a superposition of the various basis modes would look like.
        
        Parameters
        ----------
        component = {'Ex' | 'Ey' | 'Ez' | 'Hx' | 'Hy' | 'Hz' | 'Px' | 'Py' | 'Pz' | 'I' }, case-insensitive, optional
            Plot the specified field component along the Z direction.
            'E' is electric field, 'H' is magnetic field, 'P' is the Poynting vector, 'I' is Intensity, and 'x/y/z' chooses the component of each vector to return.
            Defaults to "I".
        
        mode_vector : array-like, optional
            The mode-vector to plot.  The mode-vector is a list with `get_N()` elements (as used in `Device.set_input()`), where each element is the amplitude & phase coefficient of each waveguide mode.  Using the modes as a basis-set, you can construct any mode profile, as mode modes are included in the calculation.
            If not specified, will use the currently-set input field, (Dev.input_field_left/right) corresponding to the chosen `side`.
        
        side : { 'left' | 'right' }, optional
            Which side of the device to get the launch mode for.
        
        include_pml : { True | False }, optional
            Include any perfectly-matched layers in the plot?  True by default.
        '''

        """
        def mode(self,modeN):
        '''Waveguide.mode(int): Return the specified pyFimm Mode object for this waveguide.'''
        return Mode(self, modeN,"app.subnodes[{"+str(self.parent.num)+"}].subnodes[{"+str(self.num)+"}].evlist.")
        
        For Device:
        app.subnodes[1].subnodes[3].cdev.eltlist[1].wg.evlist.update
        = self.nodestring + ".cdev.eltlist[1].wg.evlist."
        """
        
        component = component.strip().lower()
        
        
        modelist = range(0, get_N() )     # list like [0,1,2,3]
        
        side = side.lower().strip()
        
        if side == 'left' or side == 'l' or side == 'lhs':
            if mode_vector is None:  mode_vector = self.input_field_left
            n = self.elementpos[0]     # 1st element
        elif side == 'right' or side == 'r' or side == 'rhs':
            if mode_vector is None:  mode_vector = self.input_field_right
            n = self.elementpos[-1]     # last element
        
        '''
        # normalize mode_vector
        mag = np.sum(  [np.abs(x) for x in mode_vector]  )
        mode_vector = np.array(mode_vector)/float(mag)
        '''
        
        # calculate modes of the element:
        if DEBUG(): print 'Device "%s"' % self.name + '.plot_input_field(): Calculating modes of element %i...' % n
        fimm.Exec(  self.nodestring + ".cdev.eltlist[%i].wg.evlist.update()" % n  )
        
        modes =  Mode(self, modelist, self.nodestring + ".cdev.eltlist[%i].wg.evlist." % n   )
        fields = modes.get_field(  component  , include_pml=include_pml, as_list=True ) # returns list of all the fields
        
        if DEBUG(): print "Dev.get_input_field():\n", "np.shape(fields) = ", np.shape(fields), "\n", "len(fields)=", len(fields), "\n", "len(fields[0])=", len(fields[0])
        
        superfield = np.zeros_like( fields[0] )     # zeros with same dims as returned field
        for i, field   in   enumerate(fields):
            if DEBUG(): print "i=",i, "\n","mode_vector[i]=", mode_vector[i], "\n", "np.shape(field)=", np.shape(field)
            if DEBUG(): print "get_input_field(): min/max(field) = %f/%f" % (np.min(np.array(field).real), np.max(np.array(field).real))
            superfield = superfield + np.array(field) * mode_vector[i]

        return superfield.transpose()
        '''
        - can get FimmWave to do this?
        
        - Provided that you are only launching light from one end of the Device (either LHS or RHS) then the best way to do this is to export the forward (LHS) or backward (RHS) field profile at the launching end of the Device; this is the equivalent of right-click "\View XY field at..." in the GUI.
        
        '''
    #end get_input_field()
    
    # Alias for the same function:
    get_inc_field = get_input_field
    
    
    def plot_input_field(self, component='I', mode_vector=None, side='left', include_pml=True, title=None, annotations=False, return_handles=False, plot_type='pseudocolor'):
        '''Plot the input field.  Useful for viewing what a superposition of the various basis modes would look like.
        
        Parameters
        ----------
        component = {'Ex' | 'Ey' | 'Ez' | 'Hx' | 'Hy' | 'Hz' | 'Px' | 'Py' | 'Pz' | 'I' }, case-insensitive, optional
            Plot the specified field component along the Z direction.
            'E' is electric field, 'H' is magnetic field, 'P' is the Poynting vector, 'I' is Intensity, and 'x/y/z' chooses the component of each vector to return.
            Defaults to "I".
        
        mode_vector : array-like, optional
            The mode-vector to plot.  The mode-vector is a list with `get_N()` elements (as used in `Device.set_input()`), where each element is the amplitude & phase coefficient of each waveguide mode.  Using the modes as a basis-set, you can construct any mode profile, as mode modes are included in the calculation.
            If not specified, will use the currently-set input field, (Dev.input_field_left/right) corresponding to the chosen `side`.
        
        side : { 'left' | 'right' }, optional
            Which side of the device to get the launch mode for.
        
        include_pml : { True | False }, optional
            Include any perfectly-matched layers in the plot?  True by default.
        
        title : string, optional
            Will prepend this text to the output filename, and do the same to the Plot Title.
            If not provided, the name of the passed Waveguide component, Mode Number & Field Component will be used to construct the filename & plot title.
        
        annotations : boolean, optional
            If true, the effective index, mode number and field component will written on each mode plot.  True by default.
        
        plot_type : { 'pseudocolor' | 'contourf' }, optional
            Plot the modes as pseudo-color (interpolated coloring, default) or filled contour?
        
        return_handles : { True | False }, optional
            If True, will return handles to the figure, axes and images.  False by default.
        
        
        Returns
        -------
        fig, axes, imgs
            The matplotlib figure, axis and image (`pyplot.imshow()` ) handles.  Only returned if `return_handles=True`
        `fig` is the handle to the whole figure, allowing you to, for example, save the figure yourself (instead of using `Mode.save_plot()` ) via `fig.savefig(pat/to/fig.png)`.
        `ax` is the handle of the single axis object on the figure.
        `cont` is the handle to the contourf() plot (filled-contour).
        
        '''
        
        side = side.lower().strip()
        if side == 'left' or side == 'l' or side == 'lhs':
            sidestr = 'lhs'
            n=1     # 1st element
            if mode_vector is None:  mode_vector = self.input_field_left
        elif side == 'right' or side == 'r' or side == 'rhs':
            sidestr = 'rhs'
            n = self.elementpos[-1]     # last element
            if mode_vector is None:  mode_vector = self.input_field_right
            
            
        field = self.get_input_field(component=component, mode_vector=mode_vector, side=side, include_pml=include_pml)
        
        if title:
            plot_title = title + " - %s=%s" %(side, mode_vector)
        else:
            plot_title = '"%s": ' % self.name  +  "%s=%s" %(side, mode_vector)
        
        
        # Options for the subplots:
        sbkw = {'axisbg': (0.15,0.15,0.15)}    # grey plot background
        fig, ax = plt.subplots(nrows=1, ncols=1, subplot_kw=sbkw)
        
        fig.suptitle(plot_title, fontsize=10)   # figure title
        fig.canvas.draw()  # update the figure
        
        # generate X & Y coords:
        modestring = self.nodestring + ".cdev.eltlist[%i]"%(n) + ".get%sevlist"%(sidestr) + ".list[1].profile.data"
        d = get_amf_data( modestring )
        
        if DEBUG(): 
            import pprint
            print "Device.plot_input_field():  get_amf_data() returned:"
            pprint.pprint(d)
        
        x = np.linspace( d['xmin'], d['xmax'], num=d['nx'], endpoint=True )
        y = np.linspace( d['ymin'], d['ymax'], num=d['ny'], endpoint=True )
        
        if DEBUG(): print "(x, y) = ", x, y
        
        #x = range( np.shape(field)[1] )
        #y = range( np.shape(field)[0] )
        
        if DEBUG(): print "Dev.plot_input_field(): min/max(field) = %f/%f" % (np.min(np.array(field).real), np.max(np.array(field).real))
        maxfield = np.max(   np.abs(  np.array(field).real  )   )
        
        if plot_type is 'pseudocolor':
            cont = ax.pcolor( np.array(x), np.array(y), np.array(field)[:-1,:-1] , vmin=-maxfield, vmax=maxfield, cmap=cm_hotcold)      # cm_hotcold, cm.hot, RdYlBu, RdPu, RdBu, PuOr, 
        elif plot_type is 'contourf':
            cont = ax.contourf( np.array(x), np.array(y), np.array(field)[:-1,:-1] , vmin=-maxfield, vmax=maxfield, cmap=cm_hotcold)      # cm_hotcold, cm.hot, RdYlBu, RdPu, RdBu, PuOr, 
        else:
            ErrStr = 'Device "%s".plot_input_field(): ' % self.name + 'Unrecognized plot_type: `%s`. ' % plot_type + 'Please use `contour` or `psuedocolor` or leave unsepcified.'
            raise ValueError( ErrStr )
        ax.set_xlim( d['xmin'], d['xmax'] )
        ax.set_ylim( d['ymin'], d['ymax'] )
        fig.canvas.draw()
        
        if return_handles: return fig, ax, cont
        
    #end plot_input_field()
    
    # Alias for the above function:
    plot_inc_field = plot_input_field
    
    
    def set_input_beam(self, beam_pol, ref_z, h, w, inc_n, hor_tilt, ver_tilt, x_offset, y_offset, z_offset):
        '''Set input to gaussian beam with corresponding parameters.
        
        Parameters
        ----------
        beam_pol : { 'TE', 'TM' }, case-insensitive, optional
            Defaults to 45 degrees (halfway between TE & TM) with 90 degree phase delay.
        
        ref_z : float
            If ref_z == 0, then collimated beam.  Otherwise, spherically-diverging beam with pivot distance of reference plane == ref_z.
        
        h,w: float
            gaussian beam height/width
            
        inc_n: float
            refractive index of input medium
            
        horiz_tilt, vert_tilt: float
            tilt of input beam
            
        x/y/z_offset: float
            offsets of the input beam's pivot point (around which to tilt)
        '''
        
        prj_num = self.parent.num
        node_num = self.num
        if beam_pol.strip().lower() == 'te':
            fpString = self.nodestring + ".lhsinput.theta=0"+"\n"
            fpString += self.nodestring + ".lhsinput.phi=0"+"\n"
        elif beam_pol.strip().lower() == 'tm':
            fpString = self.nodestring + ".lhsinput.theta=90"+"\n"
            fpString += self.nodestring + ".lhsinput.phi=0"+"\n"
        else:
            fpString = self.nodestring + ".lhsinput.theta=45"+"\n"
            fpString += self.nodestring + ".lhsinput.phi=90"+"\n"
        
        
        fpString += self.nodestring + ".lhsinput.inputtype=3"+"\n" # input type = beam
        fpString += self.nodestring + ".lhsinput.iproftype=1"+"\n" # gaussian
        
        if ref_z == 0:
            fpString += self.nodestring + ".lhsinput.phasetype=0"+"\n" # collimated
        else:
            fpString += self.nodestring + ".lhsinput.phasetype=1"+"\n" # spherical divergence
        
        fpString += self.nodestring + ".lhsinput.gaussh={"+str(h)+"}"+"\n"
        fpString += self.nodestring + ".lhsinput.gaussw={"+str(w)+"}"+"\n"
        fpString += self.nodestring + ".lhsinput.n0={"+str(inc_n)+"}"+"\n"
        fpString += self.nodestring + ".lhsinput.h_tilt={"+str(hor_tilt)+"}"+"\n"
        fpString += self.nodestring + ".lhsinput.v_tilt={"+str(ver_tilt)+"}"+"\n"
        fpString += self.nodestring + ".lhsinput.pivxy.xalign=0"+"\n"
        fpString += self.nodestring + ".lhsinput.pivxy.xoff={"+str(x_offset)+"}"+"\n"
        fpString += self.nodestring + ".lhsinput.pivxy.yalign=0"+"\n"
        fpString += self.nodestring + ".lhsinput.pivxy.yoff={"+str(y_offset)+"}"+"\n"
        fpString += self.nodestring + ".lhsinput.pivz={"+str(z_offset)+"}"+"\n"
        fpString += self.nodestring + ".lhsinput.refdist={"+str(ref_z)+"}"+"\n"
        fpString += self.nodestring + ".lhsinput.refrot=0"
        
        fimm.Exec(fpString)
    #end set_input_beam()
    
    # Alias to the same function:
    set_coupling_beam = set_input_beam
    
    
    
    def get_coupling_loss(self,mode_n):
        '''Return coupling loss in dB.
        Corresponds to Fimmprops' `CalcModePower` command, converted to dB.
        
        mode_n: integer
            Which mode to calc loss for.
        '''
        prj_num = self.parent.num
        node_num = self.num
        power_frac = fimm.Exec(self.nodestring + ".calcmodepower("+str(mode_n+1)+")")
        return -10*log10(power_frac)
    #end get_coupling_loss()
    
    # Alias to the same function:
    coupling_loss = get_coupling_loss
    
    
    def get_coupling_efficiency(self,mode_n):
        '''Return coupling loss in fractional form (eg. 0->1).
        Corresponds to Fimmprops' `CalcModePower` command.
        
        mode_n: integer
            Which mode to calc loss for.'''
        prj_num = self.parent.num
        node_num = self.num
        power_frac = fimm.Exec(self.nodestring + ".calcmodepower("+str(mode_n+1)+")")
        return power_frac
    #end get_coupling_efficiency()
    
    # Alias to same function:
    coupling_efficiency = get_coupling_efficiency
    
    
    
    ###### Return Scattering Matrix ######
    
    def R12(self,out,inc):
        '''Return reflection at Left port.'''
        prj_num = self.parent.num
        node_num = self.num
        return fimm.Exec(self.nodestring + ".cdev.smat.ll[{"+str(out+1)+"}][{"+str(inc+1)+"}]")
    
    def S_ll(self,out,inc):
        '''Return scattering Matrix Left-to-Left: Alias for R12()'''
        return R12(self,out=out,inc=inc)
    
    
    def T12(self,out,inc):
        '''Return transmission from Left to Right.'''
        prj_num = self.parent.num
        node_num = self.num
        return fimm.Exec(self.nodestring + ".cdev.smat.lr[{"+str(out+1)+"}][{"+str(inc+1)+"}]")
    
    def S_lr(self,out,inc):
        '''Return scattering Matrix Left-to-Right: Alias for T12()'''
        return T12(self,out=out,inc=inc)
    
    
    def R21(self,out,inc):
        '''Return reflection at Right port.'''
        prj_num = self.parent.num
        node_num = self.num
        return fimm.Exec(self.nodestring + ".cdev.smat.rr[{"+str(out+1)+"}][{"+str(inc+1)+"}]")
    
    def S_rr(self,out,inc):
        '''Return scattering Matrix Right-to-Right: Alias for R21()'''
        return R21(self,out=out,inc=inc)
    
    
    def T21(self,out,inc):
        '''Return transmission from Right to Left.'''
        prj_num = self.parent.num
        node_num = self.num
        return fimm.Exec(self.nodestring + ".cdev.smat.rl[{"+str(out+1)+"}][{"+str(inc+1)+"}]")
    
    def S_rl(self,out,inc):
        '''Return scattering Matrix Right-to-Left: Alias for T21()'''
        return T21(self,out=out,inc=inc)
    
    

################################################################
####                                                        ####
####                    Plotting etc.                       ####
####                                                        ####
################################################################

    '''Each of these require the input to have been set by `set_input_field()`'''
    
    def plot_refractive_index(self, zpoints=3000, zmin=0.0, zmax=None, xcut=0.0, ycut=0.0, calc=False, return_handles=False, title=None):
        '''Plot the refractive index versus Z.  
            Calls `Device.plot()` with `component="index"`.  
            See `help(Device.plot)` for info on other arguments/options.
        '''
        if not calc:
            if not self.calculated: 
                print "Device.plot_refractive_index(): Calculating the Device..."
                calc=True
        
        return self.plot('rix', zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut, direction='total', calc=calc, return_handles=return_handles, title=title)
    
    
    def get_refractive_index(self, zpoints=3000, zmin=0.0, zmax=None, xcut=0.0, ycut=0.0, calc=False):
        '''Calls `Device.get_field()` to return the refractive index of the device.  The `component` & `direction` options have been removed as compared with `get_field()`.
        component : { X | Y | Z }, optional - NOT IMPLEMENTED YET
            Which component of the refractive index tensor to return.  For simple isotropic materials, these are all identical.  Defaults to Z.
        
        See `help(Device.get_field)` for info on the other options.
        '''
        if DEBUG(): print "Device.get_refractive_index(): "
        if not calc:
            if not self.calculated: 
                print "Device.get_refractive_index(): Calculating the Device..."
                calc=True
        
        return self.get_field( 'rix', zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut, direction='total', calc=calc)
    
    
    def get_field(self, component, zpoints=3000, zmin=0.0, zmax=None, xcut=0.0, ycut=0.0, direction='total', calc=False, warn=True):
        '''Return the field specified by `component` versus Z.
        Expects that the input field has been set with `set_input_field()`.
        
        component = {'Ex' | 'Ey' | 'Ez' | 'Hx' | 'Hy' | 'Hz' | 'Px' | 'Py' | 'Pz' | 'I' }, case-insensitive, required
            Return the specified field component along the Z direction.
            'E' is electric field, 'H' is magnetic field, 'P' is the Poynting vector, 'I' is Intensity, and 'x/y/z' chooses the component of each vector to return.
            'index', 'rix' or 'ri' will return the refractive index, a functionality provided by the more convenient function `get_refractive_index()` but otherwise identical to this func.
        
        direction = string { 'fwd', 'bwd', 'total' }, case insensitive, optional
            Which field propagation direction to plot.  Defaults to 'total'.
            Note that the propagation direction should match up with which side the input field was launched.  Eg. for `set_input_field([1,0,0], side="left")` you'll want to use `direction="fwd"`, meaning propagating to the right (+z).
            Synonyms for 'fwd' include 'forward', 'f', 'right', 'r', '+z'.
            Synonyms for 'bwd' include 'backward', 'b', 'left', 'l', '-z'.
            Synonyms for 'total' include 'tot' & 't'.  
            Defaults to 'total'.
        
        xcut, ycut = float, optional
            x & y coords at which to cut the Device along Z.  Both default to 0.
        
        zpoints = integer, optional
            Number of points to acquire in the field.  Defaults to 3000.
        
        zmin, zmax = float, optional
            min & max z-coorinates. Defaults to 0-->Device Length (plot entire Device).
        
        calc = { True | False }
            Tell FimmProp to calculate the fields?  Only needs to be done once to store all field components & refractive indices (for a given `zpoints`, `xcut` etc.), so it is useful to prevent re-calculating after the first time.  False by default.
        
        cut = tuple of two floats - NOT IMPLEMENTED YET
            Specify coordinate plane on which to plot fields. Default (0,0).
            If dir='Z', then tuple is (x,y).
            If dir='Y', then tuple is (x,z).
            If dir='X', then tuple is (y,z).
        
        warn : Boolean
            Print wanring messages?  True by default.
        
        Returns
        -------
        List of complex values corresponding to field values, starting at z=0 and ending at specified `zmax`.
        
        Examples
        --------
        Get the Total Ex field at x,y=(0,0) along Z, along the whole Device.
            >>> field = Dev.fields('Ex')
        Get the refractive index at x,y=(0,0) along Z, along the whole Device.
            >>> field = Dev.fields('index')
        
        '''
        
        # 1st arg: Figure out which component string to send FimmWave:
        component = component.lower().strip()
        if component == 'Ex'.lower():
            compstr='Ex'
        elif component == 'Ey'.lower():
           compstr='Ey'
        elif component == 'Ez'.lower():
           compstr='Ez'
        elif component == 'Hx'.lower():
           compstr='Hx'
        elif component == 'Hy'.lower():
           compstr='Hy'
        elif component == 'Hz'.lower():
           compstr='Hz'
        elif component == 'I'.lower():
           compstr='Intensity'
        elif component == 'px':
            compstr='Pxx'
        elif component == 'py':
            compstr='Pyy'
        elif component == 'pz':
            compstr='Pzz'
        elif component=='rix' or component=='index' or component=='ri':
            compstr='RefZZ'     # plots Z-to-Z component of RIX tensor only - assuming simple homogeneous material
        else:
            raise ValueError("Device.field(): Invalid field component requested: `"+str(component)+"`.")
        
        
        if direction != 'Total':
            direction = direction.lower().strip()   # lower case & strip whitespace
        
        if direction=='fwd' or direction=='forwards' or direction=='forward' or direction=='f' or direction=='right' or direction=='r' or direction=='+z':
            dirstr = 'Fwg'
        elif direction=='bwd' or direction=='backwards' or direction=='backward' or direction=='b' or direction=='left' or direction=='l' or direction=='-z':
            if component=='i':
                '''Due to Fimmwave typo bug: should be Title case.  '''
                dirstr = 'bwg'      # fieldstr for bwd intensity is 'Intensitybwd'
            else:
                '''for every other component, it's "ExBwg" with TitleCase.  '''
                dirstr = 'Bwg'
        elif direction=='total' or direction=='tot' or direction=='t':
            dirstr = 'Total'
        else:
            ErrStr = "Device.get_field(): Unrecognized `direction` passed: `%s`."%(direction) 
            raise ValueError(ErrStr)
        
        fieldstr = compstr + dirstr     #attribute of FimmWave `zfieldcomp` object
        
        
        if not zmax: zmax = self.get_length()
        
            
        # Extract the field values:
        NumPoints = zpoints        # params for calczfield()
        xpoint = xcut;     ypoint=ycut
        
        prj_num = self.parent.num
        node_num = self.num
        
        # Tell FimmProp to calculate the Z fields:
        if not calc:
            if not self.calculated: 
                if warn: print "WARNING: Device.get_field(): Device `%s` was not calculated before extracting fields - may return [zeros]."%(self.name)
                #print "Device.get_field(): Calculating the Device..."
                #self.calc(zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut)
        else:
            self.calc(zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut)
        #if calc: self.calc(zpoints=NumPoints, zmin=zmin, zmax=zmax, xcut=xpoint, ycut=ypoint)  
        #fimm.Exec("app.subnodes[{"+ str(prj_num) +"}].subnodes[{"+ str(node_num) +"}]."+"calczfield("+ str(NumPoints) +","+ str(zmin) +", "+ str(zmax) +","+ str(xpoint) +","+ str(ypoint) +",1)"    +"\n")
        
        # Extract the field values:
        fpString = self.nodestring + "."+"zfieldcomp."+fieldstr+"\n"
        zfield = fimm.Exec(fpString)
        zfield = zfield[0][1:]   # remove the first `None` entry & EOL char.
        
        return zfield
    #end field()
    
    # Alias to same function:
    field = get_field
    
    
    def plot(self, component, zpoints=3000, zmin=0.0, zmax=None, xcut=0.0, ycut=0.0, direction='total', refractive_index=False, return_handles=False, calc=False, title=None, warn=True):
        '''Plot the fields in this device along the Z (propagation) direction.
        Requires that the input field has been set with `set_input_field()`.
        
        Parameters
        ----------
        
        component = {'Ex' | 'Ey' | 'Ez' | 'Hx' | 'Hy' | 'Hz' | 'Px' | 'Py' | 'Pz' | 'I' }, case-insensitive, required
            Plot the specified field component along a specified direction.
            'E' is electric field, 'H' is magnetic field, 'P' is the Poynting vector, 'I' is Intensity, and 'x/y/z' chooses the component of each vector to return.
            'index', 'rix' or 'ri' will plot the refractive index, a functionality also provided by the argument `refractive_index=True`.
        
        direction = string { 'fwd', 'bwd', 'total' }, case-insensitive, optional
            Which field propagation direction to plot.  Defaults to 'total'.
            Note that the propagation direction should match up with which side the input field was launched.  Eg. for `set_input_field([1,0,0], side="left")` you'll want to use `direction="fwd"`.
            Synonyms for 'fwd' include 'forward', 'f', 'right', 'r', '+z'.
            Synonyms for 'bwd' include 'backward', 'b', 'left', 'l', '-z'.
            Synonyms for 'total' include 'tot' & 't'.
        
        refractive_index = { True | False }
            If True, will plot the refractive index of the structure on a second axis, with shared X-axis (so sooming etc. zooms both X axes).  Default is False.
        
        xcut, ycut = float, optional
            x & y coords at which to cut the Device along Z.  Both default to 0.
        
        zpoints = integer, optional
            Number of points to acquire in the field.  Defaults to 3000.
        
        zmin, zmax = float, optional
            min & max z-coorinates. Defaults to 0-->Device Length.
        
        calc = { True | False }
            Tell FimmProp to calculate the fields?  Only needs to be done once to store all field components & refractive indices (for a given `zpoints`, `xcut` etc.), so it is useful to prevent re-calculating after the first time.
            
        return_handles = { True | False }, optional
            If True, will return handles to the figure, axes, legends and lines.  False by default.
        
        title = str, optional
            Pre-pend some text to the plot title.
        
        cut = tuple of two floats - NOT IMPLEMENTED YET
            Specify coordinate plane on which to plot fields. Default (0,0).
            If dir='Z', then tuple is (x,y).
            If dir='Y', then tuple is (x,z).
            If dir='X', then tuple is (y,z).
        
        warn : boolean
            Print warning messages for unset default values etc.?  Defaults to True.

        Returns
        -------
        handles : tuple of (fig1, axes, lines, leg)
            If `return_handles=True`, returns matplotlib handles to the plot's objects, as so:
            fig1 : main figure object
            axes : Each axis. If `refractive_index=True` then axes = ( Field_Axis , RI_Axis ), otherwise just = Field_Axis handle.
            lines : Each curve plotted. If `refractive_index=True` then lines = ( RI_line, Field_Line_Mode_0, Field_Line_Mode_1 , ... Field_Line_Mode_N ), otherwise handle RI_Line is omitted.
            leg : legend of main Field axis, containing one legend entry for each mode number.
        
        
        Examples
        --------
        Plot Fields of the Device given some injected mode vector:
            >>> DeviceObj.set_input_field( [1,0,0] )     # launch 1st mode only, into left side.
            >>> DeviceObj.set_input_field( [0,0,0], side='right' )     # launch nothing into right side.
            >>> DeviceObj.mode( 0 ).plot('Ex')  # plot Ex propagating in +z direction
            >>> DeviceObj.mode( 'all' ).plot('Hy', direction='left')  # plot Hy for all modes on one plot, propagating in left (-z) direction.
            >>> DeviceObj.mode( 0 ).plot('Ex', refractive_index=True)  # plot Ex Total of Mode 0, with Refractive Index profile plotted on separate axis
            >>> fig, axis, line, leg = DeviceObj.mode( 0 ).plot('Ex', return_handles=True)  # plot Ex Total of Mode 0 and return matplotlib handles to the figure's elements
        '''
        
        RIplot = refractive_index
        
        
        # Component string for plot title:
        component = component.lower().strip()
        if component == 'Ex'.lower():
            compstr='Ex'
        elif component == 'Ey'.lower():
           compstr='Ey'
        elif component == 'Ez'.lower():
           compstr='Ez'
        elif component == 'Hx'.lower():
           compstr='Hx'
        elif component == 'Hy'.lower():
           compstr='Hy'
        elif component == 'Hz'.lower():
           compstr='Hz'
        elif component == 'I'.lower():
           compstr='Intensity'
        elif component=='rix' or component=='index' or component=='ri':
            compstr='Refr. Index'     # plots Z-to-Z component of RIX tensor only - assuming simple homogeneous material
        else:
            raise ValueError("Device.plot(): Invalid field component requested.")
        
        # Direction for plot title:
        if direction=='fwd' or direction=='forwards' or direction=='forward' or direction=='f' or direction=='right' or direction=='r' or direction=='+z':
            dirstr = 'Right (+z)'
        elif direction=='bwd' or direction=='backwards' or direction=='backward' or direction=='b' or direction=='left' or direction=='l' or direction=='-z':
            dirstr = 'Left (-z)'
        elif direction=='total' or direction=='tot' or direction=='t' or direction=='Total':
            dirstr = 'Total'
        else:
            ErrStr = "Device.plot(): Unrecognized `direction` passed: `%s`."%(direction) 
            #raise ValueError(ErrStr)
            if warn: print "WARNING: Unrecognized `direction` passed: `%s`."%(direction) 
            dirstr=direction
        
        if not calc:
            if not self.calculated: 
                print "Device.plot(): Calculating the Device..."
                calc=True
        zfield = self.get_field(component, zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut, direction=direction, calc=calc)
        
        # plot the field values versus Z:
        zfield = np.array(zfield)
        TotalLength = self.get_length()
        z = np.linspace( 0, TotalLength, num=len(zfield) )   # Z-coord
        
        if DEBUG(): print "Device.plot(): len(zfield)=%i"%(len(zfield) )
        if DEBUG(): print "np.shape(zfield)=", np.shape(zfield)
        if DEBUG(): print "z(%i) = "%len(z), z
        
        if RIplot:
            rix = self.get_refractive_index(zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut, calc=False)
            fig1, (ax1,ax2) = plt.subplots(2, sharex=True)      # 2 axes
            
            # Reduce axis width to 80% to accommodate legend:
            #box = ax2.get_position()
            #ax2.set_position([ box.x0, box.y0, box.width * 0.8, box.height])
            
            l2 =  [ ax2.plot(z, np.array(rix).real, 'g-', label="Refractive Index" ) ]      # plot RIX on 2nd sibplot
        else:
            fig1, ax1 = plt.subplots(1, 1)      # 1 axis
        
        # Reduce axis width to 80% to accommodate legend:
        #box = ax1.get_position()
        #ax1.set_position([ box.x0, box.y0, box.width * 0.8, box.height])
        
        l1 = [];

        #l1 = []; l2 = []; leg1 = []; leg2=[]
        l1.append(   ax1.plot(z, np.real(zfield), '-' )   )
        #leg1.append("Real")

        #end for(modenum)
    
        ax1.set_ylabel( "Field %s"%(compstr) )
        titlestr = "%s: %s %s vs. Z"%(self.name, compstr,dirstr)
        if title: titlestr = title + ": " + titlestr
        ax1.set_title(  titlestr  )
        ax1.grid(axis='both')
        #plt.legend()
        
        if RIplot:
            ax2.set_ylabel('Refractive Index')
            ax2.set_xlabel(r"Z, ($\mu{}m$)")
            ax2.grid(axis='both')
        else:
            ax1.set_xlabel(r"Z, ($\mu{}m$)")
        
        #leg = plt.legend()
        #leg = ax1.legend( loc='upper left', bbox_to_anchor=(1, 1) , fontsize='small' )
        #leg2 = ax2.legend( loc='upper left', bbox_to_anchor=(1, 1) , fontsize='small' )
    
        fig1.canvas.draw(); fig1.show()
        
        # return some figure handles
        if return_handles:     
            if RIplot:
                return fig1, (ax1, ax2), (l1, l2)
            else:
                return fig1, ax1, l1
    #end plot()



################################################################
####                                                        ####
####                    Node Builders                       ####
####                                                        ####
################################################################
    
    def buildNode(self, name=None, parent=None, overwrite=False, warn=True):
        '''Build the Fimmwave node of this Device.
        
        Parameters
        ----------
        name : string, optional
            Provide a name for this waveguide node.  Will overwrite a previously specified existing name.
        parent : Node object, optional
            Provide the parent (Project/Device) Node object for this waveguide.  If specified previously by Device.parent=<parentNode>, this will overwrite that setting.
        
        overwrite : { True | False }, optional
            Overwrite existing node of same name?  Defaults to False, which will rename the node if it has the same name as an existing node.
        
        warn : {True | False}, optional
            Print notification if overwriting a node?  True by default.
        
        
        To Do:
        ------
        Add optional argument `buildNode = True`, which will build all passed WG objects while adding them to the Device.
            
        '''
        if self.built: raise UserWarning(  'Device "%s".buildNode(): Device is already built in FimmWave!  Aborting.'%(self.name)  ) 
        
        if name: self.name = name
        if parent: self.set_parent(parent)
        
        #parent.children.append(self)
        
        '''
        nodestring="app.subnodes["+str(self.parent.num)+"]"
        self._checkNodeName(nodestring, overwrite=overwrite, warn=warn)     # will alter the node name if needed
        '''
        
        #nodestring = parent.nodestring
        check_node_name(self.name, self.parent.nodestring, overwrite=overwrite, warn=warn)
        
        self.jointpos = []    # eltlist[] position of simple joints
        self.elementpos = []  # eltlist[] position of each waveguide element
        #N_nodes = fimm.Exec("app.subnodes["+str(self.parent.num)+"].numsubnodes()")
        N_nodes = fimm.Exec( self.parent.nodestring+".numsubnodes()")
        node_num = int(N_nodes)+1
        self.num = node_num
        prj_num = self.parent.num
        node_name = self.name
        
        if DEBUG(): print "Device.buildNode(): ",len(self.elements), " elements."
        
        # create new FimmProp Device
        fimm.Exec(self.parent.nodestring + ".addsubnode(FPdeviceNode,"+str(node_name)+")"+"\n")
        self.nodestring = self.parent.nodestring + ".subnodes[%i]"%(node_num)
        
        
        elnum = 0   # element number in the Device - 1st/left-most is 1, next is 2, next is 3.
        
        fpString = ""
        
        
        # set device wavelength:
        fpString += self.nodestring + ".lambda = " + str(self.get_wavelength()) + "   \n"
        
        
        if get_material_database():
            fpString += self.nodestring + ".setmaterbase(" + get_material_database() + ")  \n"
        
        # newwgsect options:
        num2 = 1        # 0 = use Device parameters, 1 = use WG parameters
        jtype_warning = True    # warning flag for joint-type override
        
        for ii,el in enumerate(self.elements):
            elnum = elnum+1
            

            if isinstance(  el, Taper  ):
                '''I am not testing the Taper at all - not sure if this actually works.
                But keeping it here just in case it does.'''
                if DEBUG(): print "Device.buildNode():  type = Taper"
                fpString +=   self.__BuildTaperNode( el, elnum )
                el.built = True
                self.elementpos.append(elnum)
                # Set the WG length:
                fpString += self.nodestring + ".cdev.eltlist["+str(elnum)+"].length="+str(self.lengths[ii]) + "  \n"
            
            elif isinstance( el, Lens ):
                '''The Lens object will be a Waveguide Lens type of element.'''
                if DEBUG(): print "Device.buildNode():  type = Lens"
                fpString +=   self.__BuildLensElement( el, elnum )
                el.built = True
                self.elementpos.append(elnum)
                
            else:
                '''For all waveguide elements, add the previously built WG Node to this Device:'''
                
                if el.built != True:
                    '''If the WG was not previously built, tell it to build itself.  '''
                    try:
                        print self.name + ".buildNode(): Attempting to build the unbuilt element:", el.name
                        el.buildNode()  # tell the element to build itself
                    except:
                        errstr = "Error while building Device Node `"+self.name+"`: \nA constituent waveguide could not be built. Perhaps try building all waveguide nodes via `WGobj.buildNode()` before building the Device."
                        raise RuntimeError(errstr)
                
                if DEBUG(): print "Device.buildNode(): %i: type(el)=%s, name=%s"%(ii, str(type(el)), el.name)
                
                # Add the waveguide node into this Device:
                #   (assumes WG Node is in the root-level of this FimmWave Project)
                fpString += self.nodestring + ".cdev.newwgsect("+str(elnum)+","+"../"+el.name+","+str(num2)+")  \n"      
                self.elementpos.append(elnum)   # save the element number (elt) of this WG element.
                    
                # Set the WG length:
                fpString += self.nodestring + ".cdev.eltlist["+str(elnum)+"].length="+str(self.lengths[ii]) + "  \n"

            #end if(is Taper/Lens/etc.)
            
            

            if ii != len(self.elements)-1:
                '''Add a simple joint between waveguides.'''
                elnum = elnum+1
                fpString += self.nodestring + ".cdev.newsjoint("+str(elnum)+")"+"\n"
                
                
                # Set the Joint method : 0="complete"  1=normal Fresnel, 2=oblique Fresnel, 3=special complete
                # get joint types:
                if self.get_joint_type() == None:
                    jtype = el.get_joint_type(True)     # Element-level joint-type
                else:
                    jtype = self.get_joint_type(True)   # Device-level joint-type
                    if jtype != el.get_joint_type(True) and jtype_warning:
                        print "Warning: " + self.name + ".buildNode(): settings for Device joint type do not match those of element #" + str(elnum-1) + " (of type " + str(type(el)) + "). The Device setting will override the element's setting.  This warning will be suppressed for the rest of the build."
                        jtype_warning = False   # suppress this warning from now on
                #end if(joint type)
                    
                fpString += self.nodestring + ".cdev.eltlist["+str(elnum)+"].method="+str( jtype )+"\n"
                self.jointpos.append(elnum)   # add position of this joint to the joints list

            
        #end for(ii,elements)
        
        # Set wavelength:
        fpString += self.nodestring + ".lambda = " + str( self.get_wavelength() ) + "   \n"
        
        fimm.Exec(fpString)     # it is MUCH faster to send one giant string, rather than Exec'ing many times.
        
        self.built=True
    #end buildNode()
    
    
    
################################################################
##      Tapers
################################################################
    
    
    def __BuildLensElement(self, el, elnum ):
        '''FimmProp commands to build a Waveguide Lens node.  Most of the commands will come from the Lens object itself.'''
        if DEBUG(): print "__BuildLensElement(): base WG = %s"%(el.wgbase.name)
        node_num = self.num
        prj_num = self.parent.num
        #node_name = el.lhs.name
        
        
        fpString=""
        fpString += "app.subnodes[{"+str(prj_num)+"}].subnodes[{"+str(node_num) + "}].cdev.newwglens({"+str(elnum)+"},../"+str(el.wgbase.name) + ")"+"\n"     # add the WGLens element
        
        nodestring = "app.subnodes[{"+str(prj_num)+"}].subnodes[{"+str(node_num) + "}].cdev.eltlist[{"+str(elnum)+"}]"
        
        #fpString += nodestring + ".length={"+str(el.length)+"}"+"\n"
        fpString += el.get_buildNode_str(nodestring)    # get the rest of the solver params build from the object itself
        
        '''TO DO:
        set el.length, by calculating from Radius.'''
        
        return fpString
    #end __BuildLensElement
    
    
    
    def __BuildTaperNode(self, el, elnum):
        '''FimmProp commands to build a Taper Node.
            NOT TESTED YET
        '''
        
        if DEBUG(): print "__BuildTaperNode():"
        node_num = self.num
        prj_num = self.parent.num
        node_name = self.name
        fpString=""
        fpString += self.nodestring + ".cdev.newtaper({"+str(2*ii+1)+"},../"+str(el.lhs)+",../"+str(el.rhs)+")"+"\n"
        fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].length={"+str(el.length)+"}"+"\n"
        fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].shape_type=0"+"\n"
        fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].itpfunc.string=\""+str()+"\""+"\n"

        if el.method == 'full':
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].int_method=0"+"\n"
        else:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].int_method=1"+"\n"

        if  mode_solver() == 'vectorial FDM real' or mode_solver() == 'semivecTE FDM real' or mode_solver() == 'semivecTM FDM real' or mode_solver() == 'vectorial FDM complex' or mode_solver() == 'semivecTE FDM complex' or mode_solver() == 'semivecTM FDM complex':
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].enableevscan=0"+"\n"
        else:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].enableevscan=1"+"\n"

        fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].mlp.autorun=1"+"\n"
        fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].mlp.speed=0"+"\n"

        if horizontal_symmetry() is None:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.hsymmetry=0"+"\n"
        else:
            if horizontal_symmetry() == 'none':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.hsymmetry=0"+"\n"
            elif horizontal_symmetry() == 'ExSymm':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.hsymmetry=1"+"\n"
            elif horizontal_symmetry() == 'EySymm':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.hsymmetry=2"+"\n"
            else:
                print self.name + '.buildNode(): Invalid horizontal_symmetry. Please use: none, ExSymm, or EySymm'

        if vertical_symmetry() is None:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.vsymmetry=0"+"\n"
        else:
            if vertical_symmetry() == 'none':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.vsymmetry=0"+"\n"
            elif vertical_symmetry() == 'ExSymm':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.vsymmetry=1"+"\n"
            elif vertical_symmetry() == 'EySymm':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.vsymmetry=2"+"\n"
            else:
                print self.name + '.buildNode(): Invalid horizontal_symmetry. Please use: none, ExSymm, or EySymm'
        
        if N() is None:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].mlp.maxnmodes={10}"+"\n"
        else:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].mlp.maxnmodes={"+str(N())+"}"+"\n"

        if NX() is None:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].mlp.nx={60}"+"\n"
            nx_svp = 60
        else:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].mlp.nx={"+str(NX())+"}"+"\n"
            nx_svp = NX()

        if NY() is None:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].mlp.ny={60}"+"\n"
            ny_svp = 60
        else:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].mlp.ny={"+str(NY())+"}"+"\n"
            ny_svp = NY()

        if min_TE_frac() is None:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].mlp.mintefrac={0}"+"\n"
        else:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].mlp.mintefrac={"+str(min_TE_frac())+"}"+"\n"
        
        if max_TE_frac() is None:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].mlp.maxtefrac={100}"+"\n"
        else:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].mlp.maxtefrac={"+str(max_TE_frac())+"}"+"\n"
        
        if min_EV() is None:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].mlp.evend={-1e+050}"+"\n"
        else:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].mlp.evend={"+str(min_EV())+"}"+"\n"
        
        if max_EV() is None:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].mlp.evstart={1e+050}"+"\n"
        else:
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].mlp.evend={"+str(max_EV())+"}"+"\n"

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
            fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.solvid=71"+"\n"
            solverString = self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
        else:
            if mode_solver() == 'vectorial FDM real':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.solvid=71"+"\n"
                solverString = self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif mode_solver() == 'semivecTE FDM real':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.solvid=23"+"\n"
                solverString = self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif mode_solver() == 'semivecTM FDM real':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.solvid=39"+"\n"
                solverString = self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif mode_solver() == 'vectorial FDM complex':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.solvid=79"+"\n"
                solverString = self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif mode_solver() == 'semivecTE FDM complex':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.solvid=31"+"\n"
                solverString = self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif mode_solver() == 'semivecTM FDM complex':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.solvid=47"+"\n"
                solverString = self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.buff=V1 "+str(nx_svp)+" "+str(ny_svp)+" 0 100 "+str(rix_svp)+"\n"
            elif mode_solver() == 'vectorial FMM real':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.solvid=65"+"\n"
                solverString = self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            elif mode_solver() == 'semivecTE FMM real':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.solvid=17"+"\n"
                solverString = self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            elif mode_solver() == 'semivecTM FMM real':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.solvid=33"+"\n"
                solverString = self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            elif mode_solver() == 'vectorial FMM complex':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.solvid=73"+"\n"
                solverString = self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            elif mode_solver() == 'semivecTE FMM complex':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.solvid=25"+"\n"
                solverString = self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            elif mode_solver() == 'semivecTM FMM complex':
                fpString += self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.solvid=41"+"\n"
                solverString = self.nodestring + ".cdev.eltlist[{"+str(2*ii+1)+"}].svp.buff=V2 "+str(n1d_svp)+" "+str(mmatch_svp)+" 1 300 300 15 25 0 5 5"+"\n"
            else:
                print self.name + '.buildNode(): Invalid Mode Solver. Please use: '
                print '    vectorial FDM real, semivecTE FDM real,semivecTM FDM real, '
                print '    vectorial FDM complex, semivecTE FDM complex , semivecTM FDM complex, '
                print '    vectorial FMM real, semivecTE FMM real, semivecTM FMM real, '
                print '    vectorial FMM complex, semivecTE FMM complex, or semivecTM FMM complex'

        fpString += solverString
        
        return fpString
    #end __BuildTaperNode()
    

    
    
    
    ####################################    
    ####################################
    ####        Junk Funcs          ####
    ####################################
    ####################################
    '''Functions that are not used anymore, but were a huge achievement when they were first made,
    so they are kept here for nostalgic purposes only. -- Demis                     '''
        
    
    def __buildNode2(self, name=None, parentNode=None):
        '''Build the Fimmwave node of this Device.
        
        NOTE: This function is deprecated - replaced by buildNode, which re-uses existing waveguide nodes in the fimmwave top-level.
        This function instead re-builds new WG nodes below the Device node and references those.
        
        Parameters
        ----------
        name : string, optional
            Provide a name for this waveguide node.
        parent : Node object, optional
            provide the parent (Project/Device) Node object for this waveguide.'''
        if name: self.name = name
        if parentNode: self.parent = parentNode
        
        self.jointpos = []    # eltlist[] position of simple joints
        self.elementpos = []  # eltlist[] position of each waveguide element
        N_nodes = fimm.Exec("app.subnodes["+str(self.parent.num)+"].numsubnodes()")
        node_num = int(N_nodes)+1
        self.num = node_num
        prj_num = self.parent.num
        node_name = self.name
        
        # build FimmProp device
        fimm.Exec("app.subnodes[{"+str(prj_num)+"}].addsubnode(FPdeviceNode,"+str(node_name)+")"+"\n")
        
        elnum = 0   # element number in the Device
        
        fpString = ""
        
        if DEBUG(): print "Device.buildNode(): ",len(self.elements), self.elements[0], self.elements[1]
        
        for ii,el in enumerate(self.elements):
            elnum = elnum+1
            if DEBUG(): print "Device.buildNode(): %i: type(el)="%(ii), type(el)
            if isinstance(  el, Waveguide  ):
                if DEBUG(): print "Device.buildNode(): __BuildWaveguideNode()"
                print "WARNING: programming of waveguide concatenation in a device is not complete."
                fpString += self.__BuildWaveguideNode( el, elnum )
                self.elementpos.append(elnum)
            elif isinstance(  el, Taper  ):
                if DEBUG(): print "Device.buildNode(): __BuildTaperNode()"
                fpString += self.__BuildTaperNode( el, elnum )
                self.elementpos.append(elnum)
            elif isinstance(  el, Circ  ):
                if DEBUG(): print "Device.buildNode(): __BuildCylNode()"
                fpString += self.__BuildCylNode( el, elnum )
                self.elementpos.append(elnum)
            else:
                raise TypeError("Device.buildNode(): Waveguide Type `" + str( type(el) ) + "` not supported.")
            #end if(el.type)    
            
            # Make the new waveguide node
            fimm.Exec(fpString);    fpString=""
            

            if ii != len(self.elements)-1:
                '''Add a simple joint between waveguides.'''
                elnum = elnum+1
                fpString += self.nodestring + ".cdev.newsjoint("+str(elnum)+")"+"\n"
                # could choose method for the Simple Joint here:
                fpString += self.nodestring + ".cdev.eltlist["+str(elnum)+"].method=0"+"\n"
                self.jointpos.append(elnum)   # add position of this joint to the joints list
            
            # Make the joint
            fimm.Exec(fpString);    fpString=""
            
        #end for(ii,elements)
        
        #fimm.Exec(fpString)
        
        self.built=True
    #end buildNode2()
    
    
    ################################################################
    ##      Cylindrical
    ################################################################

    def __BuildCylNode(self, el, elnum):
        '''Send the FimmProp commands to build a Fiber WG (Cylindrical) Node.
        NOTE: Deprecated - we just reference a previously built WG now instead of building a whole new one under the Device node.
        '''
        if DEBUG(): print "__BuildCylNode():"
        node_num = self.num         # the Device node number
        prj_num = self.parent.num   # the Project node number
        node_name = el.name         # name of Device
        wgtypestr = "fwguideNode"
        
        subnode_num = fimm.Exec( self.nodestring + ".numsubnodes()  " ); 
        subnode_num = int(subnode_num) + 1   # the WG node number under the Device Node
        
        el.subnodenum = subnode_num     # Which subnode the WG is built under; not sure if we'll use this later, but setting it anyway
        el.elnum = elnum                # which element in the Device this WG is used for.
        
        if DEBUG(): print "element info: ", el, el.name, el.subnodenum
          
        fpString=""
        
        '''Create WG Node under dev. node.'''
        if DEBUG(): print "subnode_num=", subnode_num
        fpString += self.nodestring + ".addsubnode("+wgtypestr+","+str(el.name)+")  \n"
        fimm.Exec(fpString); fpString=''
        
        NodeStr = self.nodestring + ".subnodes[{"+str(subnode_num)+"}]"
        self.nodestr = NodeStr
        fimm.Exec(  el.get_buildNode_str(NodeStr )  )   # build the Node using object's own get_buildNodeStr()
        
        
        '''Add this waveguide to the device.'''
        # one of these is dev length, the other is whether to use device or wg params
        num1 = elnum    # position - 1st/left-most is 1, next is 2, next is 3.
        num2 = 1        # 0 = use Device parameters, 1 = use WG parameters
        #####
        fpString += self.nodestring + ".cdev.newwgsect("+str(num1)+","+el.name+","+str(num2)+")  \n"

        
        #if DEBUG(): print "__BuildCylNode(): fpString=\n", fpString
        return fpString
    #end __BuildCylNode2()
    
    

    ################################################################
    ##      Waveguide
    ################################################################

    def __BuildWaveguideNode(self, el, elnum):
        '''FimmProp commands to build a waveguide Node
        NOTE: Deprecated - we now just reference a previously built WG now instead of building a whole new one under the Device node.
        '''
        if DEBUG(): print "__BuildWaveguideNode():"
        node_num = self.num
        prj_num = self.parent.num
        node_name = el.name
        wgtypestr = "rwguideNode"
        
        subnode_num = fimm.Exec( self.nodestring + ".numsubnodes()  " ); 
        subnode_num = int(subnode_num) + 1   # the WG node number under the Device Node
        
        el.subnodenum = subnode_num     # Which subnode the WG is built under; not sure if we'll use this later, but setting it anyway
        el.elnum = elnum                # which element in the Device this WG is used for.
        
        if DEBUG(): print "element info: ", el, el.name, el.subnodenum
          
        fpString=""
        
        '''Create WG Node under dev. node.'''
        if DEBUG(): print "subnode_num=", subnode_num
        fpString += self.nodestring + ".addsubnode("+wgtypestr+","+str(el.name)+")  \n"
        fimm.Exec(fpString); fpString=''
        
        
        NodeStr = self.nodestring + ".subnodes[{"+str(subnode_num)+"}]"
        self.nodestr = NodeStr
        fimm.Exec(  el.get_buildNode_str(NodeStr )  )   # build the Node using object's own get_buildNodeStr()
        
        '''Add this waveguide to the device.'''
        # one of these is dev length, the other is whether to use device or wg params
        num1 = elnum    # position - 1st/left-most is 1, next is 2, next is 3.
        num2 = 1        # 0 = use Device parameters, 1 = use WG parameters
        #####
        fpString += self.nodestring + ".cdev.newwgsect("+str(num1)+","+el.name+","+str(num2)+")  \n"
        # Set the WG length:
        fpString += self.nodestring + ".cdev.eltlist["+str(elnum)+"].length="+str(el.length) + "  \n"
        
        
        return fpString
    #end __BuildWaveguideNode()

#end class(Device)



# Create new Device objects by importing from another Project:
def _import_device( obj='device', project=None, fimmpath=None, name=None, overwrite=False, warn=True ):
    '''This function allows you to use the FimmProp GUI for Device construction, and then interact with those Devices via pyFIMM (acquiring fields, saving plots etc.).
    The Device's parent Project should have been created in pyFIMM beforehand.  To grab a Device from a file, use `newprj = pyFIMM.import_Project()` to generate the Project from a file, and then call `newprj.import_Device()`.
    
    If this function is called as a method of a pyFIMM Project object (`ProjectObj.import_device()`) then the target FimmProp Device will be copied into the calling pyFIMM Project's corresponding FimmProp project, and the device returned will point to that.
    To ensure the imported Device can reference the needed Waveguides/Slabs from the original Project, it is easiest if the required waveguide/slab nodes are subnodes of the original device node - they will then be copied automatically into the new Project.  If this is not possible, first use the function `Project.import_Node()` to copy the required FimmProp Nodes into the calling Project.
    
    import_device() will not load the elements and waveguides used in the Device's construction.  This is to enable the use of the many complex element types available in FimmProp that aren't supported by pyFIMM - for example etch/grow paths, various types of joints etc.  These specialized elements/joints won't be inspected by pyFIMM, but you can still insert your Device into other Devices, launch/retrieve fields etc. via pyFIMM.
    Device.get_origin() will return 'fimm' for this new Device, indicating that it was constructed in FimmWave and the elements it contains will not correspond to pyFIMM waveguide objects.

    
    Parameters
    ----------
    target : { 'device' | Project object }, optional
        If this func is called from within a Project object, this argument is set to the parent Project object, ie. `self`.  The function will then attempt to copy the FimmProp Device into the calling FimmProp Project.
        If the string 'device' is passed, the function will return a new Device object without copying the FimmWave nodes - leaving the Device in it's original FimmProp Project.
    
    project : pyFIMM Project object, required
        Specify the pyFIMM Project from which to acquire the Device.

    fimmpath : string, required
        The FimmProp path to the Device, within the specified project.  This takes the form of something like "DevName" if the device named "DevName" is at the top-level of the FimmProp Project, or "NodeName/SubDevName" is SubDevName is under another Node.
    
    name : string, optional
    Optionally provide a name for the new Device node in Fimmwave.  If omitted, the name found in the Project will be used.

    overwrite : { True | False }, optional
        If True, will overwrite an existing Fimmwave Device if Fimmwave reports a name-conflict.  If False, will append random digits to the to Device's name.  False by default.

    warn : { True | False }, optional
        Print or suppress warnings when nodes will be overwritten etc.  True by default.


    Parameters of the returned Device are a bit different from one generated entirely by pyFIMM, as detialed below:
    Please type `dir(DeviceObj)` or `help(DeviceObj)` to see all the attributes and methods available.
    
    Attributes
    ----------
    The returned Device object will most of the same attributes as a standard pyFIMM Device object, with the following exceptions:
    
    DevObj.origin : { 'fimmwave' }
        This indicates that this Device was Not constructed by pyFIMM, and so has a slightly lacking set of attributes (detailed further in this section).  A normally-constructed pyFIMM Device has the value 'pyfimm'.
    
    DevObj.num : nonexistent
        Instead, use the attribute `DevObj.nodestring` to reference the device object in FimmWave.

    DevObj.elements : (empty list)
        To allow for all the various Element construction methods available in FimmWave (eg. etch/grow paths etc.), pyFIMM will not populate the elements list of the imported Device.
        However, `.elementpos` and `.jointpos` will be populated properly so that you can differentiate between joints and waveguide elements.  Note that Free-Space joints will be added to `*.elementpos` despite being in the "joints" section of the FimmProp GUI, because they have a length and are thus more appropriately treated as finite-length elements.
    
    DevObj.elementpos : list
        List of element positions (used in FimmProp's `DevNode.cdev.eltlist[%i]`) for referencing a particular element.  Elements that are references will have an entry corresponding to the original element.
        
    DevObj.lengths : list
        The length, in microns, of each element that can have a length (these elements are referenced in `DevObj.elementpos`).  Unsupported elements, such as the WGLens (which don't have a simple calculation of length) will have a `None` entry in the list.
    
    DevObj.jointpos : list
        List of positions (used in FimmProp's `DevNode.cdev.eltlist[%i]`) of joints that have no length, eg. Simple-Joints, IO-Sections.



    Examples
    --------
    To open a Device from a file, import the project file first:
        >> prj = pyfimm.import_project( 'C:\pyFIMM Simulations\example4 - WG Device 1.prj' )
    
    Create a new pyFIMM Device pointing to the FimmProp Device in the imported Project:
        >>> DevObj = pyfimm.import_device( prj,  "Name Of My Device In The Project" )
    The string "Name Of..." as actually a FimmWave path, so could reference subnodes like "ParentDev/TheDeviceIWant".
    
    Or copy the Device into a new pyFIMM Project:
        >>> prj2 = pyfimm.Project( 'New PyFIMM Project', build=True )
        >>> DevObj = prj2.import_device( prj,  "Name Of My Device In The Project" )
    
    If the Device relies on other waveguides & slabs, it's easiest if those WGs/slabs are stroed as SubNodes of the Device to copy, such that they are copied along with the Device.  If they aren't stored as SubNodes, then you'll want to import those dependency nodes individually via `Project.import_node()`.
    '''
    
    '''Note that `obj` will be a Project object, if this function is called from the Project object's methods'''
    
    if (project is None) or (fimmpath is None):
        ErrStr = "import_device(): The `project` and `fimmpath` arguments are required! Please specify these parameters."
        raise ValueError( ErrStr )
    
    if DEBUG(): print "import_device( project.name='%s', fimmpath='%s' )"%(project.name, fimmpath)
    
    dev = Device()      # new pyFIMM Device object
    dev.elements = None
    dev.num = None
    dev.set_parent( project )
    dev.origin = 'fimmwave'   # Device was constructed in FimmProp, not pyFIMM
    dev.name = fimmpath.split('/')[-1]      # get the last part of the path

    devname = "Device_%i" %(  get_next_refnum()  )  # generate dev reference name
    # create fimmwave reference to the Device:
    if DEBUG(): print "Ref& %s = "%(devname) + project.nodestring + ".findnode(%s)"%(fimmpath)
    ret = fimm.Exec( "Ref& %s = "%(devname) + project.nodestring + ".findnode(%s)"%(fimmpath)   )
    ret = strip_txt( ret )
    if DEBUG(): print "\tReturned:\n%s"%(ret)
    dev.nodestring = devname    # use this to reference the device in Fimmwave

    ret = strip_txt(  fimm.Exec( '%s.objtype'%(dev.nodestring) )  )
    if ret != 'FPDeviceNode':
        ErrStr = "The referenced node `%s` is not a FimmProp Device or couldn't be found!\n\t"%(fimmpath) + "FimmWave returned object type of:\n\t`%s`."%(ret)
        raise ValueError(ErrStr)
    
    if isinstance( obj, Project):
        '''This Function was called as a method of the Project object'''
        # copy the Device into this project:
        fimm.Exec( dev.nodestring + ".copy()" )     # copy to system clipboard
        
        #   update device's references:
        dev.set_parent(obj)
        N_nodes = fimm.Exec(obj.nodestring+".numsubnodes()")
        dev.num = int(N_nodes)+1
        dev.nodestring = obj.nodestring + ".subnodes[%i]"%(dev.num)
        
        #   check node name, overwrite existing/modify dev's name Dev if needed:
        dev.name, samenodenum = check_node_name( dev.name, nodestring=obj.nodestring, overwrite=overwrite, warn=warn )    
        fimm.Exec( obj.nodestring + '.paste( "%s" )'%(dev.name)  ) # paste into this project
    
    
    dev.built = True
    
    
    # Populate device parameters:
    dev.__wavelength = fimm.Exec(  "%s.lambda"%(dev.nodestring)  )
    if DEBUG(): print dev.name + ".__wavelength = ", dev.__wavelength, str(type(dev.__wavelength))

    els = strip_array(   fimm.Exec( "%s.cdev.eltlist"%(dev.nodestring) )    )    # get list of elements
    if DEBUG(): print "els =", els

    for   i, el    in enumerate(els):
        elnum=i+1
        objtype = strip_text(    fimm.Exec(  dev.nodestring + ".cdev.eltlist[%i].objtype"%(elnum)  )    )
        if objtype.strip()=='FPsimpleJoint' or objtype == 'FPioSection':
            '''SimpleJoints,IOports have no length'''
            if DEBUG(): print "Element %i is Joint: %s"%(elnum, objtype)
            dev.jointpos.append(elnum)
        elif objtype == 'FPRefSection':
            ''' This element references another element '''
            refpos = int( fimm.Exec(  dev.nodestring + ".cdev.eltlist[%i].getrefid()"%(elnum)  )  )
            if DEBUG(): print "Element %i is reference --> Element %i."%(elnum, refpos)
            dev.elementpos.append( refpos )     # Append the position of the Original!
            dev.lengths.append(  fimm.Exec( dev.nodestring + ".cdev.eltlist[%i].length"%(refpos)  )    )
            if DEBUG(): print "Element %i: Length = "%(elnum)  , dev.lengths[-1]
        elif objtype.lower().endswith('section') or objtype.strip() == 'FPtaper' or objtype.strip() == 'FPfspaceJoint' or objtype.strip() == 'FPbend':
            ''' Regular Section with a `*.length` attribute, including regular WG/Planar Sections'''
            if DEBUG(): print "Element %i is Section of type: %s"%(elnum, objtype)
            dev.elementpos.append(elnum)
            dev.lengths.append(  fimm.Exec( dev.nodestring + ".cdev.eltlist[%i].length"%(elnum)  )    )
            if DEBUG(): print "Element %i: Length = "%(elnum)  , dev.lengths[-1]
        else:
            '''Eg. Lens =  FPWGLens; can't get the length simply'''
            print "WARNING: Element %i: "%(elnum) + "Unsupported Element Type:", objtype
            dev.elementpos.append(elnum)
            dev.lengths.append( None )
    
        #if DEBUG(): print "%i: elementpos = ", dev.elementpos, "   & jointpos = ", dev.jointpos
    #end for(elements)
    
    
    return dev
    
    ''' Techniques in FimmProp to do the above:
    Let FimMWave find the node for us:
    Ref& R = app.subnodes[1].findnode(WG Device) - no quotes, or double-quotes!

    R.objtype
    FPDeviceNode

    Do need to distinguish the elements,
        - which are joints (jointpos) and which are elements
        - in Dev.elements, insert dummy-Section?  When interrogates, returns Warning "Loaded form external file"
    determine each element's length
    determine total device length
    Do NOT look inside each element - obviates ability to make paths etc.

    Var wg=app.subnodes[1].subnodes[3].cdev.getwg(0)
    could not find item "Var wg"

app.subnodes[1].subnodes[3].cdev.getwg(0)
app.subnodes[1].subnodes[3].cdev.eltlist

         eltlist[1]     
         eltlist[2]     
         eltlist[3]     

app.subnodes[1].subnodes[3].cdev.eltlist[3].length
    15

app.subnodes[1].subnodes[3].cdev.eltlist[2].length
    could not find item "app.subnodes[1].subnodes[3].cdev.eltlist[2].length"

app.subnodes[1].subnodes[3].cdev.eltlist[1].length
    10

>>> pf.Exec("app.subnodes[1].subnodes[3].cdev.eltlist")
[None, 'eltlist[1]', 'eltlist[2]', 'eltlist[3]']

app.subnodes[1].subnodes[3].cdev.eltlist[1].objtype
    FPWGsection

app.subnodes[1].subnodes[3].cdev.eltlist[2].objtype
    FPsimpleJoint

>>> pf.Exec("app.subnodes[1].subnodes[3].cdev.eltlist[2].objtype")
'FPsimpleJoint'


### FOr referenced section:
Device_187734.cdev.eltlist[3].objtype
    FPRefSection

Device_187734.cdev.eltlist[3].length
    could not find item "Device_187734.cdev.eltlist[3].length"

Device_187734.cdev.eltlist[3].getrefid()
    1

###################

    # import into the project:
    Device_187734.copy()

    NewProj{aka. self}.nodestring + '.paste("%s")'%(Device_187734.name)
    
    !!!-->  Update nodenumber of Device & nodestring  (always pasted at end)
    
    '''

#end import_device()

# Alias to the same function, added to the Project object:
Project.import_device = _import_device


def import_device(project, fimmpath, name=None, overwrite=False, warn=True ):
    ''' Please see `help(pyfimm._import_device)` for complete help, the following is only partial documentation.
    This function will return a new pyFIMM Device object pointing to a Device that exists in an imported Project (ie. one created in FimmProp & loaded from a file, rather than via pyFIMM).
    This allows you to use the FimmProp GUI for Device construction, and then interact with those Devices via pyFIMM (acquiring fields, saving plots etc.).
    
    
    Parameters
    ----------
    project : pyFIMM Project object, required
        Specify the pyFIMM Project from which to acquire the Device.

    fimmpath : string, required
        The FimmProp path to the Device, within the specified project.  This takes the form of something like "DevName" if the device named "DevName" is at the top-level of the FimmProp Project, or "NodeName/SubDevName" is SubDevName is under another Node.
    
    name : string, optional
    Optionally provide a name for the new Device node in Fimmwave.  If omitted, the name found in the Project will be used.

    '''
    return _import_device('device', project, fimmpath, name=None, overwrite=False, warn=warn )