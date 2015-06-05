#/usr/bin/python2.7
#
# __init__.py
# Module to load all PhotonDesign Python libraries/modules
# 	This file will cause the folder it's in to be a Python module
# 	to be importable as a module, where the module automatically includes
#	all the files within the folder.
#
# Taken from here: 
#	http://stackoverflow.com/questions/1057431/loading-all-modules-in-a-folder-in-python
#
# Demis John, Oct 2014
#
############################################################

import os       # file path manipulations
import glob     # file-name matching

# the following directs __init__ to import add to __all__ all the files within it's directory that match *.py
__all__ = [ os.path.basename(f)[:-3] for f in glob.glob(os.path.dirname(__file__)+"/*.py")]
