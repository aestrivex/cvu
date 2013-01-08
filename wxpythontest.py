from traits.api import *
from traitsui.api import *
import numpy as np
import scipy.io as sio
import cvu_utils
from matplotlib.backends.backend_wxagg import *
from matplotlib.backends.backend_wx import *
from matplotlib.backends.backend_agg import *
from matplotlib import *
from matplotlib.axes import Axes
import wx
import clickable_circle_plot as circ

class CirclePlot(HasTraits):
	figure=Instance(Figure,())
	axes=Instance(Axes)
	
	traits_view=View(
					Item('figure',editor=CustomEditor(
						circ.make_plot),
						resizable=True))

	def __init__(self):
		self.cm=cvu_utils.loadmat(\
			'/autofs/cluster/neuromind/rlaplant/pdata/adjmats/pliA1.mat',
            'adj_matrices')
		print np.shape(self.cm)
		self.labnam=[]
		fd=open('/autofs/cluster/neuromind/rlaplant/mayavi/cvu/order_sparc')
		for line in fd:
			if line.strip() != "delete":
				self.labnam.append(line.strip())

		doggy,inds = circ.plot_connectivity_circle(self.cm,self.labnam)
		print inds
		#print dir(doggy)
		#print type(doggy)
		self.figure=doggy

		#def mouse_click(event):
		#	print "DOGGY"
		#	print event

		#print dir(self.figure)
		#print dir(self.figure.canvas)
	

if __name__=="__main__":
	noodles=CirclePlot()
	noodles.configure_traits()
