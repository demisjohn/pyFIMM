# ColorMap
# Red-Black-Blue, like Matlab's 'FireIce' or 'HotCold'
#  http://stackoverflow.com/questions/24997926/making-a-custom-colormap-using-matplotlib-in-python

from matplotlib.colors import LinearSegmentedColormap
ltblue = [x/255. for x in (170,170,255)]     # set the RBG vals here
ltred = [x/255. for x in (255,100,100)]
cm_coldhot = LinearSegmentedColormap.from_list('coldhot',  [ltblue, 'black', ltred] , N=256)