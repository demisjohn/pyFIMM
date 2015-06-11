# ColorMap
# Red-Black-Blue, like Matlab's 'FireIce' or 'HotCold'
#  http://stackoverflow.com/questions/24997926/making-a-custom-colormap-using-matplotlib-in-python

from matplotlib.colors import LinearSegmentedColormap
ltblue = [x/255. for x in (170,170,255)]     # set the RBG vals here
ltred = [x/255. for x in (255,100,100)]
cm_hotcold = LinearSegmentedColormap.from_list('coldhot',  [ltblue, 'black', ltred] , N=256)

'''
# Use as so, 
#   to keep black at 0, set vmin/vmax to extent of data:
maxfield = np.max(   np.abs(  np.array(field).real  )   )
cont = ax.contourf( np.array(x), np.array(y), np.array(field) , vmin=-maxfield, vmax=maxfield, cmap=cm_coldhot) 

(also for pcolor() etc.)        
'''