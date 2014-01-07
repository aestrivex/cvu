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

import os
import sys
from traits.api import (HasTraits,List,Instance,Dict,Button,Str,
	Bool,on_trait_change)
from traitsui.api import (ButtonEditor,ShellEditor,View,Item,Spring,HSplit,
	VSplit,Group,InstanceEditor)
import dataset
import dialogs
from controller import Controller

from viewport import Viewport,DatasetViewportInterface

from traits.api import Event

class ErrorHandler(HasTraits):
	quiet=Bool

	def __init__(self,quiet=False,**kwargs):
		super(ErrorHandler,self).__init__(**kwargs)
		self.quiet=quiet

	def error_dialog(self,message):
		sys.stderr.write('%s\n'%message)
	
	def warning_dialog(self,message):
		sys.stderr.write('%s\n'%message)
	
	def verbose_msg(self,message):
		if not self.quiet: print message

class CvuGUI(ErrorHandler,DatasetViewportInterface):
	controller=Instance(Controller)

	def _mayavi_port_default(self):
		return Viewport(self.controller.ds_orig,
			view_type='3D Brain')
	def _matrix_port_default(self):
		return Viewport(self.controller.ds_orig,
			view_type='Connection Matrix')
	def _circle_port_default(self):
		return Viewport(self.controller.ds_orig,
			view_type='Circular plot')

	#options_window = 				Instance(dialogs.InteractiveSubwindow)
	#adjmat_chooser_window = 		Instance(dialogs.InteractiveSubwindow)
	#parcellation_chooser_window =	Instance(dialogs.InteractiveSubwindow)
	#node_chooser_window =			Instance(dialogs.InteractiveSubwindow)
	#module_chooser_window = 		Instance(dialogs.InteractiveSubwindow)
	#module_customizer_window =		Instance(dialogs.InteractiveSubwindow)
	#graph_theory_window =			Instance(dialogs.InteractiveSubwindow)
	#configure_scalars_window =		Instance(dialogs.InteractiveSubwindow)
	#save_snapshot_window =			Instance(dialogs.InteractiveSubwindow)
	#make_movie_window = 			Instance(dialogs.InteractiveSubwindow)
	#really_overwrite_file_window =	Instance(dialogs.InteractiveSubwindow)
	#calculate_window =				Instance(dialogs.InteractiveSubwindow)

	options_window = 				Instance(HasTraits)
	adjmat_chooser_window = 		Instance(HasTraits)
	parcellation_chooser_window =	Instance(HasTraits)
	node_chooser_window =			Instance(HasTraits)
	module_chooser_window = 		Instance(HasTraits)
	module_customizer_window =		Instance(HasTraits)
	graph_theory_window =			Instance(HasTraits)
	configure_scalars_window =		Instance(HasTraits)
	save_snapshot_window =			Instance(HasTraits)
	make_movie_window = 			Instance(HasTraits)
	really_overwrite_file_window =	Instance(HasTraits)
	calculate_window =				Instance(HasTraits)

	#load_tractography_window
	#load_standalone_matrix_window

	select_node_button = 			Button('Choose node')
	display_all_button = 			Button('Reset Display')
	graph_theory_button = 			Button('Show statistics')
	calculate_button =				Button('Calculate stats')
	#load_module_button = 			Button('Load module')
	select_module_button = 			Button('View module')
	custom_module_button = 			Button('Custom subset')
	all_modules_button = 			Button('View all modules')
	display_scalars_button = 		Button('Show scalars')
	#load_scalars_button = 			Button('Load scalars')
	load_external_button =			Button('Load stats')
	load_adjmat_button = 			Button('Load an adjacency matrix')
	force_render_button = 			Button('Force render')
	color_legend_button = 			Button('Color legend')
	load_parcellation_button =		Button('Load a parcellation')
	options_button = 				Button('Options')
	controller_button =				Button('Manage views')
	load_track_button = 			Button('Load tractography')
	save_snapshot_button = 			Button('Take snapshot')
	make_movie_button = 			Button
	mk_movie_lbl = 					Str('Make movie')
	center_adjmat_button = 			Button('Center adjmat')
	about_button = 					Button('About')

	manage_views_button = 			Button('Manage views')

	python_shell = Dict

	traits_view = View(
		VSplit(
			HSplit(
				Item(name='mayavi_port',height=500,width=500,
					editor=InstanceEditor(view='mayavi_view'),
					show_label=False,style='custom',resizable=True,),
				Item(name='matrix_port',height=500,width=500,
					editor=InstanceEditor(view='matrix_view'),
					show_label=False,style='custom',resizable=True,),
				Group(	Item(name='select_node_button'),
						Item(name='display_all_button'),
						Item(name='color_legend_button'),
						Item(name='center_adjmat_button'),
						Spring(),
						Item(name='calculate_button'),
						Item(name='load_external_button'),
						Item(name='graph_theory_button'),
						Item(name='display_scalars_button'),
						Item(name='select_module_button'),
						Item(name='all_modules_button'),
						Item(name='custom_module_button'),
						Spring(),
						Item(name='force_render_button'),
					show_labels=False,
				)
			),
			HSplit(
				Item(name='circle_port',height=500,width=500,
					editor=InstanceEditor(view='circle_view'),
					show_label=False,style='custom',resizable=True,),
				Group(
					HSplit(
						Item(name='load_parcellation_button',),
						Item(name='load_adjmat_button',),
						Item(name='load_track_button',),
						show_labels=False,
					),
					HSplit(
						Item(name='save_snapshot_button'),
						Item(name='make_movie_button',
							editor=ButtonEditor(label_value='mk_movie_lbl')),
						Item(name='options_button',),
						Item(name='controller_button',),
						Item(name='about_button'),
						show_labels=False,
					),
					HSplit(
						Item(name='python_shell',editor=ShellEditor(),
						show_label=False),
					),
				),
			),
		),
		resizable=True,title="Connectome Visualization Utility")

	def __init__(self,sample_data=None,quiet=False,**kwargs):
		super(HasTraits,self).__init__(quiet=quiet,**kwargs)
		ctrl=self.controller=Controller(self,sample_data=sample_data)
		ds_orig=self.controller.ds_orig

		#these dialogs exist strictly in the gui and have no control item
		#they do not extend interactivesubwindow
		self.error_dialog_window=dialogs.ErrorDialogWindow()
		self.warning_dialog_window=dialogs.WarningDialogWindow()
		self.about_window=dialogs.AboutWindow()
		self.really_overwrite_file_window=dialogs.ReallyOverwriteFileWindow()

		self.options_window=dialogs.OptionsWindow(ds_orig.opts,ctrl)
		self.configure_scalars_window=dialogs.ConfigureScalarsWindow(
			ds_orig.scalar_display_settings,ctrl)

		self.calculate_window=dialogs.CalculateWindow(
			ctrl.options_db.calculate_parameters,ctrl)

		self.adjmat_chooser_window=dialogs.AdjmatChooserWindow(
			ctrl.options_db.adjmat_chooser_parameters,ctrl)
		self.parcellation_chooser_window=dialogs.ParcellationChooserWindow(
			ctrl.options_db.parcellation_chooser_parameters,ctrl)
		self.node_chooser_window=dialogs.NodeChooserWindow(
			ctrl.options_db.node_chooser_parameters,ctrl)
		self.module_chooser_window=dialogs.ModuleChooserWindow(
			ctrl.options_db.module_chooser_parameters,ctrl)
		self.module_customizer_window=dialogs.ModuleCustomizerWindow(
			ctrl.options_db.module_customizer_parameters,ctrl)
		self.graph_theory_window=dialogs.GraphTheoryWindow(
			ctrl.options_db.graph_theory_parameters,ctrl)
		self.save_snapshot_window=dialogs.SaveSnapshotWindow(
			ctrl.options_db.snapshot_parameters,ctrl)
		self.make_movie_window=dialogs.MakeMovieWindow(
			ctrl.options_db.make_movie_parameters,ctrl)

		self.panel_name = 'base_gui'

	def error_dialog(self,message):
		self.error_dialog_window.error=message
		self.error_dialog_window.edit_traits()

	def warning_dialog(self,message):
		self.warning_dialog_window.warning=message
		self.warning_dialog_window.edit_traits()

	######################################################################
	# BUTTONS AND INTERACTIONS
	######################################################################

	def _options_button_fired(self):
		self.options_window.finished=False
		self.options_window.edit_traits()

	def _load_parcellation_button_fired(self):
		self.parcellation_chooser_window.finished=False
		self.parcellation_chooser_window.edit_traits()

	@on_trait_change('parcellation_chooser_window:notify')
	def _load_parcellation_check(self):
		pcw=self.parcellation_chooser_window
		if not pcw.finished: return
		if pcw.ctl.new_dataset:
			if pcw.ctl.new_dataset_name=='':
				self.error_dialog('Must specify a dataset name!'); return
			elif pcw.ctl.new_dataset_name in self.controller.ds_instances:
				self.error_dialog('Dataset name is not unique'); return	
			else:
				ds_name = pcw.ctl.new_dataset_name
				import preprocessing
				parc_struct=preprocessing.process_parc(pcw.ctl,self)
				if parc_struct is None: return #preprocessing errored out
				
				lab_pos,labnam,srf,labv,subject_name,parc_name=parc_struct

				display = dataset.CurrentDisplay(subject_name,parc_name,'')
				ds=dataset.Dataset(ds_name,lab_pos,labnam,srf,labv,display,
					gui=self)
				self.controller.add_dataset(ds)
		else:
			import preprocessing	
			parc_struct=preprocessing.process_parc(pcw.ctl,self)
			if parc_struct is None: return #preprocessing returned an error	

			lab_pos,labnam,srf,labv,subject_name,parc_name=parc_struct
			pcw.ctl.ds_ref.load_parc(lab_pos,labnam,srf,labv,
				subject_name,parc_name)

			#find the viewports that were previously holding this scene
			#find_dataset_views returns a DatasetViewportInterface object
			#with references to the viewports (source in viewport.py)
 
			#only the viewports that are affected by nodes should be reset.
			#i.e., the 3D brain and circle plot should be set here because
			#they generated something only knowing the parcellation
			#the conn mat is *not* created yet until an adjmat is generated
			# (we could make a dummy but is there much of a reason?)
			#FIXME do make a dummy in some way so that we dont need to
			#reference the controller again in adj load

			ds_interface=self.controller.find_dataset_views(pcw.ctl.ds_ref)	

			ds_interface.mayavi_port = Viewport(pcw.ctl.ds_ref)
			ds_interface.matrix_port = Viewport(pcw.ctl.ds_ref)
			ds_interface.circle_port = Viewport(pcw.ctl.ds_ref)

	def _load_adjmat_button_fired(self):
		self.adjmat_chooser_window.finished=False
		self.adjmat_chooser_window.edit_traits()

	@on_trait_change('adjmat_chooser_window:notify')
	def _load_adjmat_check(self):
		acw=self.adjmat_chooser_window
		if not acw.finished: return

		import preprocessing as pp
		adj_struct = pp.process_adj(acw.ctl,self)
		if adj_struct is None: return #preprocessing returned an error 
	
		adj,soft_max_edges,adjmat_filename = adj_struct
		acw.ctl.ds_ref.load_adj(adj,soft_max_edges,adjmat_filename)

	def _display_scalars_button_fired(self):
		#more checking required.  should make sure scalars exist first.
		self.configure_scalars_window.finished=False
		self.configure_scalars_window.edit_traits()

	def _select_node_button_fired(self):
		self.node_chooser_window.finished=False
		self.node_chooser_window.edit_traits()

	@on_trait_change('node_chooser_window:notify')
	def _select_node_check(self):
		ncw=self.node_chooser_window
		if not ncw.finished: return
		ncw.ctl.ds_ref.display_node(ncw.ctl.cur_node)

	def _calculate_button_fired(self):
		cw=self.calculate_window
		cw.finished=False
		cw.edit_traits()

	@on_trait_change('calculate_window:notify')
	def _calculation_check(self):
		cw=self.calculate_window
		if not cw.finished: return

		if cw.ctl.thresh_type=='abs':
			thres=cw.ctl.athresh
		elif cw.ctl.thresh_type=='prop':
			thres=cw.ctl.ds_ref.adjdat[
				int(round(cw.ctl.pthresh*cw.ctl.ds_ref.nr_edges-1))]

		if cw.ctl.calculation_type=='modules':
			cw.ctl.ds_ref.calculate_modules(thres)
			cw.ctl.ds_ref.display_multi_module()
		elif cw.ctl.calculation_type=='statistics':
			cw.ctl.ds_ref.calculate_graph_stats(thres)

	def _select_module_button_fired(self):
		self.module_chooser_window.finished=False
		self.module_chooser_window.edit_traits()

	@on_trait_change('module_chooser_window:notify')
	def _select_module_check(self):
		mcw=self.module_chooser_window
		if not mcw.finished or mcw.ctl.cur_mod==-1: return
		else: mcw.ctl.ds_ref.display_module(mcw.ctl.cur_mod)

	#def _all_modules_button_fired(self):
		#what dataset does this refer to?  maybe better to make the modules be
		#recalculated as a way to access this mode?

		#this, or else give control of the mode to the user in options.  if the user
		#resets the mode, call ds_ref.draw()

	def _custom_module_button_fired(self):
		self.module_customizer_window.finished=False
		self.module_customizer_window.edit_traits()

	@on_trait_change('module_customizer_window:notify')
	def _module_customizer_check(self):
		mcw=self.module_customizer_window
		if not mcw.finished: return
		try: mcw.ctl._index_convert()
		except ValueError: 
			self.error_dialog('Internal error: bad index conversion')
			return
		mcw.ctl.ds_ref.custom_module=mcw.ctl.return_module
		mcw.ctl.ds_ref.display_module('custom')

	def _graph_theory_button_fired(self):
		#more checking required. should make sure stats exist first
		self.graph_theory_window.finished=False
		self.graph_theory_window.edit_traits()

	def _save_snapshot_button_fired(self):
		self.save_snapshot_window.finished=False
		self.save_snapshot_window.edit_traits()
	
	@on_trait_change('save_snapshot_window:notify')
	def _save_snapshot_check(self):
		ssw=self.save_snapshot_window
		if not ssw.finished: return
		elif not ssw.ctl.savefile: 
			self.error_dialog('You must specify a filename to save to')
			return
		else:
			save_continuation = ssw.ctl.ds_ref.snapshot(ssw.ctl)
			if not os.path.exists(os.path.dirname(ssw.ctl.savefile)):
				self.error_dialog('Bad path specified. Check for typo?')
			elif not os.path.exists(ssw.ctl.savefile):
				save_continuation()
			else:	
				rofw = self.really_overwrite_file_window
				rofw.save_continuation = save_continuation
				rofw.finished=False
				rofw.edit_traits()

	@on_trait_change('really_overwrite_file_window:notify')
	def _really_overwrite_file_check(self):
		rofw=self.really_overwrite_file_window
		#if the user clicks ok, call the save continuation
		if rofw.finished: rofw.save_continuation()
			#otherwise, dont do anything

	def _make_movie_button_fired(self):
		self.make_movie_window.finished=False
		self.make_movie_window.edit_traits()

	def _controller_button_fired(self):
		self.controller.viewport_manager.edit_traits()

	def _about_button_fired(self):
		self.about_window.edit_traits()
