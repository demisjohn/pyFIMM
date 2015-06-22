'''Mode class, part of pyFIMM.'''

#from pylab import *     # must kill these global namespace imports!!!
#from numpy import *
import pylab as pl
import matplotlib.pyplot as plt
from pylab import cm    # color maps
import numpy as np
import math

import os  # for filepath manipulations (os.path.join/os.mkdir/os.path.isdir)

from __globals import *     # import global vars & FimmWave connection object
    # also contains AMF_FolderStr(), DEBUG()

from __pyfimm import get_N, get_wavelength

#AMF_FileStr = 'pyFIMM_temp'


class Mode:
    '''Mode( WGobj, modenum, modestring )
    
    Class for interacting with calculated Modes.  Includes extracting field values and mode plotting.
    Note that a Mode object is rarely instantiated directly - it instead is created when a waveguide/circ's `mode()` method is used - mode() returns a Mode object.  This allows behaviour like:
        WGobj.mode(0).plot()
    Where `WGobj.mode(0)` returns a Mode object instantiated with modenum=0, and `.plot()` is a moethod of that Mode object.
    
    
    Parameters
    ----------
    WGobj : Waveguide or Circ object
        The waveguide to extract modes from.
    
    modenum : int
        Choose which mode number to manipulate.
        To DO: support int, list of ints, or the string 'all'
    
    modestring : string
        The fimmwave string to reference the modes of the waveguide node.  See Circ.mode() or Waveguide.mode() to see how this string is set.
    
    
    Methods
    -------
    
    This is a partial list - see `dir(WG.mode(0))` to see all methods.
    Please see help on a specific function via `help(Mode.theFunc)` for detailed up-to-date info on accepted arguments etc.
    
    get_n_eff()
        return the effective index of this mode
    
    get_n_g()
        return the group index of this mode
    
    get_kx()
        return the propagation constant of this mode
    
    get_percent_TE()
        Return the "TEfrac" - or percentage of the mode that is transverse-electric.
    
    get_confinement()
        Return the confinement factor.

    get_confinement_ey()
        Return the confinement factor for the Ey field.
    
    get_dispersion()
        Return the modal dispersion.
    
    get_effective_area()
        Return the effective mode area.
    
    get_fill_factor()
        Return the fill factor.
    
    get_state()
        Return the Fimmwave state of this mode.  

    activate()
        Set fimmwave state of this mode to 1
    
    deactivate()
        Set fimmwave state of this mode to 0    
    
    field(component, include_pml=True)
        Get the value of a particular electromagnetic field from this Mode.
        Returns the field component of the whole mode profile.
        See help on this function for parameters.
    
    P():
        GUESS: Return the total power of this mode?
    
    plot( component )
        Plot the mode specified.
        See help on this function for more info.
    
    save_plot( component, prefix, Title )
        Save a plot of this mode.
        See help on this function for more info.
        
    Attributes
    ----------
    modenum : integer or list
        Which modenumbers are being operated on
    
    list_num : integer or list
        Fimmwave index to reference the desired mode: integer or list
    
    modeString : str
        fimmwave string to access desired modes or desired node.  
        eg. 'app.subnodes[{3}].subnodes[{1}].evlist.'
    
    
    '''
    # Note: Had to remove `__` from start of these local class variables, in order to allow the ./proprietary/UCSB.py file to access them directly
    def __init__(self,*args):

        if len(args) == 0:
            self.obj = None
            self.modenum = None
            self.list_num = None
            self.modeString = None
        elif len(args) == 3:
            '''Waveguide.mode(n) & Circ.mode(n) always call this case'''
            self.obj = args[0]  # the waveguide object
            num = args[1]       # mode number(s) requested
            #self.list_num = args[1] + 1     # add one to ModeNum
            self.modeString = args[2]   # fimmwave string to access the mode, including trailing `.`
        else:
            print 'Invalid number of input arguments to Mode()'
        
        # Check if requested 'all' modes:
        if isinstance(num, str):
            if num.lower() == 'all':
                #num = -1    # plot all modes
                self.modenum = range(0, get_N() )   # list of each modenumber calc'd
                self.list_num = range(1, get_N()+1)     # add one to ModeNum
            else:
                ErrStr = 'CavityMode: Mode Number must be an integer, list of integers, or the string "all".'
                raise ValueError(ErrStr)
        elif isinstance(num, int):
            self.modenum = [num]    # put num into a list
            self.list_num = [num+1]
        else:
            try:
                self.modenum = [int(x) for x in num]    # check that we're able to create a list of integers
                self.list_num = [x+1 for x in self.modenum]     # add one to ModeNum
            except:
                ErrStr = 'Mode: Mode Number must be an integer, list of integers, or the string "all".'
                raise ValueError(ErrStr)
        #end if(num)
        
        if np.max(self.list_num) > get_N():
            ErrStr = "Mode: Requested Mode number %i is too high: `set_N()` currently only calculates %i modes (which start at Mode #0)." %(np.max(self.modenum), get_N() )
            raise ValueError(ErrStr)
    
        if DEBUG(): print self.obj.name + ".Mode: modenum = ", self.modenum, ";  list_num = ", self.list_num
    
    
    #end __init__()
    
    
    def __str__(self):
        '''What to display if the Waveguide is `print`ed.'''
        string = ""
        if self.obj.name: string += "Waveguide Name: '"+self.obj.name+"'\n"  
        for n, num in enumerate(self.list_num):
            string += "Mode (%i):\n"%num
            string += "\tModal Index (n_eff) = %0.5f \n"%(self.get_n_eff(as_list=True)[n].real)
            string += "\tGroup Index (n_g) = %0.5f \n"%(self.get_n_g(as_list=True)[n].real)
            string += "\tPercent of the mode in TE direction = %0.1f %% \n"%(self.get_percent_TE(as_list=True)[n])
            string += "\tConfinement Factor (overlap with cfseg) = %0.1f \n"%(self.get_confinement(as_list=True)[n])
            string += "\tEffective Area = %0.3f  um^2 \n"%(self.get_effective_area(as_list=True)[n])
            string += "\tAttenuation = %0.3f  1/cm \n"%(self.get_attenuation(as_list=True)[n])
            string += "\tPropagation Constant = %0.3f + j*%0.3f  1/um \n"%(self.get_kz(as_list=True)[n].real, self.get_kz(as_list=True)[n].imag)
        
        return string
    
    
    def get_n_eff(self, as_list=False):
        '''Return the Modal index.
        
        Parameters
        ----------
        as_list : boolean, optional
            If a single-value is returned, by defualt it's de-listed (just a float/int).  If `as_list=True`, then it is returned as a single-element list - useful when iterating multiple modes.  False by default.'''
        out=[]
        for num in self.list_num:
            out.append(  fimm.Exec(self.modeString + "list[{" + str(num) + "}].neff")  )
        
        if len(self.list_num) == 1 and as_list==False:
            out = out[0]
        return out
    #end n_eff()
    
    def n_eff(self):
        '''Backwards compatibility only. 
        Use get_n_eff() instead.'''
        print "n_eff(): DeprecationWarning: Use get_n_eff() instead."
        return self.get_n_eff()


    def get_n_g(self, as_list=False):
        '''Return the group index.
        
        Parameters
        ----------
        as_list : boolean, optional
            If a single-value is returned, by defualt it's de-listed (just a float/int).  If `as_list=True`, then it is returned as a single-element list - useful when iterating multiple modes.  False by default.'''
        fimm.Exec(  self.modeString + "list[{" + str(self.list_num[0]) + "}].modedata.update(1)" + "\n"  )
        
        out=[]
        for num in self.list_num:
            out.append(  fimm.Exec(self.modeString + "list[{" + str(num) + "}].modedata.neffg")  )
        
        if len(self.list_num) == 1 and as_list==False:
            out = out[0]
        return out
    #end get_n_g()
    
    def n_g(self):
        '''Backwards compatibility only. 
        Use get_n_g() instead.'''
        print "n_g(): DeprecationWarning: Use get_n_g() instead."
        return self.get_n_g()


    def get_kz(self, as_list=False):
        '''Return the propagation constant.
        
        Parameters
        ----------
        as_list : boolean, optional
            If a single-value is returned, by defualt it's de-listed (just a float/int).  If `as_list=True`, then it is returned as a single-element list - useful when iterating multiple modes.  False by default.'''
        #return fimm.Exec(self.modeString+"list[{"+str(self.list_num)+"}].beta")
        out=[]
        for num in self.list_num:
            out.append(  fimm.Exec(self.modeString + "list[{" + str(num) + "}].beta")  )
        
        if len(self.list_num) == 1 and as_list==False:
            out = out[0]
        return out
    
    def kz(self):
        '''Backwards compatibility only. 
        Use get_kz() instead.'''
        print "kz(): DeprecationWarning: Use get_kz() instead."
        return self.get_kz()
    
    
    def get_percent_TE(self, as_list=False):
        '''Return the fraction of power that is TE polarized.
        If not calculated, returns `None` (Fimmwave returns -99).
        
        Parameters
        ----------
        as_list : boolean, optional
            If a single-value is returned, by defualt it's de-listed (just a float/int).  If `as_list=True`, then it is returned as a single-element list - useful when iterating multiple modes.  False by default.'''
        #return fimm.Exec(self.modeString+"list[{"+str(self.list_num)+"}].modedata.tefrac")
        out=[]
        for num in self.list_num:
            x = fimm.Exec(self.modeString + "list[{" + str(num) + "}].modedata.tefrac")
            if x == -99:     x = None
            out.append(  x  )
        
        if len(self.list_num) == 1 and as_list==False:
            out = out[0]
        return out
    
    def percent_TE(self):
        '''Backwards compatibility only. 
        Use get_percent_TE() instead.'''
        print "percent_TE(): DeprecationWarning: Use get_percent_TE() instead."
        return self.get_percent_TE()
    
    
    def get_confinement(self, as_list=False):
        '''Return the confinement factor for this mode - how much of the optical mode overlaps with the waveguide segments set as "cfseg" (confinement factor). (See FimmWave Manual Sec.4.7)
        
        Parameters
        ----------
        as_list : boolean, optional
            If a single-value is returned, by defualt it's de-listed (just a float/int).  If `as_list=True`, then it is returned as a single-element list - useful when iterating multiple modes.  False by default.
        
        Returns
        -------
        float : fractional confinement factor (0-->1)
        '''
        fimm.Exec(self.modeString+"list[{"+str(self.list_num[0])+"}].modedata.update(0)")
        #return fimm.Exec(self.modeString+"list[{"+str(self.list_num)+"}].modedata.gammaE")
        out=[]
        for num in self.list_num:
            out.append(  fimm.Exec(self.modeString + "list[{" + str(num) + "}].modedata.gammaE")  )
        
        if len(self.list_num) == 1 and as_list==False:
            out = out[0]
        return out
    
    def get_confinement_ey(self, as_list=False):
        '''This is a confinement factor estimation that includes just the Ey component of the field, defined over the region specified by the csfeg flag (see FimmWave Manual Sec.4.7).
        
        Parameters
        ----------
        as_list : boolean, optional
            If a single-value is returned, by defualt it's de-listed (just a float/int).  If `as_list=True`, then it is returned as a single-element list - useful when iterating multiple modes.  False by default.
        
        Returns
        -------
        float : fractional confinement factor (0-->1)
        '''
        fimm.Exec(self.modeString+"list[{"+str(self.list_num[0])+"}].modedata.update(0)")
        #return fimm.Exec(self.modeString+"list[{"+str(self.list_num)+"}].modedata.gammaEy")
        out=[]
        for num in self.list_num:
            out.append(  fimm.Exec(self.modeString + "list[{" + str(num) + "}].modedata.gammaEy")  )
        
        if len(self.list_num) == 1 and as_list==False:
            out = out[0]
        return out
    
    def get_fill_factor(self, as_list=False):
        '''Return the fill factor for this mode.
        This is a measure of the fraction of the mode power flux defined over the region specified by the csfeg flag (see FimmWave Manual Sec.4.7).
        
        Parameters
        ----------
        as_list : boolean, optional
            If a single-value is returned, by defualt it's de-listed (just a float/int).  If `as_list=True`, then it is returned as a single-element list - useful when iterating multiple modes.  False by default.
        
        Returns
        -------
        float : fractional fill factor (0-->1)
        '''
        fimm.Exec(self.modeString+"list[{"+str(self.list_num[0])+"}].modedata.update(0)")
        #return fimm.Exec(self.modeString+"list[{"+str(self.list_num)+"}].modedata.fillFac")
        out=[]
        for num in self.list_num:
            out.append(  fimm.Exec(self.modeString + "list[{" + str(num) + "}].modedata.fillFac")  )
        
        if len(self.list_num) == 1 and as_list==False:
            out = out[0]
        return out
    
    def get_dispersion(self, as_list=False):
        '''Return the mode dispersion (ps/nm/km) - see Fimmwave Manual Sec. 13.2.8 for definition.
        
        Parameters
        ----------
        as_list : boolean, optional
            If a single-value is returned, by defualt it's de-listed (just a float/int).  If `as_list=True`, then it is returned as a single-element list - useful when iterating multiple modes.  False by default.
        
        Returns
        -------
        float : mode dispersion (ps/nm/km)
        '''
        fimm.Exec(self.modeString+"list[{"+str(self.list_num[0])+"}].modedata.update(1)")  # calc 'all'
        #return fimm.Exec(self.modeString+"list[{"+str(self.list_num)+"}].modedata.dispersion")
        out=[]
        for num in self.list_num:
            out.append(  fimm.Exec(self.modeString + "list[{" + str(num) + "}].modedata.dispersion")  )
        
        if len(self.list_num) == 1 and as_list==False:
            out = out[0]
        return out
    
    def get_attenuation(self, as_list=False):
        '''Return the mode attenuation (1/cm), calculated from the imaginary part of the effective (modal) index.
        Corresponds to `ModeLossEV` (complex attenuation), so only available with complex solvers.
        
        Parameters
        ----------
        as_list : boolean, optional
            If a single-value is returned, by defualt it's de-listed (just a float/int).  If `as_list=True`, then it is returned as a single-element list - useful when iterating multiple modes.  False by default.
        
        Returns
        -------
        float : mode attenuation (1/cm)
        '''
        #fimm.Exec(self.modeString + "list[{" + str(self.list_num[0]) + "}].modedata.update(0)")
        #return fimm.Exec(self.modeString+"list[{"+str(self.list_num)+"}].modedata.alpha")
        '''out=[]
        for num in self.list_num:
            #out.append(  fimm.Exec(self.modeString + "list[{" + str(num) + "}].modedata.alpha")  )
            out.append(  self.get_n_eff(as_list=True).imag * 4*math.pi / (get_wavelength()*1e-4)  )
            '''
        # alpha [cm^-1] = imaginary(n_eff) * 4 pi / (wavelength [cm])
        out = (   np.imag( self.get_n_eff(as_list=True) ) * 4*math.pi / (get_wavelength()*1e-4  )   ).tolist()  
        # math on the numpy array returned by np.imag(), then conv. back to list
        
        if len(self.list_num) == 1 and as_list==False:
            out = out[0]
        return out
    
    def get_material_loss(self, as_list=False):
        '''Return the loss due to material absorption.  Based on the mode overlap with materials that have an attenuation/absorption coefficient.
        Corresponds to `ModeLossOV` in the GUI.
        If you are using a complex solver then modeLossOV is just the "material loss". When using a complex solver in absence of absorbing boundaries then modeLossEV and modeLossOV should match, provided that nx and ny are sufficient.
        If you are using a real solver then modeLossOV is the material loss approximated from the real profile. The point of calling it "OV" is to highlight that it is calculated via an overlap, and that it is therefore approximate when using a real solver.
        
        Parameters
        ----------
        as_list : boolean, optional
            If a single-value is returned, by defualt it's de-listed (just a float/int).  If `as_list=True`, then it is returned as a single-element list - useful when iterating multiple modes.  False by default.
        
        Returns
        -------
        float : mode attenuation (1/cm)
        '''
        fimm.Exec(self.modeString + "list[{" + str(self.list_num[0]) + "}].modedata.update(0)")

        out=[]
        for num in self.list_num:
            out.append(  fimm.Exec(self.modeString + "list[{" + str(num) + "}].modedata.alpha") * 1e4  )  # convert to 1/cm
        
        if len(self.list_num) == 1 and as_list==False:
            out = out[0]
        return out
    
    def get_effective_area(self, as_list=False):
        '''Return the effective core area (um^2).
        
        Parameters
        ----------
        as_list : boolean, optional
            If a single-value is returned, by defualt it's de-listed (just a float/int).  If `as_list=True`, then it is returned as a single-element list - useful when iterating multiple modes.  False by default.
        
        Returns
        -------
        float : effective core area (um^2)
        '''
        fimm.Exec(self.modeString+"list[{"+str(self.list_num[0])+"}].modedata.update(0)")
        #return fimm.Exec(self.modeString+"list[{"+str(self.list_num)+"}].modedata.a_eff")
        out=[]
        for num in self.list_num:
            out.append(  fimm.Exec(self.modeString + "list[{" + str(num) + "}].modedata.a_eff")  )
        
        if len(self.list_num) == 1 and as_list==False:
            out = out[0]
        return out
    
    def get_side_loss(self, as_list=False):
        '''Return the side power loss (1/um).  CHECK THESE UNITS - the popup window says 1/cm.
        
        Parameters
        ----------
        as_list : boolean, optional
            If a single-value is returned, by defualt it's de-listed (just a float/int).  If `as_list=True`, then it is returned as a single-element list - useful when iterating multiple modes.  False by default.
        
        Returns
        -------
        float : side power loss (1/um)
        '''
        fimm.Exec(self.modeString+"list[{"+str(self.list_num[0])+"}].modedata.update(0)")
        #return fimm.Exec(self.modeString+"list[{"+str(self.list_num)+"}].modedata.sideploss")
        out=[]
        for num in self.list_num:
            out.append(  fimm.Exec(self.modeString + "list[{" + str(num) + "}].modedata.sideploss")  )
        
        if len(self.list_num) == 1 and as_list==False:
            out = out[0]
        return out
    
    def get_state(self, as_list=False):
        '''Get fimmwave state of this mode as integer.
        INTEGER - state: 0=INACTIVE,1=ACTIVE,2=BAD or INCONSISTENT
        
        Parameters
        ----------
        as_list : boolean, optional
            If a single-value is returned, by defualt it's de-listed (just a float/int).  If `as_list=True`, then it is returned as a single-element list - useful when iterating multiple modes.  False by default.'''
        #return fimm.Exec(self.modeString+"list[{"+str(self.list_num)+"}].state")
        out=[]
        for num in self.list_num:
            out.append(  fimm.Exec(self.modeString + "list[{" + str(num) + "}].state")  )
        
        if len(self.list_num) == 1 and as_list==False:
            out = out[0]
        return out
    
    def state(self):
        '''Backwards compatibility only. 
        Use get_state() instead.'''
        print "state(): DeprecationWarning: Use get_state() instead."
        return self.get_state()
    
    def activate(self):
        '''Set fimmwave state to Active, 1'''
        #fimm.Exec(self.modeString+"setstate({"+str(self.list_num)+"},1)")
        for num in self.list_num:
            fimm.Exec(self.modeString + "setstate({" + str(num) + "},1)")

    def deactivate(self):
        '''Set fimmwave state to Inactive, 0'''
        #fimm.Exec(self.modeString+"setstate({"+str(self.list_num)+"},0)")
        for num in self.list_num:
            fimm.Exec(self.modeString + "setstate({" + str(num) + "},0)")
    
    
    def get_field(self, component, include_pml=True, as_list=False):
        '''field(component [, include_pml])
        Get the value of a particular electromagnetic field from this Mode.
        Returns the field component of the whole mode profile.
        
        Parameters
        ----------
        component : string, { 'Ex' | 'Ey' | 'Ez' | 'Hx' | 'Hy' | 'Hz' | 'I' }, case insensitive
            Choose which field component to return.  I is intensity.
            
        include_pml : { True | False }
            Whether to include perfectly-matched layer boundary conditons.  True by default.
            
        as_list : boolean, optional
            If a single-mode is returned, by default it's de-listed (just a singel array).  If `as_list=True`, then it is returned as a single-element list - useful when iterating multiple modes.  False by default.
        
        
        Returns
        -------
        fieldarray : [Nx x Ny] list of all the field values.  
            Nx and Ny are set by `pyfimm.set_Nx()` & `.set_Ny()`.
            It is recommended that you convert this to an array for performing math, eg. `numpy.array( fieldarray )`
            If multiple modes were selected (eg. `WG.mode([0,1,2])`), then a list is returned containing the numpy field array for each mode, eg. `fieldarray = [  Mode0[Nx x Ny],  Mode1[Nx x Ny],  Mode2[Nx x Ny]  ]`
        '''
        if include_pml:
            if DEBUG(): print "Mode.field(): include_pml"
            pml = '1'
        else:
            pml='0'

        component = component.lower().strip()   # to lower case & strip whitespace
        
        #if len(component) == 1:
        if component == 'Ex'.lower():
            comp='1'
        elif component == 'Ey'.lower():
           comp='2'
        elif component == 'Ez'.lower():
           comp='3'
        elif component == 'Hx'.lower():
           comp='4'
        elif component == 'Hy'.lower():
           comp='5'
        elif component == 'Hz'.lower():
           comp='6'
        elif component == 'I'.lower():
           comp='7'
        else:
            raise ValueError("Mode.field(): Invalid field component requested.")
        
        if DEBUG(): print "Mode.field():  f = " + self.modeString + \
        "list["+str(self.list_num)+"].profile.data.getfieldarray("+comp+","+pml+")  \n\t f.fieldarray" 
        
        # Check if modes have been calc()'d:
        a = fimm.Exec(self.modeString+"list["+str(self.list_num[0])+"].profile.update")
        # Check if modes have been calc()'d:
        if DEBUG(): print "field():  #",a[:-2].strip(),'#\n'
        if a[:-2].strip() != '':
            WarningString = "FimmWave error: please check if the modes have been calculated via WG.calc().\n\tFimmWave returned: `%s`"%a[:-2].strip()
            raise UserWarning(WarningString)
        
        #fimm.Exec("Set f = " + self.modeString + "list[" + str(self.list_num) + "].profile.data.getfieldarray(" + comp + "," + pml + ")  \n"  )
        #field =  fimm.Exec("f.fieldarray")
        out=[]
        for num in self.list_num:
            fimm.Exec("Set f = " + self.modeString + "list[" + str(num) + "].profile.data.getfieldarray(" + comp + "," + pml + ")  \n"  )  # must set this as a variable to avoid memory error
            out.append(  fimm.Exec("f.fieldarray")  )   # grab the array (as list)
        
        if len(self.list_num) == 1 and as_list==False:
            out = out[0]
        return out

        #if DEBUG(): print "Mode.field(): \n", field, "\n--------------"
        #return np.array(field)
    #end get_field()
    
    # Alias for this function
    field = get_field
        
        
    def P(self):
        '''Return the Power Density - I think in J/um'''
        if len(self.list_num) > 1:
            ErrStr = "Mode.P(): Only supports a single mode number being passed."
            raise NotImplementedError(ErrStr)
        else:
            num = self.list_num[0]
            
        # Check if modes have been calc()'d:
        a = fimm.Exec(self.modeString+"list["+str(num)+"].profile.update"+"\n")
        # Check if modes have been calc()'d:
        if DEBUG(): print "P():  #",a[:-2].strip(),'#\n'
        if a[:-2].strip() != '':
            ErrStr = "FimmWave error: please check if the modes have been calculated via WG.calc().\n\tFimmWave returned: `%s`"%a[:-2].strip()
            raise UserWarning(ErrStr)
        
        fimm.Exec(self.modeString+"list["+str(num)+"].profile.data.writeamf("+\
        "mode"+str(num)+"_pyFIMM.amf,%10.9f)"   )

        ## AMF File Clean-up
        fin = open("mode"+str(num)+"_pyFIMM.amf", "r")
        data_list = fin.readlines()
        fin.close()

        # Delete File Header
        nxy_data = data_list[1]
        xy_data = data_list[2]
        slvr_data = data_list[6]
        del data_list[0:9]
        
        fout = open("nxy"+str(num)+"_pyFIMM.txt", "w")
        fout.writelines(nxy_data)
        fout.close()
        nxy = pl.loadtxt("nxy"+str(num)+"_pyFIMM.txt", comments='//')
        nx = int(nxy[0])
        ny = int(nxy[1])

        fout = open("xy"+str(num)+"_pyFIMM.txt", "w")
        fout.writelines(xy_data)
        fout.close()
        xy = pl.loadtxt("xy"+str(num)+"_pyFIMM.txt", comments='//')
        
        fout = open("slvr"+str(num)+"_pyFIMM.txt", "w")
        fout.writelines(slvr_data)
        fout.close()
        iscomplex = pl.loadtxt("slvr"+str(num)+"_pyFIMM.txt", comments='//')
        
         # Resave Files
        fout = open("Ex"+str(num)+"_pyFIMM.txt", "w")
        fout.writelines(data_list[1:nx+2])
        fout.close()
        fout = open("Ey"+str(num)+"_pyFIMM.txt", "w")
        fout.writelines(data_list[(nx+2)+1:2*(nx+2)])
        fout.close()
        fout = open("Hx"+str(num)+"_pyFIMM.txt", "w")
        fout.writelines(data_list[3*(nx+2)+1:4*(nx+2)])
        fout.close()
        fout = open("Hy"+str(num)+"_pyFIMM.txt", "w")
        fout.writelines(data_list[4*(nx+2)+1:5*(nx+2)])
        fout.close()
        
        del data_list
        
        # Get Data
        Ex = pl.loadtxt("Ex"+str(num)+"_pyFIMM.txt")
        Ey = pl.loadtxt("Ey"+str(num)+"_pyFIMM.txt")
        Hx = pl.loadtxt("Hx"+str(num)+"_pyFIMM.txt")
        Hy = pl.loadtxt("Hy"+str(num)+"_pyFIMM.txt")
        
        Ex = np.array(Ex)
        Ey = np.array(Ey)
        Hx = np.array(Hx)
        Hy = np.array(Hy)
        
        Sz = (Ex*Hy.conjugate() - Ey*Hx.conjugate()) / 2.0
        
        xStart = xy[0]
        xEnd = xy[1]
        dx = (xEnd - xStart)/nx
        
        yStart = xy[2]
        yEnd = xy[3]
        dy = (yEnd - yStart)/ny
        
        dA = dx*dy*1e-12
        return sum(Sz)*dA
    #end P()
    
    
    
    def plot(self, *args, **kwargs ):
        #, include_pml=True):
        '''plot( [ component, title='str', return_handles=False ] )
        Plot the mode fields with matplotlib.  If multiple modes are specified (eg. `WG.mode([0,1,2]).plot()` ) then each mode will be plotted in a 2-column subplot on one figure.
        
        Parameters
        ----------
        component : { 'Ex' | 'Ey' | 'Ez' | 'Hx' | 'Hy' | 'Hz' }, case insensitive, optional
            Choose which field component to return.
            If omitted, will choose the Ex or Ey component depending on which has a higher fraction of the field (TEfrac).  For plots of multiple modes, this check of TEfrac will be performed for each specified mode.
        
        title : string, optional
            Will prepend this text to the output filename, and do the same to the Plot Title.
            If not provided, the name of the passed Waveguide component, Mode Number & Field Component will be used to construct the filename & plot title.
        
        annotations : boolean, optional
            If true, the effective index, mode number and field component will written on each mode plot.  True by default.
        
        return_handles : { True | False }, optional
            If True, will return handles to the figure, axes and images.  False by default.
        
        
        Returns
        -------
        fig, axes, imgs
            The matplotlib figure, axis and image (`pyplot.imshow()` ) handles.  Only returned if `return_handles=True`
        `fig` is the handle to the whole figure, allowing you to, for example, save the figure yourself (instead of using `Mode.save_plot()` ) via `fig.savefig(pat/to/fig.png)`.
        `ax` is a list of the possibly multiple axes created by a call to maplotlib.pyplot.subplots().  Note the non-matlab-like behviour of the returned axes array: they take the form of the actual subplots layout.  
        For example, for a single axis created by
        >>> fig, axes, imgs = strip.mode( 0 ).plot( return_handles=True)
        axes is a single axis handle.
        For two axes (eg. `mode( [0,1] ).plot()`, `axes` is a two-valued array: [ax0, ax1]
        However, for more than 2 modes, `axes` takes the form of the subplots layout, like so:
        >>> fig, axes, imgs = strip.mode( [0,1,2,3,4,5] ).plot( return_handles=True)
        >   axes = [  [ax0, ax1],
                      [ax2, ax3],
                      [1x4, ax5]   ]
        So be careful when indexing into a plot of numerous modes, due to the weirdness of `pyplot.subplots()`.
        
        
        Examples
        --------
        >>> stripWG.mode(0).calc()  # calculate the modes of the waveguide
        >>> stripWG.mode(0).plot()
            Plot the E-field component with the maximum field by default (eg. Ex for TE, and Ey for TM)
            
        >>> stripWG.mode(0).plot('Hy') 
            plot the Hy component instead
            
        >>> stripWG.mode(0).plot(title='My Mode') 
            plot Ex component with plot title "My Mode - mode 0.png"
        
        >>> stripWG.mode('all').plot()
            Will plot the Ex or Ey component (whichever is the major comp.) of all calc'd modes (as specified by `set_N()` ).  
        
        >>> stripWG.mode( [0,2] ).plot('Ey', title='Ey of Modes 0 and 2')
            Plot the Ey components of Modes 0 & 2 on one figure with custom figure title.
        
        >>> fig1, ax1, im = stripWG.mode(0).plot(return_handles = True) 
            Return the matplotlib figure, axis and image handles, for future manipulation.  
            
        For example, this allows you to add other annotations to a plot, and then save the figure:
        
        >>> fig1, ax1, im = stripWG.mode(0).plot(return_handles = True) 
        >>> ax1.text( 0.05, 0.05,        \
        >>>    r"$\alpha = %0.3f cm^{-1}$" %(  stripWG.mode(0).get_attenuation()  ),  \
        >>>    transform=axis.transAxes, horizontalalignment='left', color='green', fontsize=9, fontweight='bold')
        >>> fig1.savefig('Mode with attenuation.png')
        
        '''
        import os, sys
        
        if len(args) == 0:
            field_cpt_in = None
            '''
            tepercent = fimm.Exec(self.modeString+"list[{"+str(self.list_num)+"}].modedata.tefrac")
            if tepercent > 50:
                field_cpt = 'Ex'.lower()
            else:
                field_cpt = 'Ey'.lower()
            '''
        elif len(args) == 1:
            field_cpt_in = args[0]
            if isinstance(field_cpt_in,str) or field_cpt_in==None :
                if field_cpt_in != None:
                    '''args[0] is a string:   '''
                    field_cpt = field_cpt_in.lower().strip()
                #else args[0] = None  !
            else:
                ErrStr = "Mode.plot(): Unrecognized field component requested: `" + str(args[0]) + "`.  See `help(<pyfimm>.Mode.plot)` for more info."
                raise ValueError(ErrStr)
        else:
            ErrStr = "Mode.plot(): Invalid number of arguments.  See `help(<pyfimm>.Mode.plot)` for more info."
            raise ValueError(ErrStr)
        
        return_handles = kwargs.pop('return_handles', False)
        annotations = kwargs.pop('annotations', True)
        
        ptitle = kwargs.pop('title',None)
        if ptitle:
            plot_title = ptitle + " - Mode " + str(self.modenum)
        else:
            plot_title = '"'+self.obj.name+'":' + " Mode " + str(self.modenum)
        
        
        '''Unused kwargs returned at end of this function'''
        
        
        # Check if modes have been calc()'d:
        a = fimm.Exec(self.modeString+"list["+str(self.list_num[0])+"].profile.update")
        # Check if modes have been calc()'d:
        if DEBUG(): print "plot():  #",a[:-2].strip(),'#\n'
        if a[:-2].strip() != '':
            ErrStr = "FimmWave error: please check if the modes have been calculated via `WG.calc()`.\n\tFimmWave returned: `%s`"%a[:-2].strip()
            raise UserWarning(ErrStr)
        
        
        # get effective indices of each mode (add to plot):
        nmodes = self.get_n_eff(as_list=True)
        if DEBUG(): print "mode.plot(): nmodes =", nmodes
        
        # create the required number of axes:
        # Options for the subplots:
        sbkw = {'axisbg': (0.15,0.15,0.15)}    # grey plot background
        
        if len(self.list_num) == 1:
            fig1, axs = plt.subplots(nrows=1, ncols=1, subplot_kw=sbkw)
        else:
            Rows = int(   math.ceil( len(self.list_num)/2. )   )
            fig1, axs = plt.subplots(  nrows=Rows , ncols=2, sharex=True, sharey=True, subplot_kw=sbkw)
            if len(self.list_num) % 2 == 1:
                '''If odd# of modes, Delete the last (empty) axis'''
                fig1.delaxes( axs[ len(axs)-1,  1]  )
                #axs = axs[:-1]  # remove del'd axis from list
        
        fig1.suptitle(plot_title)   # figure title
        fig1.canvas.draw()  # update the figure
        
        ims = []
        for n, num   in   enumerate(self.list_num):
            # Which axis to draw on:
            if len(self.list_num) == 1:
                '''only single plot'''
                axis = axs
            elif len(np.shape(axs)) == 1:
                '''only one row, so axs = [ax1, ax2]'''
                axis = axs[ n ]
            else:
                '''multiple rows, so axs=[ [ax1,ax2], [ax3,ax4]...]'''
                axis = axs[ math.floor( n/2. ),  n%2. ]
            
            # write an AMF file with all the field components.
            mode_FileStr = "mode"+str(num)+"_pyFIMM.amf"     # name of files
            # SubFolder to hold temp files:
            if not os.path.isdir(str( AMF_FolderStr() )):
                os.mkdir(str( AMF_FolderStr() ))        # Create the new folder
            mode_FileStr = os.path.join( AMF_FolderStr(), mode_FileStr )
            
            if DEBUG(): print "Mode.plot():  " + self.modeString+"list[" + str(num) + "].profile.data.writeamf("+mode_FileStr+",%10.6f)"
            fimm.Exec(self.modeString+"list[" + str(num) + "].profile.data.writeamf("+mode_FileStr+",%10.6f)")

            ## AMF File Clean-up
            #import os.path, sys  # moved to the top
            fin = open(mode_FileStr, "r")
            if not fin: raise IOError("Could not open '"+ mode_FileStr + "' in " + sys.path[0] + ", Type: " + str(fin))
            data_list = fin.readlines()
            fin.close()

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
            mode_FileStr = mode_FileStr+"_"+field_cpt.strip().lower()
            fout = open(mode_FileStr, "w")
            fout.writelines(data)
            fout.close()
            
            # Get Data
            if iscomplex == 1:
                field_real = pl.loadtxt(mode_FileStr, usecols=tuple([i for i in range(0,2*ny+1) if i%2==0]))
                field_imag = pl.loadtxt(mode_FileStr, usecols=tuple([i for i in range(0,2*ny+2) if i%2!=0]))
            else:
                field_real = pl.loadtxt(mode_FileStr)
            
            '''field_real = np.real(field)'''
            
            
            # Plot Data
            xStart = xy[0]
            xEnd = xy[1]
            yStart = xy[2]
            yEnd = xy[3]
            
            im = axis.imshow(pl.rot90(abs(field_real),1), cmap=cm.hot, aspect='auto', extent=(xStart,xEnd,yStart,yEnd))
            im.set_interpolation('bilinear')
            ims.append(im)

            #axis.set_xlabel('x ($\mu$m)')
            #axis.set_ylabel('y ($\mu$m)')
            
            if annotations:
                titlestr = "Mode(" + str(num-1) + "): " + field_cpt.title()
                #axis.set_title(  titlestr  )
                axis.text( 0.95, 0.9, titlestr, transform=axis.transAxes, horizontalalignment='right', color='green', fontsize=9, fontweight='bold')
                
                n_str = "$\mathregular{n_{eff} =}$ %0.5f"%(nmodes[n].real)
                axis.text( 0.05, 0.9, n_str, transform=axis.transAxes, horizontalalignment='left', color='green', fontsize=9, fontweight='bold')
            fig1.canvas.window().raise_()    # bring plot window to front
            fig1.canvas.draw()  # update the figure
        #end for(list_num)
        
        '''
        ax1.set_xlabel('x ($\mu$m)')
        ax1.set_ylabel('y ($\mu$m)')
        ax1.set_title(  self.obj.name + ": Mode(" + str(self.modenum) + "): " + field_cpt.title()  )
        '''
        #fig1.canvas.window().raise_()    # bring plot window to front
        #fig1.canvas.draw()
        fig1.show()
        
        
        if kwargs:
            '''If there are unused key-word arguments'''
            ErrStr = "WARNING: Mode.plot(): Unrecognized keywords provided: {"
            for k in kwargs.iterkeys():
                ErrStr += "'" + k + "', "
            ErrStr += "}.    Continuing..."
            print ErrStr
        
        if return_handles: return fig1, axs, ims
        #end plot(Waveguide/Circ)
        
    #end plot()
    
    
    def save_plot(self,*args, **kwargs):
        '''save_plot( [ component, title='str', path=None ] )
        Save the mode profile to a file.  Actually just calls Mode.plot(component, title) & saves the resulting figure.
        
        Parameters
        ----------
        component : { 'Ex' | 'Ey' | 'Ez' | 'Hx' | 'Hy' | 'Hz' }, case insensitive, optional
            Choose which field component to return.
            If omitted, will choose the Ex or Ey component depending on which has a higher fraction of the field (TEfrac).
        
        title : string, optional
            Will prepend this text to the output filename, and do the same to the Plot Title.  If `path` is not provided, the filename will also have this text prepended.
            If not provided, the name of the passed Waveguide component, Mode Number & Field Component will be used to construct the filename & plot title.
        return_handles : { True | False }, optional
            If True, will return handles to the figure, axes, legends and lines.  False by default.
            
        path : string, optional
            Path to save file to, including base filename.  File extension will be automatically appended.
        
        closefigure : boolean, optional
            If `True`, will close the figure window after the file has been saved.  Useful for large for() loops.
        
        Extra keyword-arguments are passed to Mode.plot()
        
        
        Examples
        --------
        >>> stripWG.mode(0).calc()      # calculate the modes of the waveguide
        >>> stripWG.mode(0).save_plot()
            saves the Ex component to file "mode 1 - Ex.png"
            
        >>> stripWG.mode(0).save_plot('Hy') 
            save the Hy component instead
            
        >> stripWG.mode(0).save_plot(title='My Mode') 
            saves Ex component to file "My Mode - mode 1 - Ex.png"
        
        >> stripWG.mode(0).save_plot('I', title='My Mode') 
            saves Intensity  to file "My Mode - mode 1 - Ex.png"
        
        >> fig1, ax1, im = stripWG.mode(0).save_plot(return_handles = True) 
            Return the matplotlib figure, axis and image handles, for future manipulation.
        
        Returns
        -------
        fig1, ax1, im
            The matplotlib figure, axis and image (imshow) handles, returned only if `return_handles = True`.
        '''
        import os.path
        
        if len(args) == 0:
            field_cpt = None
            '''
            tepercent = fimm.Exec(self.modeString+"list[{"+str(self.list_num)+"}].modedata.tefrac")
            if tepercent > 50:
                field_cpt = 'Ex'.lower()
            else:
                field_cpt = 'Ey'.lower()
            '''
        elif len(args) == 1:
            field_cpt = args[0].lower().strip()
        else:
            ErrStr = "Mode.plot(): Invalid number of arguments.  See `help(<pyfimm>.Mode.plot)` for more info."
            raise ValueError(ErrStr)
        
        returnhandles = kwargs.pop('return_handles', False)
        path = kwargs.pop('path', None)
        closefigure = kwargs.pop('closefigure', False)
        
        ptitle = kwargs.pop('title',None)
        if ptitle:
            plot_title = ptitle + " - Mode " + str(self.modenum)
        else:
            plot_title = self.obj.name + " - Mode " + str(self.modenum)
        
        # plot the mode:
        handles   =  self.plot(field_cpt, title=ptitle, return_handles=True, **kwargs)
        fig1 = handles[0]
        if path:
            savepath = path + '.png'  
        else:
            savepath = plot_title + '.png'
        print "Saving Plot to:", savepath
        fig1.savefig(  savepath  )   # save the figure
        
        if closefigure: plt.close(fig1)
        
        if kwargs:
            '''If there are unused key-word arguments'''
            ErrStr = "WARNING: Mode.save_plot(): Unrecognized keywords provided: {"
            for k in kwargs.iterkeys():
                ErrStr += "'" + k + "', "
            ErrStr += "}.    Continuing..."
            print ErrStr
        
        if returnhandles:     return handles
    #end save_plot()
    
#end class Mode
    
    
    
 