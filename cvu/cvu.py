# (C) Roan LaPlante 2013 rlaplant@nmr.mgh.harvard.edu

quiet=True
import cvu_utils as util
if __name__=="__main__":
	import sys
	args=util.cli_args(sys.argv[1:])
	quiet=args['quiet']
if not quiet:
	print "Importing libraries"
import numpy as np
from mayavi import mlab;
import os; 
from traits.api import *; from traitsui.api import *
from mayavi.core.ui.api import MlabSceneModel,MayaviScene,SceneEditor
from chaco.api import Plot,ArrayPlotData,YlOrRd,RdYlBu,PlotGraphicsContext; 
from chaco.api import reverse,center
from enable.component_editor import ComponentEditor
from chaco.tools.api import ZoomTool,PanTool
from enable.api import Pointer
from matplotlib.figure import Figure; from pylab import get_cmap
import circle_plot as circ; import mpleditor; import dialogs;
import color_legend; import color_axis
if __name__=="__main__":
	print "All libraries loaded"

class CvuPlaceholder(HasTraits):
	conn_mat = Instance(Plot)

class ConnmatPanClickTool(PanTool):
	cvu=Instance(CvuPlaceholder)

	event_state=Enum("normal","deciding","panning")
	drag_pointer=Pointer("arrow")

	def __init__(self,holder,*args,**kwargs):
		super(PanTool,self).__init__(component=holder.conn_mat,**kwargs)
		self.cvu=holder	
		
	def normal_left_down(self,event):
		self.event_state='deciding'
		self._original_xy=(event.x,event.y)
		return

	def normal_right_down(self,event):
		self.cvu.display_all()

	# the click is a node selection
	def deciding_left_up(self,event):
		self.event_state='normal'
		x,y=self.cvu.conn_mat.map_data((event.x,event.y))
		self.cvu.display_node(int(np.floor(y)))
		return

	# the click is a pan
	# the only thing of real interest in _start_pan() is change to the panning state
	def deciding_mouse_move(self,event):
		self.event_state='panning'
		return self.panning_mouse_move(event)

class Cvu(CvuPlaceholder):
	scene = Instance(MlabSceneModel, ())
	circ_fig = Instance(Figure,())

	#stateful traits
	pthresh = Range(0.0,1.0,.95)
	nthresh = Float
	thresh_type = Enum('prop','num')
	reset_thresh = Method

