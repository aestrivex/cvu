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

from traits.api import (HasTraits,Any,List,Str,Enum,Dict,Instance,Either,
	on_trait_change)
from traitsui.api import Handler
from options_struct import OptionsDatabase
from utils import DatasetMetadataElement,CVUError
from viewport import ViewPanel

class ViewportManagerEntry(HasTraits):
	window_name=Str
	window_group=Enum('1','2')
	all_datasets=List	

class ViewportManager(Handler):
	#TODO make this a dialog
	from traitsui.api import (Item,View,ObjectColumn,TableEditor,RangeEditor,
		CheckListEditor,OKButton)

	ctl=Any

	def __init__(self,ctl,**kwargs):
		super(Handler,self).__init__(**kwargs)
		self.ctl = ctl

	traits_view=View(
		Item(name='viewports',object='object.ctl',
			editor=TableEditor(columns= [
				ObjectColumn(label='Window',#editor=TextEditor(),
					name='window_name',style='readonly'),
				ObjectColumn(label='Dataset',
					editor=CheckListEditor(name='all_datasets'),style='simple',
					name='_current_dataset_list',editable=True),
 			]),
			show_label=False,height=300,width=600, 
		),
		kind='nonmodal',buttons=[OKButton],
		title='If it were up to me it would all be in Swahili',
	)

class DatasetUIMetadata(DatasetMetadataElement):
	panel = Str				
	group = Either(1,2)
	ds_name = Str

	def __init__(self,controller,panel,group,name,**kwargs):
		super(DatasetUIMetadata,self).__init__(controller,**kwargs)
		self.panel=panel
		self.group=group
		self.ds_name=name

class Controller(HasTraits):
	datasets=List				#list of dataset instances
	gui=Any						#handle to the gui
	options_db=Instance(OptionsDatabase)

	dataset_metadatae=List
	viewport_windows=Dict 	#map of strings (panel names) to ViewPanel objects

	viewport_manager=Instance(ViewportManager)

	def __init__(self,gui,sample_data=None):
		super(Controller,self).__init__()
		self.gui=gui
		if sample_data is not None:
			self.datasets=[sample_data]

		self.options_db=OptionsDatabase(sample_data)
		self.viewport_manager=ViewportManager(self)

		self.viewport_windows={'base_gui':self.gui}
		self.dataset_metadatae=[
			DatasetUIMetadata(self,'base_gui',1,sample_data.name)]

	#listen to the GUI for changes in the current dataset and set the control
	#accordingly for the unstable windows
	@on_trait_change('gui:options_window:current_dataset')
	def options_window_ctl_listener(self):
		self.gui.options_window.ctl=self.gui.options_window.current_dataset.opts
	@on_trait_change('gui:configure_scalars_window:current_dataset')
	def configure_scalars_window_ctl_listener(self):
		csw=self.configure_scalars_window
		csw.ctl=csw.current_dataset.scalar_display_settings

	##########################################################
	#viewport allocation
	def add_dataset(self,ds,panel=None,group=None):
		'''Given a dataset, add it to the controller.  If panel and group
		   are specified, add it to that panel, otherwise any panel will do'''
		self.datasets.append(ds)

		if panel is None and group is None:
			panel_ref = self._get_any_panel()		
			panel = panel_ref.panel_name
			group = 2 if panel_ref.is_full(group=1) else 1
		elif group is not None: 
			raise CVUError('Cannot specify group without panel')
		elif panel is not None:
			panel_ref = self.get_named_panel(panel)
			if panel_ref.is_full():
				raise CVUError('That panel is full')
			group = 2 if panel_ref.is_full(group=1) else 1
		else:
			panel_ref = self.get_named_panel(panel)

		panel_ref.populate(ds,group=group)	#group can be none, doesnt matter
		group_spec = DatasetUIMetadata(self,panel,group,ds.name)
		self.dataset_metadatae.append(group_spec)	

		self.show_panel(panel_ref)

	def show_panel(self,panel):
		panel.edit_traits(panel.produce_view())

	def rebuild_panel(self,panel):
		#find the associated dataset and reset its DataViews		
		#have the panel dispose of itself if necessary
		#then show the panel
		pass

	def find_dataset_views(self,ds):
		'''Given a dataset, return the three viewports that refer to it'''
		for ds_meta in self.dataset_metadatae:
			if ds_meta.ds_name == ds.name:	
				panel=self.viewport_windows[ds_meta.panel]
				from viewport import DatasetViewportInterface
				#if panel is base gui, return it
				if isinstance(panel,DatasetViewportInterface): layout_obj=panel
				#otherwise, return its group
				elif ds_meta.group==1: layout_obj = panel.group_1
				elif ds_meta.group==2: layout_obj = panel.group_2
				else: raise CVUError("Inconsistent metadata")
				return layout_obj
			else: continue

	def remove_dataset(self,name):
		for ds in self.datasets:
			if ds.name==name: self.datasets.remove(ds)
			self.datasets.remove(ds)
		#remove the metadata elements associated with this dataset
			#(but dont do anything to reload the viewport manager right now)
		for ds_meta in self.dataset_metadatae:
			if ds_meta.ds_name==name: self.dataset_metadatae.remove(ds_meta)
		#remove the panel if appropriate

	#internal methods for panel manipulation
	def _get_named_panel(self,panel_name):
		try:
			return self.viewport_windows[panel_name]
		except KeyError as e:
			raise CVUError('No such panel')

	def _get_any_panel(self):
		for panel in self.viewport_windows:
			if panel=='base_gui': continue
			else:
				p=self.viewport_windows[panel]
				if not p.is_full(): return p

		#if no available panel was found, then make a new one
		return self._create_new_panel()

	#panel creation
	def __ctr_generate():
		i=0
		while True:
			i+=1
			yield i
	__ctr_generator = Any(__ctr_generate())
	def _panel_counter(self):
		return self.__ctr_generator.next()

	def _create_new_panel(self):
		name='Extra Views %i'%self._panel_counter()
		panel = ViewPanel(panel_name=name)
		self.viewport_windows[name]=panel
		return panel

	def _destroy_panel(self,name):
		del self.viewport_windows[name]
