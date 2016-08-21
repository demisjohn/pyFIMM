'''

Cavity Calculation functions
Demis D. John, 2015, Praevium Research Inc.
Based on Peter Beinstman's CAMFR package's `Cavity` class, 
and Vincent Brulis' CavityModeCalc.py example script.


'''

from __globals import *         # import global vars & FimmWave connection object
# DEBUG() variable is also set in __globals

import numpy as np
import math

from __pyfimm import get_N, set_wavelength         # get number of calculated modes
from __CavityMode import *          # import the CavityMode class, for `Cavity.mode(0)...`

class Cavity(object):
    '''Cavity class, for calculating cavity modes & fields.
    
    Construct as so:
    cav = <pyfimm>.Cavity( LHS_Dev, RHS_Dev )
    
    Parameters
    ----------
    LHS_Dev : Device object
        Device representing the left-hand side of the cavity.
    
    RHS_Dev : Device object
        Device representing the right-hand side of the cavity.
    
    IMPORTANT NOTE: Wherever you choose to split the cavity (arbitrary), the waveguide cross-section on either side of the split must be the same. For example, for whichever waveguide is near the desired splitting point, cut that waveguide in half, with half in the LHS_Dev & half in the RHS_Dev, so that the waveguide cross section on either side of the split is the same.  
    This is so that the modal basis set of each half of the cavity will be the same - ie. the eigenvectors calculated will be with respect to the modes of these central waveguides, and if each side's central waveguide had different modes (because they were different waveguide geometries), the eigenvector would not represent the same superposition of modes into each RHS & LHS device.
    
    
    Attributes
    ----------
    LHS_Dev : Device Object
        Left Side Device.  Should already have been built via LHS_Dev.buildNode() in FimmWave.
    
    RHS_Dev : Device Object
        Right Side Device.  Should already have been built via RHS_Dev.buildNode() in FimmWave.
    
    
    Methods
    -------
    
    This is a partial list - see `dir(CavityObj)` to see all methods.
    Please see help on a specific function via `help(Cavity.theFunc)` for detailed up-to-date info on accepted arguments etc.
    
    calc( WLs , Display=False) 
        Calculate the eigenmodes of the cavity at each wavelength.  Based on Vincent Brulis' script from the PhotonDesign example "Modelling a passive optical cavity (VCSEL, DFB)".
        WLs : array-like
            List of wavelengths at which to calculate the cavity modes.  This determines the wavelength-accuracy of the resonance wavelengths found - you will have to choose the wavelengths at which to calculate the modes.
        See help(Cavity.calc) for more info.
    
    plot() - DEPRECATED
        Plot the Eigenvalues versus Wavelength for all modes.
        This function has been deprecated - use `Cavity.mode('all').plot()` to do the same thing.
    
    
    
    After CavityObj.calc() has been performed, more attributes are available:
    
    Attributes
    ----------
    
    wavelengths : numpy array
        The wavelengths at which cavity eigenvalues were calculated.
    
    eigenvalues, eigenvectors : numpy arrays
        The eigenvalues & eigenvectors at each wavelength.  There will be N eigenvalues at each wavelength, corresponding to each lateral optical mode of the central Waveguide making up the Devices (the WG at the split).
        The eigenvalues are the (complex) magnitude & phase that would be applied to a field after a roundtrip in the cavity.  Thus a negative magnitude means the field decays each roundtrip (radiation loss or something), and a Zero-phase means the field is in-phase with itself (resonant) and can constructively interfere with itself after a round-trip.
        The eigenvectors are the magnitudes/coefficients of each mode in the basis set (the modes of the central-section WG) to get the above eigenvalues.  You would launch the central-section modes at these magnitudes/phases to produce the optical fields corresponding to the eigenvalue (to get that round-trip amplitude & phase).
        For eigenvalues & eigenvectors, indexing is like so:
            >>> eigenvalues[Iwavelength][Imodenum]
        Where `wavelengths[Iwavelength]` tells you which wavelength you're inspecting, and `Imodenum` tells you which mode number you're inspecting.
    
    resWLs , resEigVals, resEigVects : list of complex floats
        The Resonance wavelengths and corresponding EigenValues & EigenVectors (complex numbers).
        Each list index corresponds to a cavity mode with unique lateral mode-profile, and there may be multiple resonances found for each mode.  If no resonances were located, `None` is entered into the list for that mode.
        Indexing is similar to `eigenvalues` & `eigenvectors`
    
    pseudo-attributes:
    mode(N) : select one or more cavity modes to extract data for, or pass the string 'all' to work with all modes.  This actually (invisibly to the user) returns a `CavityMode` object, which can perform other actions on the selected mode.  
        See `help(CavityObj.mode('all')` or`help(CavityMode)`  for more info on the usage & attributes/methods available.
    
    
    Examples
    --------
    
    Make the left & right hand side devices, with 20 periods of repeating waveguides.  Note that the last waveguide in LHS is the same as the first waveguide in RHS.  Location of the split and thickness on either side is arbitrary.
    >>> LHS = <pyfimm>.Device(   20*( WG2(0.275) + WG3(0.125) )  + WG1(0.05)  )
    >>> RHS = <pyfimm>.Device(   WG1(0.05) +  20*( WG2(0.275) + WG3(0.125) )  )
    
    >>> Cav = <pyfimm>.Cavity( LHS, RHS )       # Define the cavity
    
    >>> WLs = numpy.array( [1.490, 1.495, 1.500, 1.505, 1.510] )
    >>> Cav.calc( WLs )     # Sweep the wavelength and calculate the eigenmodes
    
    >>> Cav.mode(0).plot()      # plot the eigenvalues for the first lateral mode
    >>> Cav.mode([0,1,2]).plot()      # plot the eigenvalues for the first three lateral modes
    >>> Cav.mode('all').plot()      # plot the eigenvalues for all modes
    >>> Cav.mode(0).plot('Ex')      # plot the Ex electric field vs. Z for resonance of lateral Mode #0.
    >>> print Cav.get_resonance_wavelengths()        # print the resonance wavelengths
    '''
    
    def __init__(self, *args, **kwargs):
        '''Please see help(Cavity) for usage info.'''
        
        #if DEBUG(): print "Cavity() connection test: " + str(fimm.Exec("app.numsubnodes()"))
        
        if len(args) >= 2:
            self.LHS_Dev = args[0]
            self.RHS_Dev = args[1]
            self.name = "Cavity(%s/%s)"%(self.LHS_Dev.name, self.RHS_Dev.name)
        else:
            raise ValueError("Invalid Number of arguments to Cavity constructor - expected exactly 2 Device objects.")
        
        ## Should check that LHS & RHS sections have same central cross-section
        
        if kwargs:
            '''If there are unused key-word arguments'''
            ErrStr = "WARNING: Cavity(): Unrecognized keywords provided: {"
            for k in kwargs.iterkeys():
                ErrStr += "'" + k + "', "
            ErrStr += "}.    Continuing..."
            print ErrStr
    #end __init__
    
    
    def __str__(self):
        ''' How to `print` this object.'''
        string= 10*"-" + " Left-Hand Device " + 10*"-" + "\n"
        string += str(LHS_Dev)
        string= 10*"-" + " Right-Hand Device " + 10*"-" + "\n"
        string += str(RHS_Dev)
        return string
    #end __str__
    
    
    def buildNode(self, parent=None, overwrite=False, warn=True, build=True):
        '''If either of the two constituent Devices passed haven't been built, they will now have their nodes built.
        
        Parameters
        ----------
        parent : Node object, optional
            Provide the parent (Project/Device) Node object for this waveguide.

        build : { True | False }, optional
            If either of the constituent Devices aren't built, attempt to call their `buildNode` method.
        
        overwrite : { True | False }, optional
            Overwrite existing Device node of same name?  Defaults to False, which will rename the node if it has the same name as an existing node.
        
        warn : {True | False}, optional
            Print notification if overwriting a node/building this Cavity?  True by default.
        '''
        if warn: print "WARNING: Cavity.buildNode(): Cavity is not a FimmWave node, just a pyFimm virtual-object, so there is nothing to build in FimmWave for this Cavity.  The constituent FimmWave Devices will now attempt to be built."
        if parent: self.parent = parent
        if not self.LHS_Dev.built: self.LHS_Dev.buildNode(name='LHS', parent=self.parent, overwrite=overwrite, warn=warn)
        if not self.RHS_Dev.built: self.RHS_Dev.buildNode(name='RHS', parent=self.parent, overwrite=overwrite, warn=warn)
    #end buildNode()
    
    
    def calc(self, WLs, Display=False):
        '''Calculate the scattering matrices and eigenvalues of the cavity.
        Based on PhotonDesign's Example "Modelling a passive optical cavity (VCSEL, DFB)" & the accompanying Python script by Vincent Brulis at Photon Design, 2014.
        
        Parameters
        ----------
        WLs : list/array of floats
            List of wavelengths at which to calculate the cavity eigenvalues.  This determines the wavelength-accuracy of the resonance wavelengths found - you will have to choose the wavelengths at which to calculate the modes.
        
        Display : { True | False }, optional
            Display the calculated eigenvalues during wavelength sweep?  This allows the user to copy/paste the results, rather than using the internally generated attributes, below.  Defaults to False.
        
        Returns
        -------
        Nothing is directly returned by this operation, but new attributes of the Cavity object will be available after calc() is called.  These new attributes are:
        
        wavelengths : 2-D list of floats
            The wavelengths at which eigenvalues were calculated. This is a direct copy of the `WLs` array passed to the calc() function.
        
        eigenvalues, eigenvectors : 2-D list of floats
            The complex eigenvalues & eigenvectors at each of the calculated wavelengths. First dimension of the array is to choose lateral cavity mode (up to get_N() ).  eg.  [   [EigV_mode0_WL0, EigV_mode0_WL1, ... EigV_mode0_WLN],  [EigV_mode1_WL0, EigV_mode1_WL1, ... EigV_mode1_WLN],    ... ,   [EigV_modeN_WL0, EigV_modeN_WL1, ... EigV_modeN_WLN]    ]
            The imaginary part of the eigenvalue corresponds to the round-trip optical phase, and the real part corresponds to the cavity loss.  The eigenvectors are vectors containing the amplitudes of each mode required to attain the corresponding eigenvalue, and they can be input directly into a Device via `Device.set_input( <vector> )`.
            
        
        resonance_wavelengths, resonance_eigenvalues, resonance_eigenvectors : 2-D list of floats
            The wavelengths & corresponding eigenvalues/vectors for cavity resonances, if any.  First dimension is to choose lateral mode (up to get_N() ), identical to eigvals. `None` will be entered into the list for any modes that do not show a resonance.
            Resonance is located by determining at which wavelength imag(eigenvalue) is closest to zero & real(eigenvalue) is positive.  The strongest resonance will show the maximum real(eigenvalue).
        
        The Cavity device will have the attributes `CavityObj.S_RHS_ll` & `CavityObj.S_LHS_rr` added, which are the left-to-left & right-to-right scattering matrices for the Right & Left devices, respectively (with reflections pointing at the central split).  
        Also the attribute `CavityObj.S_RT` will contain the round-trip scattering matrix, as viewd from the cavity split.  This is simplt the dot-product of S_RHS_ll & S_LHS_rr.
        
        
        Examples
        -------
        Calculate cavity modes in the range of wavelengths from 990nm to 1200nm:
            >>> CavityObject.calc(  numpy.arange( 0.990, 1.200, 0.01 )  )
        or just at a few wavelengths:
            >>> CavityObject.calc(  [1.000, 1.050, 1.110]  )
        
        Calculated eigenvalues can be accessed in the resulting numpy.array:
            >>> CavityObj.eigenvalues
        This is an array with eigenvalues for each mode, with the form 
            [   [EigsMode0], [EigsMode1], [EigsMode2], ..... [EigsModeN]   ]
        so len( CavityObj.eigenvalues ) == NumModes = pyFIMM.get_N()
        
        use pyFIMM.set_N(num_modes) to set the number of lateral waveguide modes to include in the calculation.
        '''
        self.wavelengths = np.array(WLs)
        self.eigenvalues, self.eigenvectors = self.__CavityModeCalc( self.LHS_Dev, self.RHS_Dev, WLs , Display=Display)       # The main calculation function/loop
        self.resWLs, self.resEigVals, self.resEigVects, self.resLosses = self.__FindResonance( get_N() )
        
        #return self.eigenvalues
    #end calc()
    
    
    
    def mode(self, num):
        '''Select a lateral mode to work on.  Defaults to 'all' modes.
        
        Parameters
        ----------
        num : int, list of int's, or 'all'
            If an integer is passed, that lateral mode is selected.  If the string "all" is passed, the functions will attempt to return data for all modes calculated, when applicable. 
            
        Technically, this method returns a CavityMode object, so to find out what methods/attributes you can perform on `CavityObj.mode(0)`, type `help(pyfimm.CavityMode)` or simply `help( CavityObj.mode(0) )`
        '''
        return CavityMode(self, num)    # return CavityMode object
    
    
    def get_length(self):
        '''Get the total length of this Cavity.'''
        return  self.LHS_Dev.get_length() + self.RHS_Dev.get_length()
    
    
    def __ploteigs(self, ):
        '''DECPRECATED: Cavity.ploteigs() is replaced by `Cavity.mode('all').plot()`, so the code is now in the __CavityMode.py module
        
        Plot the Eigenvalues for all modes at each wavelength.  
        
        Real parts plotted with '-x' & imaginary parts plotted with '-o'.
        
        Returns
        -------
        handles : tuple of (fig1, ax1, ax2, l1, leg1, l2, leg2 )
            Returns handles to the plot's objects, as so:
            fig1 : main figure object
            ax1 : primary (right) axis, for the Real part of the Eigenvalues.
            ax2 : secondary (left) axis, for the Imaginary part of the Eigenvalues.
            l1 : list of line objects, for the Real part of the Eigenvalues.
            leg1 : legend strings for lines in l1, for the Real part of the Eigenvalues.
            l2 : list of line objects, for the Imaginary part of the Eigenvalues.
            leg2 : legend strings for lines in l2, for the Imaginary part of the Eigenvalues.
            
        '''
        
        print "WARNING: Cavity.ploteigs() is being deprecated - please use `Cavity.mode('all').plot()` instead"
        import matplotlib.pyplot as plt
        
        if len(self.eigenvalues) == 0: raise UserWarning("No Cavity modes found!  Cavity modes not calculated yet? Please run Cavity.calc() to do so.")
        
        EigsArray = self.eigenvalues
        WLs = self.wavelengths
        
        fig1, ax1 = plt.subplots(1, 1)
        box = ax1.get_position()
        ax1.set_position([ box.x0, box.y0, box.width * 0.8, box.height])    # reduce axis width to 80%, to make space for legend
        ax2 = ax1.twinx()

        # print EigenVector for each mode:
        l1 = []; l2 = []; leg1 = []; leg2=[]
        for i in range( EigsArray.shape[1] ):
            print "%i: "%i, 
            l1.append(  ax1.plot(WLs, EigsArray[:,i].real, '-x', label="Mode "+str(i)+": real")  )
            leg1txt.append("Mode "+str(i)+": real")
            l2.append(  ax2.plot(WLs, EigsArray[:,i].imag, '-o', label="Mode "+str(i)+": imag")  )
            leg2txt.append("Mode "+str(i)+": imag")

        #ax1.plot(WLs, EigsArray[:,0].real, label="Mode "+str(i)+": real")
        #ax2.plot(WLs, EigsArray[:,0].imag, label="Mode "+str(i)+": imag")

        ax1.set_xlabel(r"Wavelength, ($\mu{}m$)")
        ax1.set_ylabel("Real")
        ax2.set_ylabel("Imaginary")
        ax1.set_title("Cavity Eigenvalues")
        #plt.legend()
        
        leg = ax1.legend( (l1, l2), (leg1txt, leg2txt), loc='upper left', bbox_to_anchor=(1, 1) , fontsize='small' )

        fig1.canvas.draw(); fig1.show()
        return fig1, ax1, ax2, l1, l2, leg
    #end ploteigs
    
    
    
    def get_refractive_index(self, zpoints=3000, zmin=0.0, zmax=None, xcut=0.0, ycut=0.0, calc=True):
        '''Calls `Dev.get_field('index')` of each sub-Device to return the refractive index of the device, and then concatenates them appropriately.  The `component` & `direction` options have been removed as compared with `get_field()`.
        
        See `help(Device.field)` for info on the other options.
        '''
        zptsL=int(zpoints/2.); zptsR=np.round(zpoints/2.)
        
        Lfield = self.LHS_Dev.get_field('rix', zpoints=zptsL, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut, direction='total', calc=calc)
        Rfield = self.RHS_Dev.get_field('rix', zpoints=zptsR, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut, direction='total', calc=calc)
        Lfield.extend(Rfield)   # concatenate the L+R fields
        return Lfield
    #end get_refractive_index()
        
    
    def plot_refractive_index(self, zpoints=3000, zmin=0.0, zmax=None, xcut=0.0, ycut=0.0, calc=True, return_handles=False, title=None):
        '''Plot the refractive index versus Z.  
        
        return_handles = { True | False }, optional
            If True, will return handles to the figure, axes, legends and lines.  False by default.
    
        title = str, optional
            Pre-pend some text to the plot title.
        
        Other options are passed to `Dev.get_field()` of the two constituent Devices that make up this Cavity, so see `help(Device.field)` for info on the other options.
        '''
        import matplotlib.pyplot as plt     # to create new figure
        
        rix = self.get_refractive_index(zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut, calc=calc)
        z = np.linspace( 0, self.get_length(), num=len(rix) )   # Z-coord
        
        
        fig1, ax1 = plt.subplots(1, 1)      # 1 axis
        l1 =  [ ax1.plot(z, np.array(rix).real, 'g-', label="Refractive Index" ) ]      # plot
        
        ax1.set_ylabel( "Refractive Index" )
        titlestr = self.name + ": Refractive Index vs. Z"
        if title: titlestr = title + ": " + titlestr
        ax1.set_title(  titlestr  )
        ax1.grid(axis='both')
        #plt.legend()        
        ax1.set_xlabel(r"Z, ($\mu{}m$)")
        
        #leg = plt.legend()
        #leg = ax1.legend( loc='upper left', bbox_to_anchor=(1, 1) , fontsize='small' )
        #leg2 = ax2.legend( loc='upper left', bbox_to_anchor=(1, 1) , fontsize='small' )
    
        fig1.canvas.draw(); fig1.show()
        
        # return some figure handles
        if return_handles:     
            return fig1, ax1, l1
    #end plot_refractive_index()
    
    


    def __CavityModeCalc(self, LHS, RHS, scan_wavelengths, OverlapThreshold=0.95, Display=False):
        '''Cavity Mode Calculator
        Based on PhotonDesign's Example "Modelling a passive optical cavity (VCSEL, DFB)"
        Python script by Vincent Brulis at Photon Design, 2014; heavily modified by Demis D. John to incorporate into pyFIMM.
    
        Parameters
        ----------
        LHS : Left-hand Side Device object
        
        RHS : Right-hand Side Device object
        
        WL_range : array-like
            Wavelengths to solve for as list, array or similar (any iterable).
        
        OverlapThreshold : float, optional
            If the overlap between the eigenvector and the mode is above this threshold, we will consider this eigenvector to represent this mode number. Default= 0.95.  This is important when sorting the eigenvectors, as numpy sorts the eigenproblem's solutions by the eigenvalue, while we would prefer to sort them based on which waveguide mode they represent.
        
        Display : { True | False }, optional
            Print the calculated eigenvalues during wavelength sweep?  Defaults to False.  Useful for copy/pasting the data into a text file.
        
        
        Returns
        -------
        (eigenvals, eigenvects)
        
        eigenvals : numpy array
            Calculated eigenvalues at each wavelength as a numpy.array with eigenvalues for each waveguide mode, with the form 
                [   [EigsMode0, EigsMode1, EigsMode2, ..... EigsModeN]        <-- 1st wavelength in scan_wavelengths
                    [EigsMode0, EigsMode1, EigsMode2, ..... EigsModeN]        <-- 2nd wavelength in scan_wavelengths
                    ...
                    [EigsMode0, EigsMode1, EigsMode2, ..... EigsModeN]   ]    <-- last wavelength in scan_wavelengths
                so len( CavityObj.eigenvalues ) == NumModes = pyFIMM.get_N()
        
        eigenvects : numpy array
            The calculated eigenvectors - amplitude/phase coefficients for each calc'd mode in the central section to achieve the above eigenvalues.  Similar format as eigenvects.  These can be launched via `DeviceObj.set_input()`.

        Adds the following attributes to the Cavity object:
        S_RHS_ll, S_LHS,rr: lists
            Scattering matrices as viewed from teh cavity split, for the RHS reflection (ll) and LHS reflection (rr).

        S_RT : list
            Scattering matrix for the round-trip, which is simply the dot-product of S_RHS_ll & S_LHS_rr.
        '''
        import sys  # for progress bar
        nWLs = len(scan_wavelengths)    # Number of WLs.
        
        #Nguided=0 #dimension of the truncated eigenmatrix, should be set to number of guided modes, please set to 0 to solve the eigenproblem for all the modes
        #OverlapThreshold = 0.95 # if the overlap between the eigenvector and the mode is above this threshold, we will consider them identical
        
        self.__FPList = []
        self.__pathFPList = []
        self.__projFPList = []
        self.__ProjList = []
        self.__pathProjList = []
        self.__PDnames = []
        self.__PDpath = []
        self.__PDproj = []
        self.__eigen_imag = []
        self.__eigen_real = []
        
        
        fimm.Exec("Ref& parent = app")

        n = len(self.__FPList)

        fimm.Exec("Ref& fpLHS = " + LHS.nodestring)

        fimm.Exec("Ref& fpRHS = " + RHS.nodestring)
        
        
        # At this stage we will retrieve the number of modes in the central section

        N=fimm.Exec("fpRHS.cdev.eltlist[1].mlp.maxnmodes")  # could replace with `self.RHS.element...`
        while 1:
            try:
                N = int(N)  # check if numerical value returned
                
                break
            except ValueError:
                print self.name + ".calc:CavityModeCalc(): WARNING: Could not identify how many modes are calculated in the cavity, using get_N()"
                N = get_N()

        #if DEBUG(): print "CMC(): N={}".format(N)

        """
        if (Nguided==0):
            '''Hard-coded so Nguided=0'''
            Nguided=N
        """

        # for printing our the eigenvectros/values:
        Ndisplay = N   # we want to display all the modes

        labels = "lambda "
        for i in range(0,Ndisplay,1):
            labels = labels + "real_mode" + str(i+1) + " imag_mode" + str(i+1) + " "
        #print labels


        # mode 1: scan wavelength <-- This is the only mode this script currently runs in
        # we will display all the modes, ranked by waveguide mode 

        EigVect = []        ## To save the EigenVectors vs. wavelength
        EigVal = []
        
        # Progress Bar setup:
        ProgMax = 20    # number of dots in progress bar
        if nWLs<ProgMax:   ProgMax = nWLs
        print "\n|" +    ProgMax * "-"    + "|     Cavity.calc() progress"
        sys.stdout.write('|'); sys.stdout.flush();	# print start of progress bar
        nProg = 0   # progress bar - fraction of progress
        
        for step,wavelength   in   enumerate(scan_wavelengths):
            ''' `step` goes from 0-->len(scan_wavelengths).  
                `wavelength` is the actual WL value.    '''
            
            '''scan_wavelengths is already array-like, no need to construct wavelength at each step    '''
            #wavelength = wavelength_min + step*(wavelength_max - wavelength_min)/wavelength_steps
            
            
            fimm.Exec("fpRHS.lambda="+str(wavelength))  # set Device-specific wavelength
            fimm.Exec("fpLHS.lambda="+str(wavelength))
            # this reset is an attempt to prevent memory issues
            fimm.Exec("fpRHS.reset1()")
            fimm.Exec("fpLHS.reset1()")
            fimm.Exec("fpRHS.update()")   # calc the Scattering Matrix
            RRHS = np.zeros([N,N],dtype=complex)
            SMAT = []
            for i in range(1,N+1,1):
                ''' Get Left-to-Left (reflecting) scattering matrix for Right-hand-side of cavity, for each WG mode.'''
                SMAT.append(   fimm.Exec("fpRHS.cdev.smat.ll["+str(i)+"]")   )
            for i in range(1,N+1,1):
                for k in range(1,N+1,1):
                    RRHS[i-1][k-1] = SMAT[i-1][k] # the index "k" is due to the fact that the first element of each line is "None"
            #print "RRHS:" # temp
            #print RRHS # temp
            
            
            self.S_RHS_ll = RRHS # store the left-to-left scattering matrix
            
            
            
            
            fimm.Exec("fpLHS.update()")
            
            
            # update progress bar:
            if ( step >= nProg*nWLs/ProgMax ):
                sys.stdout.write('*'); sys.stdout.flush();	# print a small progress bar
                nProg = nProg+1
            if ( step >= nWLs-1 ):
                sys.stdout.write('|     done\n'); sys.stdout.flush();	# print end of progress bar
            
            
            RLHS = np.zeros([N,N],dtype=complex)
            SMAT = []
            for i in range(1,N+1,1):
                '''Get Right-to-Right (reflecting) scattering matrix for Left-hand-side of cavity, for each WG mode.'''
                SMAT.append(   fimm.Exec("fpLHS.cdev.smat.rr["+str(i)+"]")   )
            for i in range(1,N+1,1):
                for k in range(1,N+1,1):
                    RLHS[i-1][k-1] = SMAT[i-1][k] # the index "k" is due to the fact that the first element of each line is "None"
            
            
            self.S_LHS_rr = RLHS    # store the right-to-right scattering matrix
            
            
            
            ''' Calculate the round-trip matrix R2, by multiplying reflecting Smat's of each side of cavity.     '''
            R2 = np.dot(RRHS,RLHS)  # combined scattering matrix for cavity round-trip
            self.S_RT = R2  # round-trip scattering matrix

            '''
            # optional, if Nguided < N: truncate the matrix to the guided modes.  Nguided = N, numModes (hard-coded)
            if Nguided < N:
                R2guided = np.zeros([Nguided,Nguided],dtype=complex)
                for i in range(0,Nguided,1):
                    for k in range(0,Nguided,1):
                        R2guided[i][k] = R2[i][k]
            else:
                R2guided=R2     # only this clause runs
            '''
            
            
            # solve eigenproblem
            Eig = np.linalg.eig(R2) # returned in format: (array([e1, e2]), array([v1, v2])
            # eigenvector (coefficient of each WG mode to produce scalar transformation) is in Eig[1]
            # eigenvalue (amplitude & phase applied to EigVect upon roundtrip) is in Eig[0]
            
            '''
            Eig_reorg = [] # we want to achieve an easier format: ([e1,v1],[e2,v2])
            for i in range(0,Nguided,1):
                Eig_reorg.append([Eig[0][i],Eig[1][i]])
            '''
            
            # 'zip' the two arrays together to rearrange as [ [e1,[v1]], [e2,[v2]]...[eN,[vN]] ]
            Eig_reorg = map(list,   zip(Eig[0], Eig[1])     )   # also re-map the (tuples) that zip() returns to [lists], so [list].append() will work later
            
            #if DEBUG(): print "Eig_reorg=" , Eig_reorg
            
            # now we move on to processing and displaying the results
            '''
            # we will display all the modes, ranked by eigenvalue
            Eig_ranked = []
            # calculate magnitude of eigenvalue then rank Eigenvalues accordingly
            #*** I think these loops can be replaced with more efficient Numpy functions
            for i in range(0,Nguided,1):
                magnitude = (Eig_reorg[i][0].real)**2+(Eig_reorg[i][0].imag)**2
                if len(Eig_ranked)==0:
                    Eig_ranked.append(Eig_reorg[i]+[magnitude])
                else:
                    found = 0
                    for j in range(0,len(Eig_ranked),1):
                        if magnitude > Eig_ranked[j][2]:
                            Eig_ranked_temp = Eig_ranked[:j]
                            Eig_ranked_temp.append(Eig_reorg[i]+[magnitude])
                            Eig_ranked = Eig_ranked_temp + Eig_ranked[j:]
                            found = 1
                            break
                    if found == 0:
                        Eig_ranked.append(Eig_reorg[i]+[magnitude])
            '''
            
            
            # Sorting by predominant mode number, instead of max eigenvalue.
            '''
            eg. sort eigenvalues according to which mode is largest in the eigenvector:
            EigVect_Mode0 = [*0.9983*, 0.003, 3.543e-5]
            EigVect_Mode1 = [5.05e-5, *0.9965*, 3.543e-5]
            EigVect_Mode2 = [6.23e-5, 0.0041, *0.9912*]
            '''
            # sort the list of [EigVal, [EigVect]...] with built-in list sorting via sorted()
            Eig_ranked = sorted(   Eig_reorg,   key= lambda x: np.argmax(  np.abs( x[1] )  )   )
            
            ''' How the above ``sorted` function works:
            The lambda function returns a `key` for sorting - where the key tells sorted() which position to put the element in the new list.  
            The argument passed to the lambda function, `x`, will be the current element in the list Eig_reorg as sorted() loops through it, which will look like x=[ EigVal, [EigVec0, EigVec1...EigVecN] ].  
            We then select only the EigenVector part with `x[1]`.  Then the lambda function returns the index to whichever EigVect element has the maximum amplitude (`np.abs()`), generated by `numpy.argmax()` -- the index to that element will be the `key` used for sorting - ie. the vector that has the 1st element as max. ampl. will be sorted to the top of the resulting list.   
            '''
            
            if DEBUG(): print "Eig_ranked=" , Eig_ranked
            
            
            ## To save EigenVector/EigenValue at this wavelength:
            EigVect_n = []
            EigVal_n = []
            
            # display eigenvalues + save eigvals:
            outputstr = str(wavelength) + " "
            for i in range(0,Ndisplay,1):
                ## Save eigenvector/eigenvalue for this mode
                EigVect_n.append(Eig_ranked[i][1])
                EigVal_n.append(Eig_ranked[i][0])
                #if DEBUG(): print "Mode %i: EigVect_n[-1]="%(i) , EigVect_n[-1]
                outputstr = outputstr + str(Eig_ranked[i][0].real) + " " + str(Eig_ranked[i][0].imag) + " "
            if Display:    print outputstr
            
            
            ## Save Eigenvector/Eigenvalue at this wavelength
            EigVect.append(EigVect_n)
            EigVal.append(EigVal_n)
            #if DEBUG(): print "EigVect_n(WL)=", EigVect_n
        #end for(wavelengths)

        print   # new line
        return np.array(EigVal), np.array(EigVect)
    #...
    # end CavityModeCalc()
    
    
    
    def __FindResonance(self, nummodes):
        '''Locate the wavelengths where the round-trip phase is zero (imaginary part of Eigenvalue = 0) & Eigenvalue (related to cavity loss) is positive (not lossy).
        
        From Vincent Brulis @ PhotonDesign:
        You can detect the resonances by identifying the wavelengths for which the imaginary part of the eigenvalue (round-trip phase) is zero and the real part is positive (the higher the real part, the less lossy the resonance).  The round-trip loss (i.e. the threshold gain) for a given resonance can be obtained from 10*log(real^2).

        Returns
        -------
        resWL, resEigVals, resEigVects, loss : lists
            List of wavelengths, eigenvalues, eigenvectors and round-trip losses for each mode.  List index corresponds to each mode, and will contain `None` if no cavity resonance was found for that mode.

        '''
        
        #modenum = self.modenum
        
        WLs = self.wavelengths
        
        resWL = []
        resEigVals = []
        resEigVects = []
        losses = []
        
        for modenum in range(nummodes):
            Eigs_r = self.eigenvalues[:,modenum].real
            Eigs_i = self.eigenvalues[:,modenum].imag
        
            I0 = []
            for i in xrange(len(Eigs_i)-1):
                '''xrange() is identical to range() but more efficient with memory, and replaces range() in later Python versions (ver>=3 ?).'''
                if (Eigs_i[i] > 0 and Eigs_i[i+1] < 0) or   \
                    (Eigs_i[i] < 0 and Eigs_i[i+1] > 0):
                    '''If imaginary crosses zero.'''
                    
                    if Eigs_r[i]>0 or Eigs_r[i+1]>0:
                        '''If real part is positive.  
                            Choose the point with minimum imaginary part.'''
                        if abs( Eigs_i[i] )  <  abs( Eigs_i[i+1] ):
                            I0.append( i )
                        else:
                            I0.append( i+1 )
                        #if DEBUG(): print "Mode %i: "%(modenum) + "crossing between indexes %i and %i"%(i, i+1)
                        if DEBUG(): print "Mode %i: "%(modenum) + "; Resonance found at Wavelength ", WLs[I0[-1]], " um: " + "Eigs_i=", Eigs_i[I0[-1]], "; Eigs_r=", Eigs_r[I0[-1]]
            #end for(Eigs_i)
            
            if len(I0) == 0:
                ''' if no resonance found'''
                if DEBUG(): print( "_findres(): Mode=", modenum, " // No Resonance" )
                resWL.append( None )
                resEigVals.append( None )
                resEigVects.append( None )
                losses.append( None )
            else:
                if DEBUG(): print( "_findres(): Mode=", modenum, " // I0=", I0 )
                resWL.append( WLs[I0] )     # save all resonance wavelengths for this mode
                resEigVals.append( self.eigenvalues[I0,modenum] )   # save all resonance EigVals for this mode
                resEigVects.append( self.eigenvectors[I0,modenum] )   # save all resonance EigVects for this mode


                # normalize the eigenvalue, to the magnitude of the eigenvectors:
                loss=[]
                if DEBUG(): print("_findres(): len(resEigVals)=", len(resEigVals[-1]))
                for ii in range(  len(resEigVals[-1])  ):
                    '''in case multiple resonances for this mode'''
                    if DEBUG(): print( "_findres(): rVect[", ii, "]=", resEigVects[-1][ii])
                    if resEigVects[-1][ii] != None:
                        MagEigVect = [  np.sum(  np.abs( rVect )  )   for   rVect in resEigVects[-1][ii]  ]    # total magnitude of the eigenvector
                        eVal_norm = np.array(resEigVals[-1][ii]) / np.array(MagEigVect)     # normalized eigenvalues
                        loss.append(   1.0 - np.real(eVal_norm)   )  # fractional loss for input mode amplitude
                    else: 
                        loss.append( None ) 
                losses.append( np.array(loss) )
        #end for(modenum)
        
        return (resWL, resEigVals, resEigVects, losses)
            
    #end __FindResonance
    
#end class Cavity



