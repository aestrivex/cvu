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
from matplotlib.lines import Line2D
import wx

def make_plot(parent,editor):
	fig=editor.object.figure
	panel=wx.Panel(parent,-1)
	canvas=FigureCanvasWxAgg(panel,-1,fig)
	toolbar=NavigationToolbar2Wx(canvas)
	toolbar.Realize()
	sizer=wx.BoxSizer(wx.VERTICAL)
	sizer.Add(canvas,1,wx.EXPAND|wx.ALL,1)
	sizer.Add(toolbar,0,wx.EXPAND|wx.ALL,1)
	panel.SetSizer(sizer)
	def onclick(event):
		print event
	canvas.mpl_connect('button_press_event',onclick)
	return panel

class CirclePlot(HasTraits):
	figure=Instance(Figure,())
	axes=Instance(Axes)
	line=Instance(Line2D)
	traits_view=View(
					Item('figure',editor=CustomEditor(make_plot),
						resizable=True))
	scale=Range(0.1,10.0)
	self.x=Array(value=np.linspace(-5,5,512))
	y=Property(Array,depends_on=['scale','x'])

	def _axes_default(self):
		return self.figure.add_subplot(111)
	def _line_default(self):
		return self.axes.plot(self.x,self.y)[0]

		#def mouse_click(event):
		#	print "DOGGY"
		#	print event

		#print dir(self.figure)
		#print dir(self.figure.canvas)
		#self.figure.canvas.callbacks.process('button_press_event',None)
	
	def __call__(self,event):
		print "doggy"
		print event

if __name__=="__main__":
	noodles=CirclePlot()
	noodles.configure_traits()
