'''
pyFIMM.CavityMode

Operations on Cavity Modes (modes vs. Z).  Created when the user requests:
    >>> CavityObj.mode(0)
    :   returns a <pyFIMM CavityMode object>
Demis D. John, 2015, Praevium Research Inc.

To Do:
------
- Cavity.plot()
    - plot lateral fields?
    - zmin & zmax - account for LHS_Dev & RHS_Dev lengths etc.
'''

from __globals import *         # import global vars & FimmWave connection object
# DEBUG() variable is also set in __globals

import numpy as np
import math

#from __pyfimm import DEBUG()        # Value is set in __pyfimm.py
from __pyfimm import get_N, set_wavelength         # get number of calculated modes



######## For Cavity.mode(n)...  ########

class CavityMode(object):
    '''CavityMode( CavityObj, ModeNum )
    
    Class for selecting a Cavity Mode, similar to the Mode class used in `WG.mode(0)`.
    Typically created via Cavity's `mode()` method, like so:
        >>> Cavity.mode(0).plot()   
    Since Cavity.mode() returns a CavityMode object, this calls CavityMode.plot()
    
    Parameters
    ----------
    CavityObj : pyFIMM.Cavity object
        The Cavity object to perform operations on.
    ModeNum : integer, list of integers, or the string 'all', optional.
        The Cavity mode number to work on. Default is 0.
        May pass multiple modenumbers in a list, eg. `CavityMode([0,1,2])`
        If the string 'all' (case insensitive) is passed, data will be returned for all calculated modes (as specified by get_N() - the number of calculated lateral modes per Section/Circ).
    
    
    Attributes
    ----------
    modenum : int or 'all'
        Which lateral mode to manipulate.
    
    wavelengths, eigenvalues, eigenvectors : numpy array
        Wavelengths (passed to `Cavity.calc()`) & corresponding eigenvalues/eigenvectors at each.
        The eigenvectors are the magnitudes/phases of each lateral mode needed in order to produce the resonant cavity field.  The lateral modes (up to get_N() ) are the basis set of the eigenvalue problem.
        For eigenvalues & eigenvectors, indexing is like so:
            >>> eigenvalues[Imodenum][Iwavelength]
        Where `wavelengths[Iwavelength]` tells you which wavelength you're inspecting, and `Imodenum` tells you which mode number you're inspecting.
        
    
    
    Methods
    -------
    
    Please see help on a specific function via `help(CavityMode.theFunc)` for detailed up-to-date info on accepted arguments etc.
    
    get_resonance_wavelengths():
        Returns resonance wavelength(s) for selected modes.
        `get_resonance_wavelength()` is a synonym.
    
    get_resonance_eigenvalues():
        Returns resonance eigenvalues(s) (the round-trip amplitude & phase applied to a field) for this mode.
        `get_resonance_eigenvalue()` is a synonym.
    
    get_resonance_eigenvectors():
        Returns resonance eigenvectors(s) (the magnitudes/phases of each central-section mode to get the above eigenvalues) for this mode.
        `get_resonance_eigenvector()` is a synonym.

    
    plot( component ):
        Plot a component of this mode.  
        Supported components include: 
            'EigVals' - plot Eigenvalues versus wavelength.
            Ex, Ey, Ez - Electric fields versus Z.
            Hx, Hy, Hz - Magnetic Fields versus Z.
            Px, Py, Pz - Poynting Vectors versus Z.
            'index' or 'rix' - refractive index of cavity versus Z.
        See `help(CavityMode.plot)` or `help(CavityObj.mode(0).plot)` for full help on the function, as there are more important details than mentioned here.
    
    get_cavity_loss():
        NOT IMPLEMENTED YET.
        Return the cavity loss (equivalent to threshold gain) for this mode.
    
    Examples
    --------
    CavityMode objects are typically Not called/instantiated from the CavityModes class directly, but instead as a sub-object of a Cavity `mode` method like so:
            >>> CavityObj.mode(0).plot()
        where `CavityObj.mode(0)` is the method `mode()` of the CavityObject which returns a CavityMode object (initialized with modenum=0), and `.plot()` is a method of this CavityMode object. 
    '''
    
    def __init__(self, CavObj, num):
        '''Takes Cavity object `CavObj` as input, and mode number `num` (default=0).  
        Optionally, if num == 'all' will return data on all modes.'''
        
        self.Cavity = CavObj
        
        if isinstance(num, str):
            if num.lower() == 'all':
                #num = -1    # plot all modes
                self.modenum = range(0, get_N() )   # list of each modenumber calc'd
            else:
                ErrStr = 'CavityMode: Mode Number must be an integer, list of integers, or the string "all".'
                raise ValueError(ErrStr)
        elif isinstance(num, int):
            self.modenum = [num]    # put num into a list
        else:
            try:
                self.modenum = [int(x) for x in num]    # check that we're able to create a list of integers
            except:
                ErrStr = 'CavityMode: Mode Number must be an integer, list of integers, or the string "all".'
                raise ValueError(ErrStr)
        #end if(num)
        
        
        self.eigenvalues = []
        self.eigenvectors = []
        self.wavelengths = []
        self.__resonance_wavelength = []
        self.__resonance_eigenvalue = []
        self.__resonance_eigenvector = []
        
        for num in self.modenum:
            '''eigenvalues[i][ corresponds to the modenumber modenum[i]'''
            try:
                '''Make sure the Cavity has been calculated.'''
                CavObj.eigenvalues
                CavObj.eigenvectors
            except AttributeError:
                ErrStr = "EigenValues/EigenVectors not found - not calculated yet?   Try calling `Cavity.calc()` first."
                raise AttributeError(ErrStr)
            self.eigenvalues.append(  CavObj.eigenvalues[: , num]  )
            self.eigenvectors.append(  CavObj.eigenvectors[: , num]  )
            self.wavelengths.append( CavObj.wavelengths )  # could just have one entry for this...
            self.__resonance_wavelength.append( CavObj.resWLs[num] )
            self.__resonance_eigenvalue.append( CavObj.resEigVals[num] )
            self.__resonance_eigenvector.append( CavObj.resEigVects[num] )
    #end __init__
    
    
    def get_field(self, component, wavelength, zpoints=3000, zmin=0.0, zmax=None, xcut=0.0, ycut=0.0, direction=None, calc=True):
        '''Return the field specified by `component`, versus Z.
        2 arguments are requires, `component` and `wavelength`.
        The fields returned are for the Cavity having input field set to the eigenvectors calculated at the given wavelength.
        
        component : {'Ex' | 'Ey' | 'Ez' | 'Hx' | 'Hy' | 'Hz' | 'Px' | 'Py' | 'Pz' | 'I' }, case-insensitive, required
            Return the specified field component along the Z direction.
            'E' is electric field, 'H' is magnetic field, 'P' is the Poynting vector, 'I' is Intensity, and 'x/y/z' chooses the component of each vector to return.
            'index', 'rix' or 'ri' will return the refractive index, a functionality provided by the more convenient function `get_refractive_index()` but otherwise identical to this func.  `wavelength` is ignored in this case.
        
        wavelength : number or the string 'resonance'
            If 'resonance' specified, will launch the resonance wavelength with maximum eigenvalue (min loss).   Synonyms are 'res' and 'max', and these are all case-insensitive.
            If a number is specified, that wavelength will be launched.  The wavelength should be found in the list of calculated wavelengths (`Cavity.calc(wavelengths)`), found after `calc()` in the attribute `Cavity.wavelengths`.
        
        direction = string { 'fwd', 'bwd', 'total' }, case insensitive, optional
            DISABLED - now chosen based on LHS or RHS input.
            Which field propagation direction to plot.  Defaults to 'total'.
            Note that the propagation direction should match up with which side the input field was launched.  Eg. for `set_input([1,0,0], side="left")` you'll want to use `direction="fwd"`.
            Synonyms for 'fwd' include 'forward' & 'f'.
            Synonyms for 'bwd' include 'backward' & 'b'.
            Synonyms for 'total' include 'tot' & 't'.
        
        xcut, ycut = float, optional
            x & y coords at which to cut the Device along Z.  Both default to 0.
        
        zpoints = integer, optional
            Number of points to acquire in the field.  Defaults to 3000.
        
        zmin, zmax = float, optional
            min & max z-coorinates. Defaults to 0-->Device Length.
        
        calc = { True | False }
            Tell FimmProp to calculate the fields?  Only needs to be done once to store all field components & refractive indices (for a given `zpoints`, `xcut` etc.), so it is useful to prevent re-calculating after the first time.
        
        cut = tuple of two floats - NOT IMPLEMENTED YET
            Specify coordinate plane on which to plot fields. Default (0,0).
            If dir='Z', then tuple is (x,y).
            If dir='Y', then tuple is (x,z).
            If dir='X', then tuple is (y,z).
        
        Returns
        -------
        2-D List of complex values corresponding to field values, starting at z=0 and ending at specified `zmax`, for each specified modenumber.  
        1st dimension of List corresponds to the specified modenumbers.  For example:
            >>> f = CavObj.mode([1,3]).get_field('Ex', 'resonance')
        Will return the list `f` with `f[0]` corresponding to mode(1) & `f[1]` corresponding to mode(3).
            >>> f =  CavObj.mode(2).get_field('Ex', 'resonance')
        Will only have `f[0]`, corresponding to mode(2).
        
        
        Examples
        --------
        Get the Total Ex field at x,y=(0,0) along Z, along the whole Cavity.
            >>> field = Cav.get_field('Ex')
        Get the refractive index at x,y=(0,0) along Z, along the whole Cavity.
            >>> field = Cav.fields('index')
        '''
        wl = wavelength
        zptsL=int(zpoints/2.); zptsR=np.round(zpoints/2.)
        
        comp = component.lower().strip()
        if comp == 'index' or comp == 'rix' or comp == 'ri':
            '''Return refractive index - wavelength unimportant'''
            Lfield = self.Cavity.LHS_Dev.get_field('rix', zpoints=zptsL, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut, direction='total', calc=calc)
            Rfield = self.Cavity.RHS_Dev.get_field('rix', zpoints=zptsR, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut, direction='total', calc=calc)
    
            Lfield.extend(Rfield)   # concatenate the L+R fields
            zfield=Lfield
        else:
            zfield=[]   # to hold fields at each mode number
            for num,M in enumerate(self.modenum):
                '''num goes from 0-># of modes requested.  M tells use the actual mode number.'''
            
                if DEBUG(): print "CavityMode.plot(field): (num, M) = (", num, ",", M, ")"
            
            
                # find index to the spec'd wavelength.
                #   `wl` is the passed argument, `WL` is the final wavelength
                
                if isinstance(wl, str):
                    '''if 2nd arg, wl, is a string:  '''
                    wl = wl.lower().strip()     # to lower case + strip whitespace
                    if wl == 'resonance'  or  wl == 'res'  or  wl == 'max':
                        '''Find the resonant wavelength/eigval/eigvector'''
                        if DEBUG(): print "CavityMode.plot('res'): self.get_resonance_eigenvalues() = \n", self.get_resonance_eigenvalues()
                        if DEBUG(): print "CavityMode.plot('res'): self.get_resonance_wavelengths() = \n", self.get_resonance_wavelengths()
                    
                        if self.__resonance_eigenvalue[num]==[None] or self.__resonance_wavelength[num]==None:
                            '''No resonance found for this mode'''
                            ErrStr = "No resonance found for mode %i, "%(M) + "can't plot via `resonance`."
                            raise UserWarning(ErrStr)
                    
                        Iwl = np.argmax(  np.real( self.__resonance_eigenvalue[num] )  )
                        
                        WL = self.__resonance_wavelength[num][Iwl]
                        Iwl = np.where(  np.array([WL]) == self.wavelengths[:][num]  )[0]  # set to index of all calc'd WL's, not just resonance WLs
                        print "CavityMode.plot('res'): Getting field at resonance mode @ %0.3f nm" %( WL )
                        if DEBUG(): print "Iwl=%s\nWL=%s"%(Iwl,WL)
                    else:
                        raise ValueError("CavityMode.plot(field): Unrecognized wavelength string.  Please use 'resonance' or provide a wavelength in microns.  See `help(CavityMode.plot)` for more info.")
                else:
                    '''A specific wavelength (number) must have been passed: '''
                    WL = wl
                    Iwl = np.where(  np.array([WL]) == self.wavelengths[num]  )[0]
                    if not Iwl:
                        '''If wavelength not found in calculated WLs:   '''
                        ErrStr = "CavityMode.plot(field): Wavelength `", WL, "` not found in among list of calculated wavelengths list (chosen during `Cavity.calc(wavelengths)`).   See `help(CavityMode.plot)` for more info."
                        raise ValueError(ErrStr)
                if DEBUG(): print "CavityMode.plot(): (num,Iwl)=(",num,",",Iwl,")"
            
                EigVec = self.eigenvectors[num][Iwl[0]]    # find eigenvector at given wavelength
            
            
                # Launch this eigenvector:
                norm = False
                self.Cavity.RHS_Dev.set_input( EigVec, side='left', normalize=norm )
                self.Cavity.RHS_Dev.set_input( np.zeros(  get_N() ), side='right' )   # no input from other side
                
                # Get mode vector reflected from RHS device & launch it into LHS dev, to accomplish one roundtrip
                vec = self.Cavity.RHS_Dev.get_output_vector(side='left', direction='left')
                self.Cavity.LHS_Dev.set_input( vec, side='right', normalize=norm )
                self.Cavity.LHS_Dev.set_input( np.zeros(  get_N() ), side='left' )   # no input from other side

                
                # Get field values:
                Lfielddir, Rfielddir = 'total','total' 
                self.Cavity.LHS_Dev.calc(zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut)
                Lfield = self.Cavity.LHS_Dev.get_field(comp, zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut, direction=Lfielddir, calc=False)
                
                self.Cavity.RHS_Dev.calc(zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut)
                Rfield = self.Cavity.RHS_Dev.get_field(comp, zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut, direction=Rfielddir, calc=False)
                
                Lfield.extend(Rfield)   # concatenate the L+R fields
                zfield.append(Lfield)   # add field for this mode number
            #end for(self.modenum)
        #end if(comp==etc.)
        
        return zfield
    #end get_field()
    
    # Alias for this func:
    field = get_field
    
    
    def plot(self, *args, **kwargs):
        '''CavityMode.plot(component, [more options])
        CavityMode.plot()
        CavityMode.plot( 'EigVals' )    # plot eigenvalues versus wavelength
        CavityMode.plot( 'Ex', 1.055 )  # plot cavity field Ex versus Z @ 1.055um wavelength
        
        Plot the cavity modes.
        If no arguments are provided, this will plot the calculated Eigenvalues versus wavelength.  
        However, if a field component is specified, the function will plot the cavity fields versus Z.
        
        
        Parameters
        ----------
        component : string (see below), case-insensitive, optional
            Two different plot functionalities may be performed, depending on whether `component` specifies a field component or the eigenvalues of the cavity.  The different functionality for either type of `component` specified is as follows:
            
            component = 'EigVal' : 
                Plot EigenValues vs. wavelength (at the wavelengths determined by `Cavity.calc(wavelengths)` ).  
                This is the default if no argument passed.  Synonyms for 'EigVal' are 'EigVals' & 'EigV'.
                
            component = {'Ex' | 'Ey' | 'Ez' | 'Hx' | 'Hy' | 'Hz' | 'I' | 'RIX'} : 
                Plot the specified field component along a specified direction.  
                "RIX", "RI" or "index" will plot only the refractive index vs. Z.
                The 2nd argument must be the wavelength at which to plot the fields, or the string 'resonance'.  The specified wavelength must be in the list of calculated wavelengths passed to `Cavity.calc(wavelengths)`.  These wavelengths can be found in the list `CavityObj.wavelengths`.  For example, you could get them directly from that list, like so:
                    >>> CavityObj.mode(0).plot( 'Ex', CavityObj.wavelengths[51] )
                If the string 'resonance' is provided as the wavelength, then the wavelength with dominant resonance (max eigenvalue/min. loss) will be used.  Synonyms for 'resonance' are 'res' & 'max', and the string is case-insensitive.
                
                
                Other optional keywords for field plotting that may be provided are:
                
                refractive_index = { True | False }
                    If True, will plot the refractive index of the structure on a second axis, with shared X-axis (so zooming etc. zooms both X axes).  Default is False.
                
                field_points = integer, optional
                    Number of points to acquire in a field plot.  Defaults to 3000.  The exact number of acquired points may vary by one of two points.
                
                xcut, ycut = float, optional
                    x & y coords at which to cut the Device along Z.  Both default to 0.
                
                zmin, zmax = float, optional
                    min & max z-coorinates. Defaults to 0-->Device Length.
                
                xpoint, ypoint = float, optional
                    x & y coords at which to cut the Device along Z.  Both default to 0.
                
                direction = string { 'fwd', 'bwd', 'total' }, case insensitive, optional
                    DISABLED: direction now chosen based on launch dir.
                    Which field propagation direction to plot.  Defaults to 'bwd'.
                    
                cut = tuple of two floats - NOT IMPLEMENTED YET
                    Specify coordinate plane on which to plot fields. Default (0,0).
                    If dir='Z', then tuple is (x,y).
                    If dir='Y', then tuple is (x,z).
                    If dir='X', then tuple is (y,z).
                
        return_handles = { True | False }
            If True, will return handles to the figure, axes, legends and lines.  False by default.
        
        title = str, optional
            Pre-pend some text to the plot title.
        
        warn = bool
            Display warnings?  Defaults to True.
        
        
        Returns
        -------
        handles : tuple of (fig1, axes, lines, leg)
            If `return_handles=True`, returns matplotlib handles to the plot's objects, as so:
            fig1 : main figure object
            axes : Each axis. For field plots, if `refractive_index=True` then axes = ( Field_Axis , RI_Axis ), otherwise just = Field_Axis handles (or one axis for EigenValues).
            lines : Each curve plotted. If `refractive_index=True` then lines = ( RI_line, Field_Line_Mode_0, Field_Line_Mode_1 , ... Field_Line_Mode_N ), otherwise handle RI_Line is omitted.
                For EigenValue plots, `lines = (EigV_real_lines, EigV_imaginary_lines, Resonance_lines)`, with each being a list with a line per mode.  Resonance_lines are the vertical lines indicating resonance wavelengths, which itself is a list of lists - `Resonance_lines[modenum][resonance_num]`, since there can be multiple resonances for each mode.
            leg : legend of main Field/EigV axis, containing one legend entry for each mode number.
        
        
        Examples
        --------
        Typically Not called/instantiated from CavityModes class directly, but instead as a sub-object of a Cavity mode object like so:
            >>> CavityObj.mode(0).plot('EigVal')
        where `CavityObj.mode(0)` returns a CavityMode object (initialized with modenum=0), and `.plot` is a method of this CavityMode object. 
        
        Plot Eigenvalues vs. Wavelength for a few lateral (waveguide) modes:
            >>> CavityObj.mode( [0,2] ).plot('EigVal')
            >>> CavityObj.mode( 'all' ).plot('EigVal')  # plot all Mode's EigV's on one plot
            >>> CavityObj.mode( 0 ).plot('EigVal')      # plot only 1st mode's Eigenvalues
        
        Plot Fields of the Cavity Mode:
            >>> CavityObj.mode( 0 ).plot('Ex', 'resonance')  # plot Ex for strongest resonance of Mode 0
            >>> CavityObj.mode( 'all' ).plot('Hy', 1.550)  # plot Hy for all modes on one plot, at wavelength 1.550 (may not be resonant, so fields may be discontinuous @ Cavity cut)
            >>> CavityObj.mode( 0 ).plot('Ex', 'resonance', refractive_index=True)  # plot Ex for strongest resonance of Mode 0, with Refractive Index profile plotted on separate axis
            >>> fig, axis, line, leg = CavityObj.mode( 0 ).plot('Ex', 'res', return_handles=True)  # plot Ex for strongest resonance, and return matplotlib handles to the figure's elements
        '''
        
        import matplotlib.pyplot as plt     # there is no extra overhead to re-import a python module
        
        # parse keyword args:
        return_handles = kwargs.pop('return_handles', False)
        title = kwargs.pop('title', None)
        warn = kwargs.pop('warn', True)
        
        ''' Unused Kwargs are returned at the end of the plot() func.'''
        
        
        if len(args)==0:
            comp = 'eigval'
        else:
            if isinstance(args[0], str):
                comp = args[0].lower().strip()  # make lower case, strip whitespace
            else:
                ErrStr = "CavityMode.plot(component): expected `component` to be a string, but instead got: " + str(type(component)) + " : " + str(component)
                raise ValueError(ErrStr)
        #end if(args)
        
        
        # Perform different plots depending on requested component `comp`:
        #eigvstr = ['eigval', 'eigvals', 'eigv']     # possible strings for EigenValue plotting
        fieldstrs = ['ex','ey','ez','hx','hy','hz','i','rix','ri','index']   # possible strings for field plotting
        
        
        
        '''
        -----------------------------------
        First case: Plot the Eigenvalues
        -----------------------------------
        '''
        if comp == 'eigval' or comp == 'eigvals' or comp == 'eigv':
            '''Plot the eigenvalues'''
            
            fig1, ax1 = plt.subplots(1, 1)
            box = ax1.get_position()
            ax1.set_position([ box.x0, box.y0, box.width * 0.8, box.height])    # reduce axis width to 80%, to make space for legend
            
            l1 = []; l2 = []
            vlines_out=[]
            for num,M   in   enumerate(self.modenum):
                '''num goes from 0-># of modes requested.  M tells use the actual mode number.'''
                #if DEBUG(): print "CavityMode.plot: num in modenum = ", num, type(num), " in ", self.modenum, type(self.modenum)
                
                if len(self.eigenvalues[num]) == 0: raise UserWarning("No EigenValues found for mode %i!" %M +"  Cavity modes not calculated yet? Please run Cavity.calc() to do so.")    
            
                EigsArray = self.eigenvalues[num]
                WLs = self.wavelengths[num]
        
                #l1 = []; l2 = []; leg1 = []; leg2=[]
                l1.extend(  ax1.plot(WLs, EigsArray.real, '-x', label="%i: Real"%self.modenum[num] )   )
                curr_color = l1[-1].get_color()     # color for this mode, as selected my MPL
                #leg1.append("Real")
                l2.extend(  ax1.plot(WLs, EigsArray.imag, '-+', label="%i: Imag"%self.modenum[num], color=curr_color )    )
                #leg2.append("Imaginary")
        
                #ax1.plot(WLs, EigsArray[:,0].real, label="Mode "+str(i)+": real")
                #ax2.plot(WLs, EigsArray[:,0].imag, label="Mode "+str(i)+": imag")

            
                # add line indicating resonance, if found:
                vlines = [] # holds handles of vertical lines
                if np.any(self.__resonance_wavelength[num]):
                    # This line starts at the data coords `xytext` & ends at `xy`
                    ymin, ymax = ax1.get_ylim()
                    for ii, resWL in enumerate( self.__resonance_wavelength[num] ):
                        if ii==0:
                            '''Only add label once'''
                            vlines.append( ax1.vlines(resWL, ymin, ymax, linestyles='dashed', colors=curr_color, label="%i: Resonance"%self.modenum[num] )  )
                        else:
                            vlines.append( ax1.vlines(resWL, ymin, ymax, linestyles='dashed', colors=curr_color)  )
                    #end for(resWL)
                #end if(resonance)
                vlines_out.append(vlines)
            #end for(modenum)
            
            ax1.set_xlabel(r"Wavelength, ($\mu{}m$)")
            ax1.set_ylabel("Eigenvalue")
            #ax2.set_ylabel("Imaginary")
            titlestr = self.Cavity.name + " Eigenvalues for Mode "+str(self.modenum)
            if title: titlestr = title + ": " + titlestr
            ax1.set_title(  titlestr  )
            ax1.grid(axis='both')
            #plt.legend()
            
            #leg = plt.legend()
            leg = ax1.legend( loc='upper left', bbox_to_anchor=(1, 1) , fontsize='small' )
            
            fig1.canvas.draw(); fig1.show()
            
            # return some figure handles
            if return_handles:     return fig1, ax1, (l1, l2, vlines_out), leg
            
        #end if(comp='EigV')
        
        
        
        #-----------------------------------
        #    2nd case: Plot the Fields
        #-----------------------------------
        elif np.any( np.array(comp)==np.array(fieldstrs) ):
            # check if comp matches Any strings in `fieldstrs`, defined above the if(...), ln. 409
            
            # -- Plot fields in structure --
            
            
            # 1st arg: Component string for plot legend:
            #   (`comp` will be send to `get_field()` for parsing which field) 
            if comp == 'Ex'.lower():
                compstr='Ex'
            elif comp == 'Ey'.lower():
               compstr='Ey'
            elif comp == 'Ez'.lower():
               compstr='Ez'
            elif comp == 'Hx'.lower():
               compstr='Hx'
            elif comp == 'Hy'.lower():
               compstr='Hy'
            elif comp == 'Hz'.lower():
               compstr='Hz'
            elif comp == 'I'.lower():
               compstr='Intensity'
            elif comp=='rix' or comp=='index' or comp=='ri':
                compstr='Refr. Index'     
            else:
                raise ValueError("CavityMode.plot(field): Invalid field component requested.")
            
            
            # get keyword arguments, with default:
            RIplot = kwargs.pop('refractive_index', False)  # plot refractive index?
            zpoints = kwargs.pop('field_points', 3000)    # number of points in field plot
            xcut = kwargs.pop('xpoint', 0.0)
            ycut = kwargs.pop('ypoint', 0.0)
            zmin = kwargs.pop('zmin', 0.0)
            zmax = kwargs.pop('zmax',   (self.Cavity.LHS_Dev.get_length() + self.Cavity.RHS_Dev.get_length())   )   # default to total device length
            
            zpoints = math.ceil( zpoints/2. )    # half as many zpoints in each of the two Devs
            
            xpoints, ypoints = xcut, ycut   # probably not needed - old method
            PlotPoints = zpoints    # not needed
            
            """
            dirstr = kwargs.pop('direction', None)
            if dirstr == None:
                dirstr = 'bwd'
            else:
                dirstr = dirstr.lower().strip()
            
            if dirstr=='fwd' or dirstr=='forwards' or dirstr=='f':
                dirstr = 'Fwg'
            elif dirstr=='bwd' or dirstr=='backwards' or dirstr=='b':
                if comp=='i':
                    '''Due to Fimmwave typo bug: should be Title case.  '''
                    dirstr = 'bwg'
                else:
                    dirstr = 'Bwg'
            elif dirstr=='total' or dirstr=='tot' or dirstr=='t':
                dirstr = 'Total'
            
            fieldstr = compstr + dirstr     #attribute of FimmWave `zfieldcomp` object
            """
            
            # 2nd arg: Figure out array index to proper wavelength
            if len(args) >= 2:
                wl = args[1]
            else:
                ErrStr="Cavity.plot(): For plotting a field component, 2nd argument must be the wavelength to plot.  Please see `help(CavityMode.plot)` for more info."
                raise ValueError(ErrStr)
            
            #if DEBUG(): print "CavityMode.plot(field): wl= ", wl
            
            zfield=[]   # to hold fields at each mode number
            for num,M in enumerate(self.modenum):
                '''num goes from 0-># of modes requested.  M tells use the actual mode number.'''
                
                if DEBUG(): print "CavityMode.plot(field): (num, M) = (", num, ",", M, ")"
                
                
                
                # find index to the specified wavelength in the list of calc'd wavelengths.
                #   `wl` is the passed argument, `WL` is the final wavelength
                if isinstance(wl, str):
                    '''if 2nd arg is a string:  '''
                    wl = wl.lower().strip()     # to lower case + strip whitespace
                    if wl == 'resonance'  or  wl == 'res'  or  wl == 'max':
                        '''Find the resonant wavelength/eigval/eigvector'''
                        if DEBUG(): print "CavityMode.plot('res'): self.get_resonance_eigenvalues() = \n", self.get_resonance_eigenvalues()
                        if DEBUG(): print "CavityMode.plot('res'): self.get_resonance_wavelengths() = \n", self.get_resonance_wavelengths()
                        
                        if np.all(  np.array(self.__resonance_eigenvalue[num])==np.array([None])  )   or   np.all(  np.array(self.__resonance_wavelength[num])==np.array([None])  ):
                            '''No resonance found for this mode'''
                            ErrStr = "No resonance found for mode %i, "%(M) + "can't plot via `resonance`."
                            raise UserWarning(ErrStr)
                        
                        # Find maximum Resonant EigenValue
                        Iwl = np.argmax(  np.real( self.__resonance_eigenvalue[num] )  )
                            
                        WL = self.__resonance_wavelength[num][Iwl]
                        Iwl = np.where(  np.array([WL]) == self.wavelengths[:][num]  )[0]  # set to index of all calc'd WL's, not just resonance WLs
                        print "CavityMode.plot('res'): Getting field at resonance mode @ %f nm" %( WL )
                        if DEBUG(): print "Iwl=%s\nWL=%s"%(Iwl,WL)
                    else:
                        raise ValueError("CavityMode.plot(field): Unrecognized wavelength string.  Please use 'resonance' or provide a wavelength in microns.  See `help(CavityMode.plot)` for more info.")
                else:
                    '''A specific wavelength (float/number) must have been passed: '''
                    WL = wl
                    Iwl = np.where(  np.array([WL]) == self.wavelengths[num]  )[0]  # get index to specified wl
                    if not Iwl:
                        '''If wavelength not found in calculated WLs:   '''
                        ErrStr = "CavityMode.plot(field): Wavelength `", WL, "` not found in the list of calculated wavelengths list (chosen during `Cavity.calc(wavelengths)`).   See `help(CavityMode.plot)` for more info."
                        raise ValueError(ErrStr)
                #end parsing `wl`
                
                
                
                if DEBUG(): print "CavityMode.plot(): (num,Iwl)=(",num,",",Iwl,") \n" +\
                    "Setting Wavelength to WL=%f um"%WL
                
                
                # Set FimmWave & Device wavelengths to proper value:
                print self.Cavity.name + ": Setting Global & Device wavelength to %0.8f."%(WL)
                set_wavelength(WL)
                self.Cavity.RHS_Dev.set_wavelength(WL)
                self.Cavity.LHS_Dev.set_wavelength(WL)
                
                
                EigVec = self.eigenvectors[num][Iwl[0]]    # find eigenvector at given wavelength
                
                
                
                # Launch this eigenvector:
                norm = False    # normalize the launch vectors?  V.Brulis said to disable this
                self.Cavity.RHS_Dev.set_input( EigVec, side='left', normalize=norm )
                self.Cavity.RHS_Dev.set_input( np.zeros(  get_N() ), side='right' )   # no input from other side
                
                # Get mode vector reflected from RHS device & launch it into LHS dev, to accomplish one roundtrip
                vec = self.Cavity.RHS_Dev.get_output_vector(side='left', direction='left')
                self.Cavity.LHS_Dev.set_input( vec, side='right', normalize=norm )
                self.Cavity.LHS_Dev.set_input( np.zeros(  get_N() ), side='left' )   # no input from other side

                
                # Get field values:
                Lfielddir, Rfielddir = 'total','total' 
                self.Cavity.LHS_Dev.calc(zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut)
                Lfield = self.Cavity.LHS_Dev.get_field(comp, zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut, direction=Lfielddir, calc=False)
                
                self.Cavity.RHS_Dev.calc(zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut)
                Rfield = self.Cavity.RHS_Dev.get_field(comp, zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut, direction=Rfielddir, calc=False)
                
                Lfield.extend(Rfield)   # concatenate the L+R fields
                
                
                zfield.append(Lfield)   # add field for this mode number
                
            #end for(modenums)
                
            ##################################
            # plot the field values versus Z:
            zfield = np.array(zfield)
            TotalLength = self.Cavity.LHS_Dev.get_length() + self.Cavity.RHS_Dev.get_length()
            z = np.linspace( 0, TotalLength, num=len(zfield[0]) )   # Z-coord
            
            if DEBUG(): print "CavityMode.plot(field): len(zfield[0])=%i"%(len(zfield[0]) ) + \
                "np.shape(zfield)=", np.shape(zfield), "\nz(%i) = "%len(z), z
            
            lines=[]    # to return
            if RIplot:
                Lindex = self.Cavity.LHS_Dev.get_refractive_index(zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut, calc=False)
                Rindex = self.Cavity.RHS_Dev.get_refractive_index(zpoints=zpoints, zmin=zmin, zmax=zmax, xcut=xcut, ycut=ycut, calc=False)
                Lindex.extend(Rindex)   # concatenate the L+R indices
                
                rix=Lindex   # add field for this mode number
                
                
                fig1, (ax1,ax2) = plt.subplots(2, sharex=True)      # 2 axes
                axes=(ax1,ax2)  # to return
                # Reduce axis width to 80% to accommodate legend:
                box = ax2.get_position()
                ax2.set_position([ box.x0, box.y0, box.width * 0.8, box.height])
                
                l2 =  [ ax2.plot(z, np.real( np.array(rix) ), 'g-', label="Refractive Index" ) ]      # plot RIX on 2nd sibplot
                lines.append(l2)
            else:
                fig1, ax1 = plt.subplots(1, 1)      # 1 axis
                axes=ax1    # to return
            
            # Reduce axis width to 80% to accommodate legend:
            box = ax1.get_position()
            ax1.set_position([ box.x0, box.y0, box.width * 0.8, box.height])
        
            l1 = []; #l2 = []
            for num,M   in   enumerate(self.modenum):
                '''num goes from 0-># of modes requested.  M tells us the actual mode number.'''
                #if DEBUG(): print "CavityMode.plot(field): num in modenum = ", num, type(num), " in ", self.modenum, type(self.modenum)
    
                #l1 = []; l2 = []; leg1 = []; leg2=[]
                if DEBUG(): print "zfield[%i] = " %(num), zfield[num]
                l1.append(   ax1.plot(z, np.real(zfield[num]), '-', label="%i: %s"%(self.modenum[num], compstr) )   )
                lines.append(l1[num])
                #leg1.append("Real")

            #end for(modenum)
        
            ax1.set_ylabel( "Field %s"%(compstr) )
            
            titlestr = self.Cavity.name + ": %s vs. Z for Mode @ %0.2f $\mu{}m$"%(compstr,WL)
            if title: titlestr = title + ": " + titlestr
            fig1.suptitle(  titlestr  , fontsize=11)
            ax1.grid(axis='both')
            #plt.legend()
        
            if RIplot:
                ax2.set_ylabel('Refractive Index')
                ax2.set_xlabel(r"Z, ($\mu{}m$)")
                ax2.grid(axis='both')
            else:
                ax1.set_xlabel(r"Z, ($\mu{}m$)")
            
            #leg = plt.legend()
            leg = ax1.legend( loc='upper left', bbox_to_anchor=(1, 1) , fontsize='small' )
            #leg2 = ax2.legend( loc='upper left', bbox_to_anchor=(1, 1) , fontsize='small' )
        
            fig1.canvas.draw(); fig1.show()
        
            # return some figure handles
            if return_handles:     
                if RIplot:
                    return fig1, axes, lines, leg
                else:
                    return fig1, axes, lines, leg
                
            
        #end if(comp=='Ex, Ey etc.')
            
            
        else:
            '''If component specified is unrecognized:   '''
            ErrStr = "CavityMode.plot(): Invalid field component specified: `%s`.  \n\tSee `help(pyFIMM.CavityMode.plot)`." %(args[0])
            raise ValueError(ErrStr)
        #end if(component)
        

        if kwargs:
            '''If there are unused key-word arguments'''
            ErrStr = "WARNING: Cavity.plot(): Unrecognized keywords provided: {"
            for k in kwargs.iterkeys():
                ErrStr += "'" + k + "', "
            ErrStr += "}.    Continuing..."
            if warn: print ErrStr
    #end plot
        
    
    
    def get_resonance_wavelengths(self, ):
        '''Return the resonance wavelength for selected modes, as list, with each list index corresponding to the selected mode. Returns `None` if no resonances found.'''
        out = []
        for num, M in enumerate(self.modenum):
            out.append( self.__resonance_wavelength[num] )
        return out
    # alias to same function:
    get_resonance_wavelength = get_resonance_wavelengths
    
    
    def get_resonance_eigenvalues(self, ):
        '''Return the eigenvalue at the resonance wavelengths selected modes, as list, with each list index corresponding to the selected mode. Returns `None` if no resonances found.'''
        out = []
        for num, M in enumerate(self.modenum):
            out.append( self.__resonance_eigenvalue[num] )
        return out
    # alias to same function:
    get_resonance_eigenvalue = get_resonance_eigenvalues
    
    
    def get_resonance_eigenvectors(self, ):
        '''Return the eigenvector at the resonance wavelengths selected modes, as list, with each list index corresponding to the selected mode. Returns `None` if no resonances found.'''
        out = []
        for num, M in enumerate(self.modenum):
            out.append( self.__resonance_eigenvector[num] )
        return out
    # alias to same function:
    get_resonance_eigenvector = get_resonance_eigenvectors
    
    
    def get_cavity_loss(self, ):
        '''Return the cavity loss (equivalent to threshold gain) for this mode.
        The round-trip loss (i.e. the threshold gain) for a given resonance can be obtained from 10*log(real^2).'''
        print "get_cavity_loss(): WARNING: Not implemented."
        return -1
    
    
    