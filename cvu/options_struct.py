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

from traits.api import (HasTraits,Instance,Int,Range,Bool,Float,Property,Enum,
	Str,List,Directory,Any,File,on_trait_change,cached_property)
from color_map import CustomColormap
import os

class OptionsDatabase(HasTraits):
	def __init__(self,init_ds,**kwargs):
		super(OptionsDatabase,self).__init__(**kwargs)
		self.parcellation_chooser_parameters=(
			ParcellationChooserParameters(init_ds))
		self.adjmat_chooser_parameters=(
			AdjmatChooserParameters(init_ds))
		self.general_matrix_chooser_parameters=(
			GeneralMatrixChooserParameters(init_ds))
		self.node_chooser_parameters=(
			NodeChooserParameters(init_ds))
		self.calculate_parameters=(
			CalculateParameters(init_ds))
		self.module_chooser_parameters=(
			ModuleChooserParameters(init_ds))
		self.module_customizer_parameters=(
			ModuleCustomizerParameters(init_ds))
		self.snapshot_parameters=(
			SnapshotParameters(init_ds))
		self.make_movie_parameters=(
			MakeMovieParameters(init_ds))	
		self.graph_theory_parameters=(
			GraphTheoryParameters(init_ds))

#GUI INTERACTION PARAMETER CLASSES

#the idea is to separate GUI construction and the location of the data referred
#to by GUI editors.  The idea of having data specified directly in GUI window
#makes it difficult to appropriately designate that data to the proper target
#dataset.  For some targets this is not an issue (e.g., AboutWindow) but having
#the data in the GUI component itself is still a bit kludgy (even if traits
#expects this).

#So, I'll just have everything out in an OptionsStructure whether it really
#needs it or not, except for the AboutWindow which literally has no data.

	#######################################################################
	# OPTIONS STRUCTURES
	#######################################################################

#having the reference to the dataset is not needed by most of the structs,
#but having the bidirectional access is very helpful to avoid copying data in
#a number of cases
class DatasetReferenceOptionsStructure(HasTraits):
	ds_ref=Any					#symbolic reference to a dataset

	def __init__(self,ds_ref,**kwargs):
		super(DatasetReferenceOptionsStructure,self).__init__(**kwargs)
		self.ds_ref=ds_ref

class DisplayOptions(DatasetReferenceOptionsStructure):
	#THE DISPLAY OPTIONS SHOULD BE DISPLAYED IN NUMEROUS TABS
	# **MISCELLANEOUS, **COLORMAPS, **GRAPH STATISTICS
	#* should be moved to a non-display-related tab if there are enough items
	#miscellaneous tab
	surface_visibility = Range(0.0,1.0,.15)
	circ_size = Range(7,20,10,mode='spinner')
	conns_colorbar=Bool(False)
	scalar_colorbar=Bool(False)
	pthresh = Range(0.,1.,.95)	
	athresh = Float					
	thresh_type = Enum('prop','abs')
	prune_modules = Bool(True)
	show_floating_text = Bool(True)
	module_view_style = Enum('intramodular','intermodular','both')
	render_style=Enum('glass','cracked_glass','contours','wireframe','speckled')
	interhemi_conns_on = Bool(True)
	lh_conns_on = Bool(True)
	rh_conns_on = Bool(True)
	lh_nodes_on = Bool(True)
	rh_nodes_on = Bool(True)
	lh_surfs_on = Bool(True)
	rh_surfs_on = Bool(True)
	conns_width = Float(2.)
	conns_colors_on = Bool(True)

	#colormap tab
	default_map=	Instance(CustomColormap,CustomColormap('default'))
	scalar_map=		Instance(CustomColormap,CustomColormap('scalar'))
	activation_map=	Instance(CustomColormap,CustomColormap('activation'))
	connmat_map=	Instance(CustomColormap,CustomColormap('connmat'))

	#graph statistics tab
	intermediate_graphopts_list=List(Str)

	def _intermediate_graphopts_list_default(self):
		return ['global efficiency', 'clustering coefficient']

class ScalarDisplaySettings(DatasetReferenceOptionsStructure):
	node_color=Str
	surf_color=Str
	node_size=Str
	circle=Str
	connmat=Str
	scalar_sets=Property(List(Str))
	def _get_scalar_sets(self):
		return self.ds_ref.node_scalars.keys()