#	node_scalars=Instance(np.ndarray)

	#buttons
	select_node_button = Button('Choose node')
	all_node_button = Button('Show all')
	calc_mod_button = Button('Calc modules')
	load_mod_button = Button('Load premade')
	select_mod_button = Button('View module')
	custom_mod_button = Button('Custom module')
	display_scalars_button = Button('Show scalars')
	load_scalars_button = Button('Load scalars')
	load_adjmat_button = Button('Load an adjacency matrix')
	draw_stuff_button = Button('Force render')
	color_legend_button = Button('Color legend')
	load_parc_button=Button('Load a parcellation')
	options_button=Button('Options')
	mayavi_snapshot_button=Button('3D snapshot')
	chaco_snapshot_button=Button('Adjmat snapshot')
	circ_snapshot_button = Button('Circle snapshot')
	center_adjmat_button = Button('Center adjmat')

	#various subwindows
	parc_chooser_window = Instance(HasTraits)
	adjmat_chooser_window = Instance(HasTraits)
	load_standalone_matrix_window = Instance(HasTraits)
	node_chooser_window = Instance(HasTraits)
	module_chooser_window = Instance(HasTraits)
	module_customizer_window = Instance(HasTraits)
	save_snapshot_window = Instance(HasTraits)
	really_overwrite_file_window = Instance(HasTraits)
	error_dialog_window = Instance(HasTraits)
	color_legend_window = Instance(HasTraits)
	opts = Instance(HasTraits)
	#Must declare each of the subwindows specifically as a trait so its 
	#attributes can be listened for as traits with decorators.

	#current display information
	cur_display_title = Str('CURRENT DISPLAY')
	cur_display_brain = Str
	cur_display_parc = Str
	cur_display_mat = Str

	python_shell = Dict

	## HAVE TRAITSUI ORGANIZE THE GUI ##
	traits_view = View(
		VSplit(
			HSplit(
				Item(name='cur_display_title',show_label=False),
				Item(name='cur_display_brain',label='subject',
					height=21,width=100),
				#Spring(),
				Item(name='cur_display_parc',label='parcellation'
					,height=21,width=100),
				#Spring(),
				Item(name='cur_display_mat',label='matrix',
					height=21,width=500),
				show_labels=True,style='readonly'),
			HSplit(
				Item(name='scene',
					editor=SceneEditor(scene_class=MayaviScene),
					height=500,width=500,show_label=False,resizable=True),
				Item(name='conn_mat',
					editor=ComponentEditor(),
					show_label=False,height=450,width=450,resizable=True),
				Group(	Item(name='select_node_button'),
						Item(name='all_node_button'),
						Item(name='color_legend_button'),
						Item(name='center_adjmat_button'),
						Spring(),
						Item(name='calc_mod_button'),
						Item(name='load_mod_button'),
						Item(name='select_mod_button'),
						Item(name='custom_mod_button'),
						Spring(),
						Item(name='load_scalars_button'),
						Item(name='display_scalars_button'),
						Spring(),
						Item(name='draw_stuff_button'),
					show_labels=False,
				)
			),
			HSplit(
				Item(name='circ_fig',
					editor=mpleditor.MPLFigureEditor(),
					height=500,width=500,show_label=False,resizable=True),
				Group(
				HSplit(
						Item(name='load_parc_button',),
						Item(name='load_adjmat_button',),
						Item(name='options_button',),
						show_labels=False,
					),
					HSplit(
						Item(name='mayavi_snapshot_button'),
						Item(name='chaco_snapshot_button'),
						Item(name='circ_snapshot_button'),
						show_labels=False,
					),
					HSplit(
					Item(name='pthresh'),
						Item(name='nthresh',editor=DefaultOverride(
							auto_set=False,enter_set=True)),
						Item(name='thresh_type')
					),
					HSplit(
						Item(name='python_shell',editor=ShellEditor(),
						show_label=False),
					),
				),
			),
		),
		resizable=True,title="Connectome Visualization Utility")

	## INITIALIZE THE CVU OBJECT ##
	# args are in order pos,adj,names,srfinfo,datainfo
	def __init__(self,args):
		super(Cvu,self).__init__()
		## UNPACK THE ARG TUPLE
		self.lab_pos=args[0]
		self.adj_nulldiag=args[1]
		self.labnam=args[2]
		self.adjlabfile=args[3]
		self.srf=args[4]
		self.dataloc=args[5][0]
		self.modality=args[5][1]
		self.partitiontype=args[5][2]
		self.soft_max_edges=args[5][3]

		## SET UP ALL THE DATA TO FEED TO MLAB ##
		self.nr_labels=len(self.lab_pos)

		self.cur_display_brain=args[5][4]
		self.cur_display_parc=args[5][5]
		self.cur_display_mat=args[5][6]
	
		#self.lab_pos *= 1000
		#print np.shape(self.lab_pos)
		self.opts=dialogs.OptionsWindow()
		self.adjmat_chooser_window=dialogs.AdjmatChooserWindow()
		self.parc_chooser_window=dialogs.ParcellationChooserWindow()
		self.load_standalone_matrix_window=dialogs.LoadGeneralMatrixWindow()
		self.node_chooser_window=dialogs.NodeChooserWindow()
		self.module_chooser_window=dialogs.ModuleChooserWindow()
		self.module_customizer_window=dialogs.ModuleCustomizerWindow()
		self.save_snapshot_window=dialogs.SaveSnapshotWindow()
		self.really_overwrite_file_window=dialogs.ReallyOverwriteFileWindow()
		self.error_dialog_window=dialogs.ErrorDialogWindow()
		self.color_legend_window=color_legend.ColorLegendWindow()

		self.node_chooser_window.node_list=self.labnam
		self.module_customizer_window.initial_node_list=self.labnam

	#default initializations
	def _reset_thresh_default(self):
		return self.prop_thresh

	@on_trait_change('scene.activated')	
	def setup(self):
		## SET UP DATA ##
		self.pos_helper_gen()
		self.adj_nulldiag=util.flip_adj_ord(self.adj_nulldiag,self.adjlabfile,
			self.labnam)
		self.adj_helper_gen()

		self.modules=None
		self.cur_module=None

		## SET UP COLORS AND COLORMAPS ##
		self.yellow_map=get_cmap('YlOrRd')
		self.cool_map=get_cmap('cool')
		self.bluegreen_map=get_cmap('BuGn')

		## SET UP ALL THE MLAB VARIABLES FOR THE SCENE ##	
		self.fig = mlab.figure(bgcolor=(.36,.34,.30),
			figure=self.scene.mayavi_scene)
		self.surfs_gen()
		self.nodes_gen()
		self.vectors_gen()

		## SET UP THE CIRCLE PLOT ##
		self.circ_fig_gen()

		## SET UP CHACO VARIABLES ##
		self.chaco_gen()
		self.color_legend_gen()

		## SET UP THE CALLBACKS (for mayavi and matplotlib) ##
		pck = self.fig.on_mouse_pick(self.leftpick_callback)
		pck.tolerance = .02
		self.fig.on_mouse_pick(self.rightpick_callback,button='Right')

		self.display_all()

	## VISUALIZATION GENERATOR FUNCTIONS ##
	def init_thres_gen(self):
		self.thresval = float(sorted(self.adjdat)\
			[int(round(self.pthresh*self.nr_edges))-1])
		if not quiet:
			print "Initial threshold: "+str(self.pthresh)

	def pos_helper_gen(self):
		self.nr_edges = self.nr_labels*(self.nr_labels-1)/2
		self.starts = np.zeros((self.nr_edges,3),dtype=float)
		self.vecs = np.zeros((self.nr_edges,3),dtype=float)
		self.edges = np.zeros((self.nr_edges,2),dtype=int)
		i=0
		for r2 in xrange(0,self.nr_labels,1):
			for r1 in xrange(0,r2,1):
				self.starts[i,:] = self.lab_pos[r1]
				self.vecs[i,:] = self.lab_pos[r2]-self.lab_pos[r1]
				self.edges[i,0],self.edges[i,1] = r1,r2
				i+=1
	
	#precondition: adj_helper_gen() must be run after pos_helper_gen()
	def adj_helper_gen(self):
		self.nr_edges = self.nr_labels*(self.nr_labels-1)/2
		self.adjdat = np.zeros((self.nr_edges,1),dtype=float)
		self.interhemi = np.zeros((self.nr_edges,1),dtype=bool)
		self.left = np.zeros((self.nr_edges,1),dtype=bool)
		self.right = np.zeros((self.nr_edges,1),dtype=bool)
		self.masked = np.zeros((self.nr_edges,1),dtype=bool)
		i=0
		for r2 in xrange(0,self.nr_labels,1):
			self.adj_nulldiag[r2][r2]=0
			for r1 in xrange(0,r2,1):
				self.adjdat[i] = self.adj_nulldiag[r1][r2]
				self.interhemi[i] = self.labnam[r1][0] != self.labnam[r2][0]
				self.left[i] = self.labnam[r1][0]==self.labnam[r2][0]=='l'
				self.right[i] = self.labnam[r1][0]==self.labnam[r2][0]=='r'
				i+=1
		self.adj_thresdiag=self.adj_nulldiag.copy()
		self.adj_thresdiag[np.nonzero(self.adj_thresdiag==0)]=\
			np.min(self.adj_thresdiag[np.nonzero(self.adj_thresdiag)])

		#remove all but the soft_max_edges largest connections
		if self.nr_edges > self.soft_max_edges:
			cutoff = sorted(self.adjdat)[self.nr_edges-self.soft_max_edges-1]
			zi = np.nonzero(self.adjdat>=cutoff)
			# if way way too many edges remain, make it a hard max
			# this happens in DTI data which is very sparse, the cutoff is 0
			if len(zi[0])>2*self.soft_max_edges:
				zi=np.nonzero(self.adjdat>cutoff)

			self.starts=self.starts[zi[0],:]
			self.vecs=self.vecs[zi[0],:]
			self.edges=self.edges[zi[0],:]
			self.adjdat=self.adjdat[zi[0]]
			self.interhemi=self.interhemi[zi[0]]
			
			self.nr_edges=len(self.adjdat)
		if not quiet:
			print str(self.nr_edges)+" total connections"
	# this one is intended only for displaying individuals other than fsaverage
	# not necessary for now
	def surfs_clear(self):
		try:
			self.syrf_lh.remove()
			self.syrf_rh.remove()
		except ValueError:
			pass

	def surfs_gen(self):
		self.syrf_lh = mlab.triangular_mesh(self.srf[0][:,0],self.srf[0][:,1],
			self.srf[0][:,2],self.srf[1],opacity=self.opts.surface_visibility,
			color=(.82,.82,.82),name='syrfl')
		self.syrf_rh = mlab.triangular_mesh(self.srf[2][:,0],self.srf[2][:,1],
			self.srf[2][:,2],self.srf[3],opacity=self.opts.surface_visibility,
			color=(.82,.82,.82),name='syrfr')
		self.syrf_lh.actor.actor.pickable=0
		self.syrf_rh.actor.actor.pickable=0
		#some colors
		#(.4,.75,0) #DARKISH GREEN
		#(.82,1,.82) #LIGHTER GREEN
		#(.82,.82,.82) #GRAY

	def nodes_clear(self):
		try:
			self.nodesource.remove()
			self.txt.remove()
		except ValueError:
			pass

	def nodes_gen(self):
		self.nodesource = mlab.pipeline.scalar_scatter(self.lab_pos[:,0],
			self.lab_pos[:,1],self.lab_pos[:,2],name='noddy')
		self.nodes = mlab.pipeline.glyph(self.nodesource,scale_mode='none',
			scale_factor=3.0,name='noddynod',mode='sphere',colormap='cool')
		self.nodes.glyph.color_mode='color_by_scalar'
		self.txt = mlab.text3d(0,0,0,'',scale=4.0,color=(.8,.6,.98,))
		self.txt.position=(0,0,83)
		self.txt.actor.actor.pickable=0
		self.reset_node_color_mayavi()

	def vectors_clear(self):
		try:
			self.vectorsrc.remove()
		except ValueError:
			pass

	def vectors_gen(self):
		self.vectorsrc = mlab.pipeline.vector_scatter(self.starts[:,0],
			self.starts[:,1],self.starts[:,2],self.vecs[:,0],self.vecs[:,1],
			self.vecs[:,2],name='connsrc')
		self.vectorsrc.mlab_source.dataset.point_data.scalars = self.adjdat 
		self.vectorsrc.mlab_source.dataset.point_data.scalars.name='edgekey'
		self.vectorsrc.outputs[0].update()
		self.init_thres_gen()
		self.thres = mlab.pipeline.threshold(self.vectorsrc,name='thresh',
			low=self.thresval)
		self.thres.auto_reset_lower=False
		self.thres.auto_reset_upper=False
		self.myvectors = mlab.pipeline.vectors(self.thres,colormap='YlOrRd',
			name='cons',scale_mode='vector',transparent=False)
		self.myvectors.glyph.glyph_source.glyph_source.glyph_type='dash'
		self.myvectors.glyph.glyph.clamping=False
		self.myvectors.glyph.color_mode='color_by_scalar'
		self.myvectors.actor.property.opacity=.3
		self.myvectors.actor.actor.pickable=0

	def chaco_clear(self):
		self.conn_mat.data.set_data("imagedata",np.tile(0,(self.nr_labels,
			self.nr_labels)))
		
	def chaco_gen(self):
		# set the diagonal of the adjmat to lower threshold rather than 0
		# otherwise the color scheme is a mess for non-sparse matrices
		#z_adjmat = (self.adj_thresdiag-np.mean(self.adj_thresdiag))/np.std(self.adj_thresdiag)
		#l_adjmat = np.log(self.adj_thresdiag/(1-self.adj_thresdiag))
 		#print np.where(np.isnan(l_adjmat))
		#l_adjmat[np.where(np.isnan(l_adjmat))]=0
		#print np.where(np.isnan(l_adjmat))
		self.conn_mat = Plot(ArrayPlotData(imagedata=self.adj_thresdiag))
		#centerpoint=np.mean(self.adj_thresdiag)/2+np.max(self.adj_thresdiag)/4+\
		#	np.min(self.adj_thresdiag)/4
		self.conn_mat.img_plot("imagedata",name='conmatplot',
			colormap=reverse(RdYlBu))
		self.conn_mat.tools.append(ZoomTool(self.conn_mat))
		self.conn_mat.tools.append(ConnmatPanClickTool(self,self.conn_mat))
		self.xa=color_axis.ColorfulAxis(self.conn_mat,self.node_colors,'x')
		self.ya=color_axis.ColorfulAxis(self.conn_mat,self.node_colors,'y')
		self.conn_mat.underlays=[self.xa,self.ya]

	def circ_clear(self):
		self.circ_fig.clf()
		self.circ_fig.canvas.draw()

	# The figure parameter allows figure reuse. At startup, it should be None,
	# but if the user changes the data the existing figure should be preserved
	def circ_fig_gen(self,figure=None):
		fig_holdr,self.sorted_edges,self.sorted_adjdat,\
			self.node_colors,self.group_labels,self.group_colors=\
			circ.plot_connectivity_circle2(
			np.reshape(self.adjdat,(self.nr_edges,)),self.labnam,
			indices=self.edges.T,colormap="YlOrRd",fig=figure,
			n_lines=self.soft_max_edges)
		if figure==None or True:
			self.circ_fig=fig_holdr
		self.circ_data = self.circ_fig.get_axes()[0].patches
		self.reset_node_color_circ()

	def color_legend_gen(self):
		def create_entry(zipped):
			label,color=zipped
			return color_legend.LegendEntry(metaregion=label,col=color)
		self.color_legend_window.legend=\
			map(create_entry,zip(self.group_labels,self.group_colors))

	## FUNCTIONS FOR LOADING NEW DATA ##
	def load_new_parcellation(self):
		try:
			pcw=self.parc_chooser_window
			labnam,ign = util.read_parcellation_textfile(pcw.labelnames_f)
			labv = util.loadannot(pcw.parcellation_name,pcw.SUBJECT,
				pcw.SUBJECTS_DIR)
			self.lab_pos = util.calcparc(labv,labnam,quiet=quiet,
				parcname=pcw.parcellation_name)
			self.cur_display_brain=pcw.SUBJECT
			self.cur_display_parc=pcw.parcellation_name
			self.cur_display_mat=''
		except IOError as e:
			self.error_dialog(str(e))
			return
		self.labnam=labnam
		self.node_chooser_window.node_list=labnam
		self.module_customizer_window.initial_node_list=labnam
		self.nr_labels=len(self.labnam)
		self.pos_helper_gen()
		print "Parcellation %s loaded successfully" % pcw.parcellation_name
		self.surfs_clear()
		self.nodes_clear()
		self.vectors_clear()
		self.chaco_clear()
		self.circ_clear()
		self.nodes_gen()
		self.surfs_gen()
	
	def load_new_surfaces(self):
		pass

	def load_new_adjmat(self):
		acw=self.adjmat_chooser_window
		try:
			adj=util.loadmat(acw.adjmat,field=acw.field_name)
			if acw.adjmat_order:
				self.adjlabfile=acw.adjmat_order
				adj=util.flip_adj_ord(adj,self.adjlabfile,self.labnam,
					ign_dels=acw.ignore_deletes)
			if acw.max_edges>0:
				self.soft_max_edges=acw.max_edges
			self.cur_display_mat=acw.adjmat
		except (util.CVUError,IOError) as e:
			self.error_dialog(str(e))
			return
		except (ValueError,IndexError) as e:
			self.error_dialog("Mismatched channels: %s" % str(e))
			raise
			#return
		except KeyError as e:
			self.error_dialog("Field not found: %s" % str(e))
			return
		if len(adj) != self.nr_labels:
			self.error_dialog('The adjmat specified is of size %i and the '
				'parcellation size is %i' %(len(adj),self.nr_labels))
			return
		self.adj_nulldiag = adj
		#it is necessary to rerun pos_helper_gen() because the number of edges
		#is not constant from one adjmat to another.  thus the positions of
		#the edges cannot be assumed to be the same
		self.pos_helper_gen()
		self.adj_helper_gen()
		print "Adjacency matrix %s loaded successfully" % acw.adjmat

		self.curr_node=None
		self.cur_module=None
		self.thresh_type='prop'
		self.txt.set(text='')
		self.vectors_clear()
		self.vectors_gen()
		self.circ_clear()
		self.circ_fig_gen(figure=self.circ_fig)
		self.redraw_circ()
		self.chaco_gen()
		self.color_legend_gen()	
		self.reset_node_color_mayavi()
		self.reset_node_color_circ()

	def load_standalone_matrix(self):
		lsmw=self.load_standalone_matrix_window
		try:
			ci=util.loadmat(lsmw.mat,field=lsmw.field_name)
			if lsmw.mat_order:
				init_ord,bads=util.read_parcellation_textfile(lsmw.mat_order)
				#delete the extras
				if not lsmw.ignore_deletes:
					ci=np.delete(ci,bads)
				ci_ord=util.adj_sort(init_ord,self.labnam)
				#swap the new order
				ci=ci[ci_ord]
		except (util.CVUError,IOError) as e:
			self.error_dialog(str(e))
			return
		except (ValueError,IndexError) as e:
			self.error_dialog("Mismatched channels: %s" % str(e))
			return
		except KeyError as e:
			self.error_dialog("Field not found: %s" % str(e))
			return
		if lsmw.whichkind=='modules':
			import modularity
			self.modules=modularity.comm2list(ci)
			self.update_modules_metadata()
		elif lsmw.whichkind=='scalars':
			#convert data to float to avoid potential integer division
			ci=np.array(ci,dtype=float)
			#normalize scalars to 0-1 range
			self.node_scalars=(ci-np.min(ci))/np.max(ci)

	## USER-DRIVEN INTERACTIONS ##
	def error_dialog(self,message):
		self.error_dialog_window.error=message
		self.error_dialog_window.edit_traits()

	@on_trait_change('all_node_button')
	def display_all(self):
		self.curr_node=None
		self.cur_module=None
		#change mlab source data in main scene
		new_edges = np.zeros([self.nr_edges,2],dtype=int)
		count_edges = 0
		for e,(a,b) in enumerate(zip(self.edges[:,0],self.edges[:,1])):
			if not self.masked[e]:
				new_edges[e]=np.array(self.edges)[e]
			else:
				new_edges[e]=[0,0]
		new_starts=self.lab_pos[new_edges[:,0]]
		new_vecs=self.lab_pos[new_edges[:,1]] - new_starts
		self.vectorsrc.mlab_source.reset(x=new_starts[:,0],y=new_starts[:,1],
			z=new_starts[:,2],u=new_vecs[:,0],v=new_vecs[:,1],w=new_vecs[:,2])
		self.myvectors.actor.property.opacity=.3
		self.vectorsrc.outputs[0].update()
		self.txt.set(text='')
		self.reset_thresh()
		self.edge_color_on()
		self.nodes.glyph.scale_mode='data_scaling_off'
		self.nodes.glyph.glyph.scale_factor=3
		
		#change data in chaco plot
		self.conn_mat.data.set_data("imagedata",self.adj_thresdiag)

		#change data in circle plot
		self.reset_node_color_mayavi()
		self.reset_node_color_circ()
		self.reset_node_color_chaco()
		self.redraw_circ()

	def display_node(self,n):
		if n<0 or n>=self.nr_labels:
			#raise Exception("Internal error: node index not recognized")
			#throwing an exception here causes chacoplot misclicks to throw 
			#odd-looking errors, best to just return quietly and do nothing
			return
		self.curr_node=n
		#change mlab source data in main scene
		new_edges = np.zeros([self.nr_edges,2],dtype=int)
		count_edges = 0
		for e,(a,b) in enumerate(zip(self.edges[:,0],self.edges[:,1])):
			if n in [a,b] and not self.masked[e]:
				new_edges[e]=np.array(self.edges)[e]
				if self.adjdat[e] >= self.thres.lower_threshold and \
						self.adjdat[e] <= self.thres.upper_threshold:
					count_edges+=1
			else:
				new_edges[e]=[0,0]
		if not quiet:
			print "node #%s: %s" % (str(n), self.labnam[n])
			print "expecting "+str(int(count_edges))+" edges"
		new_starts=self.lab_pos[new_edges[:,0]]
		new_vecs=self.lab_pos[new_edges[:,1]] - new_starts
		self.vectorsrc.mlab_source.reset(x=new_starts[:,0],y=new_starts[:,1],
			z=new_starts[:,2],u=new_vecs[:,0],v=new_vecs[:,1],w=new_vecs[:,2])
		self.myvectors.actor.property.opacity=.75
		self.vectorsrc.outputs[0].update()
		self.txt.set(text='  '+self.labnam[n]) #position=self.lab_pos[n]

		#change data in chaco plot
		dat=np.tile(np.min(self.adj_thresdiag),(self.nr_labels,self.nr_labels))
		dat[n,:]=self.adj_thresdiag[n,:]
		self.conn_mat.data.set_data("imagedata",dat)

		#change data in circle plot
		#self.reset_node_color_circ()
		self.redraw_circ()

		#how much resetting is desirable?  e.g. colors

	def display_module(self,modnum,module=None):
		self.cur_module=modnum
		if module is None:
			module=self.modules[self.cur_module]
		if not quiet:
			print str(np.size(module))+" nodes in module"
		new_edges = np.zeros([self.nr_edges,2],dtype=int)
		for e in xrange(0,self.nr_edges,1):
			if self.opts.intramodule_only and not self.masked[e] and (
				(self.edges[e,0] in module) and (self.edges[e,1] in module)):
					new_edges[e]=self.edges[e]
			elif not self.opts.intramodule_only and not self.masked[e] and (
				(self.edges[e,0] in module) or (self.edges[e,1] in module)):
					new_edges[e]=self.edges[e]
			else:
				new_edges[e]=[0,0]
		new_starts=self.lab_pos[new_edges[:,0]]
		new_vecs=self.lab_pos[new_edges[:,1]] - new_starts
		self.vectorsrc.mlab_source.reset(x=new_starts[:,0],y=new_starts[:,1],
			z=new_starts[:,2],u=new_vecs[:,0],v=new_vecs[:,1],w=new_vecs[:,2])
		self.myvectors.actor.property.opacity=.75
		self.vectorsrc.outputs[0].update()
		
		self.nodesource.children[0].scalar_lut_manager.lut_mode='cool'
		new_colors = np.tile(.3,self.nr_labels)
		new_colors[module]=.8
		self.nodes.mlab_source.dataset.point_data.scalars=new_colors
		self.txt.set(text='')
		mlab.draw()
		
		#display on circle plot
		new_color_arr=self.cool_map(new_colors)
		circ_path_offset=len(self.sorted_adjdat)
		for n in xrange(0,self.nr_labels,1):
			self.circ_data[circ_path_offset+n].set_fc(new_color_arr[n,:])
			#self.circ_data[circ_path_offset+n].set_ec(new_color_arr[n,:])
		self.redraw_circ()

		#display on chaco plot
		self.xa.colors=list(new_color_arr)
		self.ya.colors=list(new_color_arr)
		self.conn_mat.request_redraw()

	@on_trait_change('display_scalars_button')
	def display_scalars(self):
		if self.node_scalars is None:
			self.error_dialog('Load some scalars first')
			return
		self.nodesource.children[0].scalar_lut_manager.lut_mode='BuGn'
		self.nodes.mlab_source.dataset.point_data.scalars=self.node_scalars
		self.nodes.glyph.scale_mode='scale_by_scalar'
		self.nodes.glyph.glyph.scale_factor=8
		mlab.draw()
		
		new_color_arr=self.bluegreen_map(self.node_scalars)
		circ_path_offset=len(self.sorted_adjdat)
		for n in xrange(0,self.nr_labels,1):
			self.circ_data[circ_path_offset+n].set_fc(new_color_arr[n,:])
		self.redraw_circ()

		self.xa.colors=list(new_color_arr)
		self.ya.colors=list(new_color_arr)
		self.conn_mat.request_redraw()

	## CALLBACK FUNCTIONS ##
	#chaco callbacks are in ConnmatPointSelector class out of necessity
	#where they override the _select method
	def leftpick_callback(self,picker):
		#for actor in picker.actors
			#if actor in self.nodes.actor.actors:
			#	correct_actor=actor
			#ptid
		if picker.actor in self.nodes.actor.actors:
			ptid = picker.point_id/self.nodes.glyph.glyph_source.glyph_source.\
				output.points.to_array().shape[0]
			if (ptid != -1):
				self.display_node(int(ptid))
		self.pick=picker

	def rightpick_callback(self,picker):
		self.display_all()

	def circ_click(self,event,mpledit):
		if not quiet:
			print 'button=%d,x=%d,y=%d,xdata=%s,ydata=%s'%(event.button,event.x,
				event.y,str(event.xdata),str(event.ydata))
		# in principle all the clicking logic would be done here, but i felt
		# this file was cluttered enough
		mpledit._process_circ_click(event,self)

	## TRAITS-DRIVEN INTERACTIONS ##
	#node selection
	def _select_node_button_fired(self):
		self.node_chooser_window.cur_node=-1
		self.node_chooser_window.edit_traits()

	@on_trait_change('node_chooser_window:notify')
	def node_select_check(self):
		ncw=self.node_chooser_window
		if (not ncw.finished) or ncw.cur_node==-1:
			pass
		else:
			self.display_node(ncw.cur_node)

	#module selection
	def _calc_mod_button_fired(self):
		import modularity
		if self.partitiontype=="metis":
			self.modules=modularity.use_metis(self.adj_nulldiag)
		elif self.partitiontype=="spectral":
			self.modules=modularity.spectral_partition(self.adj_nulldiag,
				delete_extras=self.opts.prune_modules)
		else:
			raise Exception("Partition type %s not found" % self.partitiontype)
		self.update_modules_metadata()

	def update_modules_metadata(self):
		if self.modules is None:
			self.error_dialog('Modules were not loaded properly')
			return
		self.nr_modules=len(self.modules)
		self.module_chooser_window.module_list=[]
		for i in xrange(0,self.nr_modules):
			self.module_chooser_window.module_list.append('Module '+str(i))

	def _select_mod_button_fired(self):
		if self.modules is None:
			self.error_dialog('No modules loaded')
		else:
			self.module_chooser_window.cur_mod=-1
			self.module_chooser_window.finished=False
			self.module_chooser_window.edit_traits()

	@on_trait_change('module_chooser_window:notify')
	def mod_select_check(self):
		mcw=self.module_chooser_window
		if not mcw.finished or mcw.cur_mod==-1:
			pass
		else:
			self.display_module(mcw.cur_mod)

	def _custom_mod_button_fired(self):
		self.module_customizer_window.finished=False
		self.module_customizer_window.edit_traits()

	@on_trait_change('module_customizer_window:notify')
	def custom_mod_check(self):
		mcw=self.module_customizer_window
		if not mcw.finished:
			pass
		else:
			try:
				mcw.index_convert()
			except ValueError as e:
				self.error_dialog('Something went wrong! Blame the programmer')
			self.custom_module=mcw.return_module
			#self.cur_module='custom'
			self.display_module('custom',module=self.custom_module)

	#misc trait changes
	@on_trait_change('pthresh')
	def prop_thresh(self):	
		if self.thresh_type!='prop':
			return
		sort_adjdat=sorted(self.adjdat)
		self.thresval=float(sort_adjdat[int(round(self.pthresh\
			*self.nr_edges))-1])
		dmax=sort_adjdat[self.nr_edges-1]
		self.thres.set(upper_threshold=dmax,lower_threshold=self.thresval)
		self.vectorsrc.outputs[0].update()	
		if not quiet:
			print "upper threshold "+("%.4f" % self.thres.upper_threshold)
			print "lower threshold "+("%.4f" % self.thres.lower_threshold)
		self.redraw_circ()

	@on_trait_change('nthresh')
	def num_thresh(self):
		if self.thresh_type!='num':
			return
		try:
			self.thresval=self.nthresh
			dmax=float(sorted(self.adjdat)[self.nr_edges-1])
			self.thres.set(upper_threshold=dmax,lower_threshold=self.thresval)
		except TraitError as e:
			self.error_dialog(str(e))
			return
		self.vectorsrc.outputs[0].update()
		if not quiet:
			print "upper threshold "+("%.4f" % self.thres.upper_threshold)
			print "lower threshold "+("%.4f" % self.thres.lower_threshold)
		self.redraw_circ()
	
	@on_trait_change('thresh_type')
	def chg_thresh_type(self):
		if self.thresh_type=='prop':
			self.reset_thresh=self.prop_thresh
		elif self.thresh_type=='num':
			self.reset_thresh=self.num_thresh
		self.reset_thresh()

	@on_trait_change('opts:surface_visibility')
	def chg_syrf_vis(self):
		self.syrf_lh.actor.property.set(opacity=self.opts.surface_visibility)
		self.syrf_rh.actor.property.set(opacity=self.opts.surface_visibility)

	@on_trait_change('opts:circ_size')
	def chg_circ_size(self):
		self.circ_fig.axes[0].set_ylim(0,self.opts.circ_size)
		#self.redraw_circ()

	@on_trait_change('opts:show_floating_text')
	def chg_float_text(self):
		self.txt.visible=self.opts.show_floating_text

	# beware.  currently masking only comes from one of these three types
	# which are mutually exclusive.  if this changes, xor wont work anymore
	# one thing that would work would be using addition of binary flags as types
	@on_trait_change('opts:interhemi_off')
	def chg_intermodule_mask(self):
		if self.opts.interhemi_off:
			self.masked=np.logical_or(self.masked,self.interhemi)
		else:
			self.masked=np.logical_xor(self.masked,self.interhemi)
		
	@on_trait_change('opts:lh_off')
	def chg_lh_mask(self):
		if self.opts.lh_off:
			self.masked=np.logical_or(self.masked,self.left)
		else:
			self.masked=np.logical_xor(self.masked,self.left)
	
	@on_trait_change('opts:rh_off')
	def chg_rh_mask(self):
		if self.opts.rh_off:
			self.masked=np.logical_or(self.masked,self.right)
		else:
			self.masked=np.logical_xor(self.masked,self.right)

	#def load_timecourse_data():
		#if self.dataloc==None:
		#	raise Exception('No raw data was specified')
		#elif self.modality==None:
		#	raise Exception('Which modality is this data?  Specify with'
		#		' --modality')
		#raise Exception("I like exceptions")

	#load adjmat/parc
	def _load_adjmat_button_fired(self):
		self.adjmat_chooser_window.finished=False
		self.adjmat_chooser_window.edit_traits()

	@on_trait_change('adjmat_chooser_window:notify')
	def load_adjmat_check(self):
		acw=self.adjmat_chooser_window
		if not acw.finished:
			pass
		elif acw.adjmat:
			self.load_new_adjmat()
		else:
			self.error_dialog('You must specify the adjacency matrix')

	def _load_parc_button_fired(self):
		self.parc_chooser_window.finished=False
		self.parc_chooser_window.edit_traits()

	@on_trait_change('parc_chooser_window:notify')
	def load_parc_check(self):
		pcw=self.parc_chooser_window
		if not pcw.finished:
			pass
		elif pcw.SUBJECTS_DIR and pcw.SUBJECT and pcw.parcellation_name and\
				pcw.labelnames_f:
			self.load_new_parcellation()
		else:
			self.error_dialog('You must specify all of SUBJECT, SUBJECTS_DIR, '
				'the desired label ordering, and the parcellation name '
				'(e.g. aparc.2009)')

	def _load_mod_button_fired(self):
		self.load_standalone_matrix_window.finished=False
		self.load_standalone_matrix_window.whichkind='modules'
		self.load_standalone_matrix_window.edit_traits()

	def _load_scalars_button_fired(self):
		self.load_standalone_matrix_window.finished=False
		self.load_standalone_matrix_window.whichkind='scalars'
		self.load_standalone_matrix_window.edit_traits()

	@on_trait_change('load_standalone_matrix_window:notify')
	def load_standalone_matrix_check(self):
		lmw=self.load_standalone_matrix_window
		if not lmw.finished:
			pass
		elif lmw.mat:
			#check whichkind in the load_standalone() function,
			#in both cases the ordering procedure is the same
			self.load_standalone_matrix()
		else:
			self.error_dialog('You must specify a valid matrix file')	
		
	#snapshots
	def _mayavi_snapshot_button_fired(self):
		self.save_snapshot_window.finished=False
		self.save_snapshot_window.whichplot='mayavi'
		self.save_snapshot_window.edit_traits()

	def _chaco_snapshot_button_fired(self):
		self.save_snapshot_window.finished=False
		self.save_snapshot_window.whichplot='chaco'
		self.save_snapshot_window.edit_traits()

	def _circ_snapshot_button_fired(self):
		self.save_snapshot_window.finished=False
		self.save_snapshot_window.whichplot='circ'
		self.save_snapshot_window.edit_traits()

	@on_trait_change('save_snapshot_window:notify')
	def save_snapshot_check(self):
		ssw=self.save_snapshot_window
		if not ssw.finished:
			pass
		# use continuation passing style
		elif ssw.savefile:
			# capture the continuation
			def saveit():
				try:
					# the contents of the continuation depend on the plot type
					if ssw.whichplot=='circ':
						self.circ_fig.savefig(ssw.savefile,dpi=ssw.dpi,
							facecolor='black')
					elif ssw.whichplot=='mayavi':
						res=np.ceil(500*ssw.dpi/8000.0*111)
						self.hack_mlabsavefig(ssw.savefile,size=(res,res))
					elif ssw.whichplot=='chaco':
						gc=PlotGraphicsContext(self.conn_mat.outer_bounds,
							dpi=ssw.dpi)
						gc.render_component(self.conn_mat)
						gc.save(ssw.savefile)
				except IOError as e:
					self.error_dialog(str(e))
				except KeyError as e:
					self.error_dialog("The library handling the operation you "
						"requested supports multiple file types.  Please "
						"specify a file extension to disambiguate.")
			if os.path.exists(ssw.savefile):
				# set the continuation on the rofw widget and spawn it
				self.set_save_continuation_and_spawn_rofw(saveit)
			else:
				# not a duplicate filename, just call the save continuation
				saveit()
		else:
			self.error_dialog('You must specify the save file')

	def set_save_continuation_and_spawn_rofw(self,continuation):
		self.really_overwrite_file_window.finished=False
		self.really_overwrite_file_window.save_continuation=continuation
		self.really_overwrite_file_window.edit_traits()

	@on_trait_change('really_overwrite_file_window:notify')
	def really_overwrite_file_check(self):
		rofw=self.really_overwrite_file_window
		# if the user clicks OK, call the save continuation
		if rofw.finished:
			rofw.save_continuation()
		# otherwise, don't do anything

	def hack_mlabsavefig(self,fname,size):
		#TODO hacky fix pull request etc
		self.txt.visible=False
		curx,cury=tuple(self.scene.scene_editor.get_size())
		magnif_desired = max(size[0]//curx,size[1]//cury)+1
		newsize=(int(size[0]/magnif_desired),int(size[1]/magnif_desired))
		self.scene.scene_editor.set_size(newsize)
		from tvtk.api import tvtk
		filter=tvtk.WindowToImageFilter(read_front_buffer=True)
		filter.magnification=int(magnif_desired)
		self.scene.scene_editor._lift()
		filter.input = self.scene.scene_editor._renwin
		ex = tvtk.PNGWriter()
		ex.file_name = fname
		ex.input = filter.output
		self.scene.scene_editor._exporter_write(ex)
		self.scene.scene_editor.set_size((curx,cury))
		#set the mayavi text to nothing for the snapshot, then restore it
		self.txt.visible=self.opts.show_floating_text

	#misc button presses
	def _options_button_fired(self):
		self.opts.edit_traits()

	def _color_legend_button_fired(self):
		#set up the color legend
		#spawn the legend window
		self.color_legend_window.edit_traits()

	def _draw_stuff_button_fired(self):
		self.redraw_circ()
		self.conn_mat.request_redraw()

	def _up_node_button_fired(self):
		if self.curr_node==None:
			return
		elif self.curr_node==self.nr_labels-1:	
			self.display_node(0)
		else:
			self.display_node(self.curr_node+1)

	def _down_node_button_fired(self):
		if self.curr_node==None:
			return
		elif self.curr_node==0:
			self.display_node(self.nr_labels-1)
		else:
			self.display_node(self.curr_node-1)
	
	def _center_adjmat_button_fired(self):
		for ax in [self.xa,self.ya]:
			ax.mapper.range.high_setting=self.nr_labels
			ax.mapper.range.low_setting=0
	
	## DRAWING FUNCTIONS ##
	def edge_color_on(self):
		self.myvectors.actor.mapper.scalar_visibility=True

	def edge_color_off(self):
		self.myvectors.actor.mapper.scalar_visibility=False

	def reset_node_color_mayavi(self):
		self.nodesource.children[0].scalar_lut_manager.lut_mode='cool'
		self.nodes.mlab_source.dataset.point_data.scalars=np.tile(.3,
			self.nr_labels)
		mlab.draw()

	def reset_node_color_circ(self):
		#the circle only plots the ~max_edges highest edges.  the exact number 
		#varies with the data, but we can inspect a variable to find it
		circ_path_offset=len(self.sorted_adjdat)
		for n in xrange(0,self.nr_labels,1):
			self.circ_data[circ_path_offset+n].set_fc(self.node_colors[n])
			#self.circ_data[circ_path_offset+n].set_fc((0,0,0))
			#self.circ_data[circ_path_offset+n].set_ec(self.node_colors[n])

	def reset_node_color_chaco(self):
		self.xa.colors = self.node_colors
		self.ya.colors = self.node_colors
	
	def redraw_circ(self):
		vrange=self.thres.upper_threshold-self.thres.lower_threshold
		for e,(a,b) in enumerate(zip(self.sorted_edges[0],
				self.sorted_edges[1])):
			if ((self.sorted_adjdat[e] <= self.thres.upper_threshold) and
				(self.sorted_adjdat[e] >= self.thres.lower_threshold) and
				(self.curr_node==None or self.curr_node in [a,b]) and
		#logic for module display
				(self.cur_module is None or
		#check for a custom module first to avoid null pointer
					(self.cur_module=='custom' and (a in self.
					custom_module and b in self.custom_module)) or
		#check for the current module
					(self.modules is not None and a in self.modules[self.
					cur_module] and b in self.modules[self.cur_module]))):
				self.circ_data[e].set_visible(True)
				if self.myvectors.actor.mapper.scalar_visibility:
					self.circ_data[e].set_ec(self.yellow_map((self.
						sorted_adjdat[e]-self.thres.lower_threshold)/vrange))
				else:
					self.circ_data[e].set_ec((1,1,1))
			else:
				self.circ_data[e].set_visible(False)
		self.circ_fig.canvas.draw()

def preproc():
	#load label names from specified text file for ordering
	labnam,ign=util.read_parcellation_textfile(args['parcorder'])
	adjlabs=args['adjorder']
	
	#load adjacency matrix.  entries in order of labnam
	adj = util.loadmat(args['adjmat'],args['field']) 

	#load surface for visual display
	surf_fname=os.path.join(args['subjdir'],args['subject'],'surf',
		'lh.%s'%args['surftype'])
	surf_struct=util.loadsurf(surf_fname)

	#load parcellation and vertex positions
	labv=util.loadannot(args['parc'],args['subject'],args['subjdir'])

	#calculate label positions from vertex positions
	lab_pos=util.calcparc(labv,labnam,quiet=quiet,parcname=args['parc'])

	# Package dataloc and modality into tuple for passing
	datainfo =(args['dataloc'],args['modality'],args['partitiontype'],
		args['maxedges'],args['subject'],args['parc'],args['adjmat'])

	# Return tuple with summary required data
	return lab_pos,adj,labnam,adjlabs,surf_struct,datainfo

if __name__ == "__main__":
	#gc.set_debug(gc.DEBUG_LEAK)
	cvu_args = preproc()
	cvu = Cvu(cvu_args)
	cvu.configure_traits()
