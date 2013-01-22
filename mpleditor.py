import wx
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import *
from matplotlib.backends.backend_wx import *

from traits.api import *
from traitsui.wx.editor import Editor
from traitsui.basic_editor_factory import BasicEditorFactory

#This code is extensively adapted from Gael Varoquax's example code for
#hacking a traited matplotlib editor

class _MPLFigureEditor(Editor):

	scrollable = True
	parent = Any
	#canvas = Instance(FigureCanvasWxAgg)

	def init(self,parent):
		self.parent=parent
		self.control=self._create_canvas(parent)
		#self.set_tooltip()

	def update_editor(self):
		pass
		#print 'morvunskar'
		#self.reset_editor()
		#self.control=self._create_canvas(self.parent)

	def _create_canvas(self,parent):
		#unsure if there is a way to avoid hard coding these function names
		#obviously this is hacky and undesirable
		fig=self.object.circ_fig
		panel=wx.Panel(parent,-1)
		canvas=FigureCanvasWxAgg(panel,-1,fig)
		sizer=wx.BoxSizer(wx.VERTICAL)
		sizer.Add(canvas,1,wx.EXPAND|wx.ALL,1)
		panel.SetSizer(sizer)
		canvas.mpl_connect('button_press_event',self.object.circ_click)
		return panel

class MPLFigureEditor(BasicEditorFactory):

	klass = _MPLFigureEditor