class ParcellationChooserParameters(DatasetReferenceOptionsStructure):
	new_dataset=Bool(False)
	new_dataset_name=Str
	subjects_dir=Directory('./')
	subject=Str('fsavg5')
	labelnames_file=File
	parcellation_name=Str
	surface_type=Str('pial')

class TractographyChooserParameters(DatasetReferenceOptionsStructure):
	NotImplemented

class AdjmatChooserParameters(DatasetReferenceOptionsStructure):
	adjmat=File	
	adjmat_order=File
	max_edges=Int
	field_name=Str
	ignore_deletes=Bool
	require_ls=List(Str)

class GeneralMatrixChooserParameters(DatasetReferenceOptionsStructure):
	mat=File
	mat_order=File
	field_name=Str
	ignore_deletes=Bool
	whichkind=Enum('modules','scalars')

	#TODO this is a bit of a dumb strategy.  It would be fine if
		#a) it reset occasionally
		#b) it represented that this uses scalars and modules alike
	measure_nr=Int(1)
	measure_name=Property(Str)
	def _get_general_data_name(self):
		return 'statistic%i'%self.dataset_nr

	def _dataset_plusplus(self):
		self.measure_nr+=1

class NodeChooserParameters(DatasetReferenceOptionsStructure):
	cur_node=Int(-1)
	node_list=Property(List(Str))
	def _get_node_list(self):
		return self.ds_ref.labnam

class CalculateParameters(DatasetReferenceOptionsStructure):
	calculation_type=Enum('modules','statistics')
	athresh=Float
	pthresh=Range(0.,1.,.95)
	thresh_type=Enum('prop','abs')

class ModuleChooserParameters(DatasetReferenceOptionsStructure):
	cur_mod=Int(-1)
	module_list=Property(List(Str),depends_on='ds_ref.modules')
	@cached_property
	def _get_module_list(self):
		return ['Module %i'%i for i,m in enumerate(self.ds_ref.modules)]

class ModuleCustomizerParameters(DatasetReferenceOptionsStructure):
	initial_node_list=Property(List(Str))
	def _get_initial_node_list(self):
		return self.ds_ref.labnam
	intermediate_node_list=List(Str)
	return_module=List(Int)

	#index_convert may return a ValueError, it should be contained in try/except
	def _index_convert(self):
		self.return_module=[self.initial_node_list.index(i)
			for i in self.intermediate_node_list]

class SnapshotParameters(DatasetReferenceOptionsStructure):
	savefile=Str(os.environ['HOME'])
	whichplot=Enum('3D brain','connection matrix','circle plot')
	dpi=Int(300)

class MakeMovieParameters(DatasetReferenceOptionsStructure):
	savefile=Str(os.environ['HOME'])
	framerate=Int(20)
	bitrate=Int(4000)
	samplerate=Int(8)
	anim_style=Bool(True)
	anim_rate=Int(8)

class GraphTheoryParameters(DatasetReferenceOptionsStructure):
	from graph import StatisticsDisplay
	
	graph_stats=List(StatisticsDisplay)	#this is a *display* list
		#each dataset has its own dictionary of stats from which this is created
	current_stat=Instance(StatisticsDisplay)
	scalar_savename=Str
	
	#the params is not populated until the graph theory window is 
	#requested for the first time.  populate is called as a direct GUI interact
	def populate(self):
		if len(self.ds_ref.graph_stats)==0:
			self.error_dialog("No graph stats exist yet")
		self.graph_stats=list()
		for k,v in self.ds_ref.graph_stats.iteritems():
			self.graph_stats.append(StatisticsDisplay(k,v,self.ds_ref.labnam))

	def _current_stat_changed(self):
		self.scalar_savename=self.current_stat.name

	@on_trait_change('gui:graph_theory_window:SaveToScalarEvent')
	def _proc_save_to_scalar_event(self):
		self.ds_ref.save_scalar(self.scalar_savename,self.current_stat)

	@on_trait_change('gui:graph_theory_window:RecalculateEvent')
	def _proc_recalculate_event(self):
		self.ds_ref.calculate_graph_stats()
		self._populate()
