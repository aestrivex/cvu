#    (C) Roan LaPlante 2013 rlaplant@nmr.mgh.harvard.edu
#
#	 This file is part of cvu, the Connectome Visualization Utility.
#
#    cvu is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import wx
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wx import NavigationToolbar2Wx

from traits.api import *
from traitsui.wx.editor import Editor
from traitsui.basic_editor_factory import BasicEditorFactory
import numpy as np
import time 

#This code is extensively adapted from Gael Varoquax's example code for
#hacking a traited matplotlib editor

class _MPLFigureEditor(Editor):

	scrollable = True
	parent = Any
	canvas = Instance(FigureCanvasWxAgg)
	tooltip = Instance(wx._misc.ToolTip)

	# define some callbacks that need to be added and removed on the fly.
	# these callbacks can't be passed around easily
	release_cid = Int
	motion_cid = Int

	waiting_for_tooltip = Bool(False)

	def init(self,parent):
		self.parent=parent
		self.control=self._create_canvas(parent)

	def update_editor(self):
		pass
		#print 'morvunskar'
		#self.reset_editor()
		#self.control=self._create_canvas(self.parent)

	def _create_canvas(self,parent):
		#unsure if there is a way to avoid hard coding these function names
		#obviously this is hacky and undesirable
		fig=self.object.circ
		panel=wx.Panel(parent,-1)
		self.canvas=FigureCanvasWxAgg(panel,-1,fig)
		sizer=wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.canvas,1,wx.EXPAND|wx.ALL,1)
		#toolbar=NavigationToolbar2Wx(self.canvas)
		#toolbar.Realize()
		#sizer.Add(toolbar,0,wx.EXPAND|wx.ALL,1)
		panel.SetSizer(sizer)
		#self.canvas.mpl_connect('button_press_event',
		#	lambda ev:self.object.circ_click(ev,self))
		#self.motion_cid=self.canvas.mpl_connect('motion_notify_event',
		#	lambda ev:self.object.circ_mouseover(ev,self))

		self.canvas.mpl_connect('button_press_event',self.object.circle_click)
		self.canvas.mpl_connect('motion_notify_event',
			lambda ev:self.object.circle_mouseover(ev,self.tooltip))

		self.tooltip=wx.ToolTip(tip='')
		self.tooltip.SetDelay(2000)
		self.canvas.SetToolTip(self.tooltip)
		return panel

	def _process_click(self,event):
		if event.button==3:
			self.ds.display_all()
		elif event.button==1 and (7 <= event.ydata <= 8):
			n=self.ds.nr_labels*event.xdata/(np.pi*2)+.5*np.pi/self.ds.nr_labels
			self.ds.display_node(int(np.floor(n)))

	def _process_circ_click(self,event,cvu):
		# if the user right clicked, just display all
		if event.button==3:
			cvu.display_all()
			return
		elif event.button==2:
			self.object.mpleditor=self
			return
		# the user left clicked, lets wait and see if he wants to pan
		self.release_cid=self.canvas.mpl_connect('button_release_event',
			lambda ignore:self._single_click(event,cvu))
			# use the existing event coordinates; theres probably no difference
			# but if there were the originals would be more reliable

		#self.motion_cid=self.canvas.mpl_connect('motion_notify_event',
		#	self._pan_decide)

	def _single_click(self,event,cvu):
		self._clear_callbacks()
		#this event has xdata and ydata in reverse polar coordinates (theta,r)
		#do some algebra to figure out which ROI based on the angle
		if event.button==1 and event.ydata>=7 and event.ydata<=8:
			nod=cvu.nr_labels*event.xdata/(np.pi*2)+.5*np.pi/cvu.nr_labels
			#the formula for the correct node, assuming perfect clicking,
			#is floor(n*theta/2pi).  however, matplotlib seems to not do great
			#with this, the clicking is often too high, so i add this correction
			cvu.display_node(int(np.floor(nod)))

	def _possibly_show_tooltip(self,event,cvu):
		self._clear_callbacks()
		if event.ydata>=7 and event.ydata<=8:
			nod=int(np.floor(cvu.nr_labels*event.xdata/(np.pi*2)
				+.5*np.pi/cvu.nr_labels))
			self.tooltip.Enable(True)
			self.tooltip.SetTip(cvu.labnam[nod])
		else:
			self.tooltip.Enable(False)

		#if and when panning is also done, this logic needs to become a bit
		#more complex to respond only to novel mouse events and constantly
		#clear old callbacks.
		
		#self.waiting_for_tooltip=True
		#self.motion_cid=self.canvas.mpl_connect('motion_notify_event',
		#	self._move_unset_tooltip)
		#time.sleep(1)

	def _move_unset_tooltip(self,ignore):
		self.waiting_for_tooltip=False

	def _clear_callbacks(self):
		self.canvas.mpl_disconnect(self.release_cid)
		#self.canvas.mpl_disconnect(self.motion_cid)

	def _pan_decide(self,event):
		ax=self.canvas.figure.get_axes()[0]
		ax.set_navigate_mode('PAN')
		ax.start_pan(event.x,event.y,1)
		self._pan(event)
		self._clear_callbacks()
		self.release_cid=self.canvas.mpl_connect('button_release_event',
			self._end_pan)
		self.motion_cid=self.canvas.mpl_connect('motion_notify_event',
			self._pan)

	def _pan(self,event):
		ax = self.canvas.figure.get_axes()[0]
		ax.drag_pan(1,event.key,event.x,event.y)
		self.canvas.draw()
	
	def _end_pan(self,event):
		ax = self.canvas.figure.get_axes()[0]
		ax.end_pan()
		self._clear_callbacks()

class MPLFigureEditor(BasicEditorFactory):

	klass = _MPLFigureEditor
