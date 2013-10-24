#------------------------------------------------------------------------------
#
#  Copyright (c) 2005, Enthought, Inc.
#  All rights reserved.
#
#  This software is provided without warranty under the terms of the BSD
#  license included in enthought/LICENSE.txt and may be redistributed only
#  under the conditions described in the aforementioned license.  The license
#  is also available online at http://www.enthought.com/licenses/BSD.txt
#
#  Thanks for using Enthought open source!
#
#  Author: David C. Morrill
#  Date:   10/21/2004
#
#------------------------------------------------------------------------------

""" Defines file editors for the wxPython user interface toolkit.
"""

#-------------------------------------------------------------------------------
#  Imports:
#-------------------------------------------------------------------------------

import wx
from traits.api import (File, HasTraits, Button, Instance, Any, Callable, 
	Property, Directory, Bool)
from traitsui.wx.helper import TraitsUIPanel
from traitsui.api import (View, Item, CustomEditor, Handler, UIInfo)
from traitsui.file_dialog import open_file

from traitsui.wx.custom_editor import CustomEditor as CustomEditorKlass
from directory_dialog import open_directory

def mkeditor ( parent,editor,use_dir=False, *args ):
	""" Custom editor factory.  Must be instantiated on top of an
		InteractiveSubwindow instance with an implemented reconstruct().
	"""

	#IE the file trait is in the InteractiveSubwindow, not somewhere else

	editor.control = panel = TraitsUIPanel( parent, -1 )
	sizer        = wx.BoxSizer( wx.HORIZONTAL )

	if use_dir:
		editor.use_dir = True

	pad = 8

	bmp = wx.ArtProvider.GetBitmap ( wx.ART_FOLDER_OPEN, size= (15,15))
	button = wx.BitmapButton(panel, -1, bitmap=bmp)
	
	editor.text_control = text_control = wx.TextCtrl(panel, -1, '',
		style=wx.TE_PROCESS_ENTER)

	_do_update_obj = lambda ev:update_file_obj(ev,editor)
#	_do_update_obj = editor.update_file_obj

	wx.EVT_TEXT_ENTER( panel, text_control.GetId(), _do_update_obj)
	wx.EVT_KILL_FOCUS( text_control, _do_update_obj)

	sizer.Add( text_control, 1, wx.EXPAND | wx.ALIGN_CENTER )
	sizer.Add( button,  0, wx.RIGHT   | wx.ALIGN_CENTER, pad )

	wx.EVT_BUTTON( panel, button.GetId(),
		lambda ev:button_click(ev,editor) )
#		editor.button_click )
	panel.SetSizerAndFit( sizer )

	return panel

#methods referring to editor factory, which is not a real object
def button_click(event,editor):
	if editor.use_dir:
		file_selected=open_directory(entries=20)
	else:
		file_selected=open_file(entries=20)
	if file_selected:
		editor.value=file_selected
	#editor.object.reconstruct()
	editor.ui.handler.reconstruct()
	#editor.text_control.SetValue(editor.value)

def update_file_obj(event,editor):
	editor.value=editor.text_control.GetValue()

#custom editor on traitsui abstraction level
class CustomFileEditor(CustomEditor):
	'''abstraction layer for Custom File editor.  This editor must be
	instantiated within a view of an InteractiveSubwindow object with a
	correctly implemented reconstruct()'''
	#factory = Callable(mkeditor)
	factory = Property #Callable

	use_dir = Bool(False)

	#klass = Property

	def _get_klass(self):
		#tell the editor to use this instead of importing from traitsui.wx
		return CustomFileEditorKlass

	def _get_factory(self):
		if self.use_dir:
			return lambda p,e:mkeditor(p,e,True)
		else:
			return mkeditor

class CustomDirectoryEditor(CustomFileEditor):
	use_dir = True

#custom editor on level of toolkit (i.e., wx)
class CustomFileEditorKlass(CustomEditorKlass):
	text_control = Any # Instance( wx._control.TextCtrl )

	use_dir = Bool(False)

	def update_editor(self):
		self.text_control.SetValue(self.value)

	def button_click(self,event):
		#print "SKAGGGEY MUFFIN"
		file_selected=open_file()
		if file_selected:
			self.value=file_selected
		self.object.reconstruct()

	def update_file_obj(self,event):
		self.value=self.text_control.GetValue()

#test as main file
if __name__=='__main__':
	class Farkish(Handler):
		f=File('saukish')
		b=Button
		info=Instance(UIInfo)

		traits_view=View(
			Item('f',editor=CustomFileEditor()),
			Item('b'),
			height=500,width=500)

		def _b_fired(self):
			print self.f

		def init_info(self,info):
			self.info=info
		def reconstruct(self):
			self.info.ui.dispose()
			self.info.object.edit_traits()

	Farkish().configure_traits()
