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
from chaco.api import Plot,ArrayPlotData,YlOrRd; 
from enable.component_editor import ComponentEditor
from chaco.tools.api import ZoomTool,PanTool
#from chaco.tools.pan_tool2 import PanTool
from enable.api import Pointer
from matplotlib.figure import Figure; from pylab import get_cmap
import circle_plot as circ; import mpleditor
if __name__=="__main__":
	print "All libraries loaded"

class CvuPlaceholder(HasTraits):
	conn_mat = Instance(Plot)

class ConnmatPanClickTool(PanTool):
	cvu=Instance(CvuPlaceholder)

	event_state=Enum("normal","deciding","panning")
	drag_pointer=Pointer("arrow")

	def __init__(self,holder,*args,**kwargs):
		super(PanTool,self).__init__(**kwargs)
		self.cvu=holder	
		#there is some weird problem with component not being set in super().super()
		self.component=self.cvu.conn_mat
		
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
	group_by_strength = Enum('all','strong','medium','weak')
	thresh = Range(0.0,1.0,.95)
	surface_visibility = Range(0.0,1.0,.15)
	up_node_button = Button('^')
	down_node_button = Button('v')
	all_node_button = Button('all')
	calc_mod_button = Button('Calculate modules')
	cycle_mod_button = Button('cycle\nmodule')
	load_adjmat_button = Button('Load an adjacency matrix')
	draw_stuff_button = Button('Perform outstanding rendering (slow)')
	load_parc_button=Button('Load a parcellation')
	load_surface_button=Button('Load surface files')
	load_what = Enum(None,'adjmat','labelnames','surface')
	curr_node = Trait(None,None,Int)
	cur_module = Trait(None,None,Int)
	prune_modules = Bool
	extra_button = Button('clickme')
	file_chooser_window = Instance(HasTraits)
	parc_chooser_window_finished = Bool
	labelnames_f = File
	parcname = Str
	subject = Str
	subjects_dir = Directory
	#inherits connmat from placeholder
	python_shell = Dict

	## HAVE TRAITSUI ORGANIZE THE GUI ##
	traits_view = View(
			VSplit(
				HSplit(
					Item(name='scene',
						editor=SceneEditor(scene_class=MayaviScene),
						height=500,width=500,show_label=False,resizable=True),
					Item(name='conn_mat',
						editor=ComponentEditor(),
						show_label=False,height=450,width=450,resizable=True),
					Group(	Item(name='up_node_button',show_label=False),
							Item(name='down_node_button',show_label=False),
							Item(name='all_node_button',show_label=False),
							Item(name='cycle_mod_button',show_label=False),
					)
				),
				HSplit(
					Item(name='circ_fig',
						editor=mpleditor.MPLFigureEditor(),
						height=500,width=500,show_label=False,resizable=True),
					Group(
						HSplit(
							Item(name='load_parc_button',show_label=False),
							Item(name='load_adjmat_button',show_label=False),
							Item(name='load_surface_button',show_label=False),
						),
						HSplit(
							Item(name='calc_mod_button',show_label=False),
							Item(name='draw_stuff_button',show_label=False),
							Item(name='extra_button',show_label=False),
						),
						HSplit(
							Item(name='group_by_strength',show_label=False),
							Item(name='prune_modules'),
						),
						Item(name='thresh'),
						Item(name='surface_visibility'),
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
		self.srf=args[3]
		self.dataloc=args[4][0]
		self.modality=args[4][1]
		self.partitiontype=args[4][2]
		self.soft_max_edges=args[4][3]

		## SET UP ALL THE DATA TO FEED TO MLAB ##
		self.nr_labels=len(self.lab_pos)
	
		#self.lab_pos *= 1000
		#print np.shape(self.lab_pos)
	
	@on_trait_change('scene.activated')	
	def setup(self):
		## SET UP DATA ##
		self.pos_helper_gen()
		self.adj_helper_gen()

		## SET UP COLORS AND COLORMAPS ##
		self.yellow_map=get_cmap('YlOrRd')
		self.cool_map=get_cmap('cool')

		## SET UP ALL THE MLAB VARIABLES FOR THE SCENE ##	
		self.fig = mlab.figure(bgcolor=(.36,.34,.30),
			figure=self.scene.mayavi_scene)
		self.surfs_gen()
		self.nodes_gen()
		self.vectors_gen()

		## SET UP CHACO VARIABLES ##
		# set the diagonal of the adjmat to min(data) and not 0 so the
		# plot's color scheme is not completely messed up
		self.conn_mat = Plot(ArrayPlotData(imagedata=self.adj_thresdiag))
		self.conn_mat.img_plot("imagedata",name='conmatplot',colormap=YlOrRd)
		self.conn_mat.tools.append(ZoomTool(self.conn_mat))
		self.conn_mat.tools.append(ConnmatPanClickTool(self,self.conn_mat))
		self.conn_mat.x_axis.set(visible=False)
		self.conn_mat.x_grid.set(visible=False)
		self.conn_mat.y_axis.set(visible=False)
		self.conn_mat.y_grid.set(visible=False)
		#TODO write a controller that asks chaco to explicitly redraw

		## SET UP THE CIRCLE PLOT ##
		self.circ_fig_gen()

		## SET UP THE CALLBACKS (for mayavi and matplotlib) ##
		pck = self.fig.on_mouse_pick(self.leftpick_callback)
		pck.tolerance = 10000
		self.fig.on_mouse_pick(self.rightpick_callback,button='Right')

		self.display_all()

	## VISUALIZATION GENERATOR FUNCTIONS ##
	def init_thres_gen(self):
		self.thresval = float(sorted(self.adjdat)\
			[int(round(self.thresh*self.nr_edges))-1])
		if not quiet:
			print "Initial threshold: "+str(self.thresh)

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
		if not quiet:
			print str(self.nr_edges)+" total connections"
	
	#precondition: adj_helper_gen() must be run after pos_helper_gen()
	def adj_helper_gen(self):
		self.adjdat = np.zeros((self.nr_edges,1),dtype=float)
		i=0
		for r2 in xrange(0,self.nr_labels,1):
			for r1 in xrange(0,r2,1):
				self.adjdat[i] = self.adj_nulldiag[r1][r2]
				i+=1
		self.adj_thresdiag=self.adj_nulldiag.copy()
		self.adj_thresdiag[np.nonzero(self.adj_thresdiag==0)]=\
			np.min(self.adj_thresdiag[np.nonzero(self.adj_thresdiag)])

		#remove all but the soft_max_edges largest connections
		if self.nr_edges > self.soft_max_edges:
			cutoff = sorted(self.adjdat)[self.nr_edges-self.soft_max_edges-1]
			zi = np.nonzero(self.adjdat>=cutoff)

			self.starts=self.starts[zi[0],:]
			self.vecs=self.vecs[zi[0],:]
			self.edges=self.edges[zi[0],:]
			self.adjdat=self.adjdat[zi[0]]
			
			self.nr_edges=len(self.adjdat)

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
			self.srf[0][:,2],self.srf[1],opacity=self.surface_visibility,
			color=(.4,.75,0),name='syrfl')
		self.syrf_rh = mlab.triangular_mesh(self.srf[2][:,0],self.srf[2][:,1],
			self.srf[2][:,2],self.srf[3],opacity=self.surface_visibility,
			color=(.4,.75,0),name='syrfr')

	def nodes_clear(self):
		try:
			self.nodesource.remove()
		except ValueError:
			pass

	def nodes_gen(self):
		self.nodesource = mlab.pipeline.scalar_scatter(self.lab_pos[:,0],
			self.lab_pos[:,1],self.lab_pos[:,2],name='noddy')
		self.nodes = mlab.pipeline.glyph(self.nodesource,scale_mode='none',
			scale_factor=3.0,name='noddynod',mode='sphere',colormap='cool')
		self.nodes.glyph.color_mode='color_by_scalar'
		self.txt = mlab.text3d(0,0,0,'',scale=4.0,color=(.8,.6,.98,))
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

	def chaco_clear(self):
		self.conn_mat.data.set_data("imagedata",np.tile(0,(self.nr_labels,
			self.nr_labels)))
		
	def chaco_gen(self):
		self.conn_mat.data.set_data("imagedata",self.adj_thresdiag)

	def circ_clear(self):
		self.circ_fig.clf()
		self.circ_fig.canvas.draw()

	# The figure parameter allows figure reuse. At startup, it should be None,
	# but if the user changes the data the existing figure should be preserved
	def circ_fig_gen(self,figure=None):
		fig_holdr,self.sorted_edges,self.sorted_adjdat,\
			self.circ_node_colors=\
			circ.plot_connectivity_circle2(
			np.reshape(self.adjdat,(self.nr_edges,)),self.labnam,
			indices=self.edges.T,colormap="YlOrRd",fig=figure,
			n_lines=self.soft_max_edges)
		if figure==None or True:
			self.circ_fig=fig_holdr
		self.circ_data = self.circ_fig.get_axes()[0].patches
		self.reset_node_color_circ()

	## FUNCTIONS FOR LOADING NEW DATA ##
	def load_new_label_names(self,fname):
		try:
			self.labnam=util.read_parcellation_textfile(fname)
		except IOError as e:
			util.error_dialog(str(e))
		self.nr_labels=len(self.labnam)
		self.vectors_clear()
		self.chaco_clear()
		self.circ_clear()
		
	def load_new_parcellation(self):
		try:
			labnam = util.read_parcellation_textfile(self.labelnames_f)
			labv = util.loadannot(self.parcname,self.subject,self.subjects_dir)
			self.lab_pos = util.calcparc(labv,labnam,quiet)
		except IOError as e:
			util.error_dialog(str(e))
			return
		self.labnam=labnam
		self.nr_labels=len(self.labnam)
		self.pos_helper_gen()
		print "Parcellation %s loaded successfully" % self.parcname
		self.surfs_clear()
		self.nodes_clear()
		self.vectors_clear()
		self.chaco_clear()
		self.circ_clear()
		self.nodes_gen()
		self.surfs_gen()
	
	def load_new_surfaces(self):
		pass

	def load_new_adjmat(self,fname):
		try:
			adj = util.loadmat(fname,"adj_matrices")
		except IOError as e:
			util.error_dialog(str(e))
			return
		if len(adj) != self.nr_labels:
			util.error_dialog('The adjacency matrix you added corresponds to a '
				' different parcellation.  Update the parcellation first.\n'
				'Note this check only examines matrix size, you are responsible'
				' for correctly aligning the matrix with its labels')
			return
		self.adj_nulldiag = adj
		self.adj_helper_gen()
		print "Adjacency matrix %s loaded successful" % fname

		self.vectors_clear()
		self.vectors_gen()
		self.chaco_gen()
		self.circ_clear()
		self.circ_fig_gen(figure=self.circ_fig)
		self.redraw_circ()

	## USER-DRIVEN INTERACTIONS ##
	@on_trait_change('all_node_button')
	def display_all(self):
		self.curr_node=None
		if self.cur_module != None and self.cur_module >=1:
			self.cur_module*=-1
		#change mlab source data in main scene
		self.vectorsrc.mlab_source.set(x=self.starts[:,0],y=self.starts[:,1],
			z=self.starts[:,2],u=self.vecs[:,0],v=self.vecs[:,1],
			w=self.vecs[:,2])
		self.myvectors.actor.property.opacity=.3
		self.vectorsrc.outputs[0].update()
		self.txt.set(text='')
		self.reset_thresh()
		
		#change data in chaco plot
		self.conn_mat.data.set_data("imagedata",self.adj_thresdiag)

		#change data in circle plot
		self.reset_node_color_mayavi()
		self.reset_node_color_circ()
		self.redraw_circ()

	def display_node(self,n):
		if n<0 or n>=self.nr_labels:
			#raise Exception("Internal error: node index not recognized")
			#throwing an exception here causes chacoplot misclicks to throw 
			#odd-looking errors, best to just return quietly and do nothing
			return
		self.curr_node=n
		if self.cur_module != None and self.cur_module >= 1:
			self.cur_module*=-1
		#change mlab source data in main scene
		new_edges = np.zeros([self.nr_edges,2],dtype=int)
		count_edges = 0
		for e,(a,b) in enumerate(zip(self.edges[:,0],
				self.edges[:,1])):
			if n in [a,b]:
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
		self.txt.set(position=self.lab_pos[n],text='  '+self.labnam[n])

		#change data in chaco plot
		dat=np.tile(np.min(self.adj_thresdiag),(self.nr_labels,self.nr_labels))
		dat[n,:]=self.adj_thresdiag[n,:]
		self.conn_mat.data.set_data("imagedata",dat)
		#is resetting threshold desirable behavior?  probably not

		#change data in circle plot
		self.reset_node_color_circ()
		self.redraw_circ()

	#module is an optional array of node indices to display.  if module
	#is not provided it is assumed that we are looking for the builtin modules
	def display_module(self,module=None):
		if module==None:
			module=self.modules[self.cur_module-1]
		if not quiet:
			print str(int(len(np.squeeze(module))))+" nodes in module"
		new_edges = np.zeros([self.nr_edges,2],dtype=int)
		for e in xrange(0,self.nr_edges,1):
			if (self.edges[e,0] in module) and (self.edges[e,1] in module):
				new_edges[e]=self.edges[e]
			else:
				new_edges[e]=[0,0]
		new_starts=self.lab_pos[new_edges[:,0]]
		new_vecs=self.lab_pos[new_edges[:,1]] - new_starts
		self.vectorsrc.mlab_source.reset(x=new_starts[:,0],y=new_starts[:,1],
			z=new_starts[:,2],u=new_vecs[:,0],v=new_vecs[:,1],w=new_vecs[:,2])
		self.myvectors.actor.property.opacity=.75
		self.vectorsrc.outputs[0].update()
		
		new_colors = np.tile(.3,self.nr_labels)
		new_colors[module]=.8
		self.nodes.mlab_source.dataset.point_data.scalars=new_colors
		mlab.draw()
		
		#display on circle plot
		new_color_arr=self.cool_map(new_colors)
		circ_path_offset=len(self.sorted_adjdat)
		for n in xrange(0,self.nr_labels,1):
			self.circ_data[circ_path_offset+n].set_fc(new_color_arr[n,:])
			#self.circ_data[circ_path_offset+n].set_ec(new_color_arr[n,:])
		self.redraw_circ()

	def display_grouping(self):
		weakmid_cut=float(sorted(self.adjdat)\
			[int(round(self.nr_edges*(2.0*self.thresh/3+1.0/3)))-1])
		midstrong_cut=float(sorted(self.adjdat)\
			[int(round(self.nr_edges*(1.0*self.thresh/3+2.0/3)))-1])
		max=float(sorted(self.adjdat)[self.nr_edges-1])

		if (self.group_by_strength=="all"):
			self.thres.set(upper_threshold=max,lower_threshold=self.thresval)
			self.edge_color_on()
		else:
			self.edge_color_off()
			if (self.group_by_strength=="strong"):
				self.thres.set(upper_threshold=max,\
					lower_threshold=midstrong_cut)
			elif (self.group_by_strength=="medium"):
				self.thres.set(lower_threshold=weakmid_cut,\
					upper_threshold=midstrong_cut)
			elif (self.group_by_strength=="weak"):
				self.thres.set(upper_threshold=weakmid_cut,\
				lower_threshold=self.thresval)
		self.vectorsrc.outputs[0].update()	
		if not quiet:
			print "upper threshold "+("%.4f" % self.thres.upper_threshold)
			print "lower threshold "+("%.4f" % self.thres.lower_threshold)
		self.redraw_circ()

	## CALLBACK FUNCTIONS ##
	#chaco callbacks are in ConnmatPointSelector class out of necessity
	#where they override the _select method
	def leftpick_callback(self,picker):
		if picker.actor in self.nodes.actor.actors:
			ptid = picker.point_id/self.nodes.glyph.glyph_source.glyph_source.\
				output.points.to_array().shape[0]
			if (ptid != -1):
				self.display_node(int(ptid))

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
	@on_trait_change('thresh')
	def reset_thresh(self):	
		self.thresval = float(sorted(self.adjdat)\
			[int(round(self.thresh*self.nr_edges))-1])
		self.display_grouping()
		#display grouping takes care of circle plot 

	@on_trait_change('surface_visibility')
	def chg_syrf_vis(self):
		self.syrf_lh.actor.property.set(opacity=self.surface_visibility)
		self.syrf_rh.actor.property.set(opacity=self.surface_visibility)

	@on_trait_change('calc_mod_button')
	def calc_modules(self):
		import modularity
		if self.partitiontype=="metis":
			self.modules=modularity.use_metis(self.adj_nulldiag)
		elif self.partitiontype=="spectral":
			self.modules=modularity.spectral_partition(self.adj_nulldiag,
				delete_extras=self.prune_modules)
		else:
			raise Exception("Partition type %s not found" % self.partitiontype)
		self.display_all()
		self.cur_module=1
		self.nr_modules=len(self.modules)
		self.display_module()

	#def load_timecourse_data():
		#if self.dataloc==None:
		#	raise Exception('No raw data was specified')
		#elif self.modality==None:
		#	raise Exception('Which modality is this data?  Specify with'
		#		' --modality')
		#raise Exception("I like exceptions")

	def _load_adjmat_button_fired(self):
		self.load_what='adjmat'
		util.fancy_file_chooser(self)


	def _load_parc_button_fired(self):
		self.parc_chooser_window_finished=False
		util.parcellation_chooser(self)

	def _load_surface_button_fired(self):
		util.error_dialog('not supported yet')
		#self.load_what='surface'
		#util.fancy_file_chooser(self)
	
	@on_trait_change('file_chooser_window.f')
	def load_thing(self):
		if self.file_chooser_window==None or self.load_what==None or\
				 self.file_chooser_window.f=='':
			pass
		elif self.load_what=='adjmat':
			self.load_new_adjmat(self.file_chooser_window.f)
		elif self.load_what=='labelnames':
			self.load_new_label_names(self.file_chooser_window.f)
		elif self.load_what=='surface':
			pass
			#self.surf_f=self.file_chooser_window.f
			#self.load_parc_check()
		else:
			pass
		self.file_chooser_window.f=''
		self.load_what==None
	
	@on_trait_change('parc_chooser_window_finished')
	def load_parc_check(self):
		if not self.parc_chooser_window_finished:
			pass
		elif self.subjects_dir and self.subject and self.parcname and\
				self.labelnames_f:
			self.load_new_parcellation()
		else:
			util.error_dialog('You must specify all of SUBJECT, SUBJECTS_DIR, '
				'and the parcellation name (e.g. aparc.2009)')

	@on_trait_change('cycle_mod_button')
	def cycle_module(self):
		self.display_all()
		if self.cur_module==None:
			return
		elif self.cur_module < 0:
			self.cur_module*=-1
		if self.cur_module==self.nr_modules:
			self.cur_module=1
		else:
			self.cur_module=self.cur_module+1
		self.display_module()	
	#TODO MAJOR REWORK AND MODULARIZATION (no pun intended) OF ALL DISPLAY LOGIC

	def _draw_stuff_button_fired(self):
		#util.error_dialog('This button is not currently used')	
		self.redraw_circ()

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
	
	def _extra_button_fired(self):
		util.error_dialog('This button is not currently used')

	## DRAWING FUNCTIONS ##
	def edge_color_on(self):
		self.myvectors.actor.mapper.scalar_visibility=True

	def edge_color_off(self):
		self.myvectors.actor.mapper.scalar_visibility=False

	def reset_node_color_mayavi(self):
		self.nodes.mlab_source.dataset.point_data.scalars=np.tile(.3,
			self.nr_labels)
		mlab.draw()

	def reset_node_color_circ(self):
		#the circle only plots the ~10000 highest edges.  the exact number of edges
		#is variable dependent on the data, but we can inspect a variable to find it
		circ_path_offset=len(self.sorted_adjdat)
		for n in xrange(0,self.nr_labels,1):
			self.circ_data[circ_path_offset+n].set_fc(self.circ_node_colors[n])
			#self.circ_data[circ_path_offset+n].set_fc((0,0,0))
			#self.circ_data[circ_path_offset+n].set_ec(self.circ_node_colors[n])
	
	def redraw_circ(self):
		vrange=self.thres.upper_threshold-self.thres.lower_threshold
		for e,(a,b) in enumerate(zip(self.sorted_edges[0],
				self.sorted_edges[1])):
			if self.sorted_adjdat[e] <= self.thres.upper_threshold and \
					self.sorted_adjdat[e] >= self.thres.lower_threshold and \
					(self.curr_node==None or self.curr_node in [a,b]) and \
					(self.cur_module==None or self.cur_module<0 or 
					#the current module is 0 indexed but saved as 1-n because
					#negative values are stateful
					(a in self.modules[self.\
					cur_module-1] and b in self.modules[self.cur_module-1])):
				self.circ_data[e].set_visible(True)
				if self.myvectors.actor.mapper.scalar_visibility:
					self.circ_data[e].set_ec(self.yellow_map((self.\
						sorted_adjdat[e]-self.thres.lower_threshold)/vrange))
				else:
					self.circ_data[e].set_ec((1,1,1))
			else:
				self.circ_data[e].set_visible(False)
		self.circ_fig.canvas.draw()

def preproc():
	#load label names from specified text file for ordering
	labnam=util.read_parcellation_textfile(args['parcfile'])
	
	#load adjacency matrix.  entries in order of labnam
	adj = util.loadmat(args['adjmat'],args['field']) 

	#load surface for visual display
	surf_fname=(args['subjdir']+args['subject']+'/surf/lh.%s')%args['surftype']
	surf_struct=util.loadsurf(surf_fname)

	#load parcellation and vertex positions
	labv=util.loadannot(args['parc'],args['subject'],args['subjdir'])

	#calculate label positions from vertex positions
	lab_pos=util.calcparc(labv,labnam,quiet)

	# Package dataloc and modality into tuple for passing
	datainfo =(args['dataloc'],args['modality'],args['partitiontype'],
		args['maxedges'])

	# Return tuple with summary required data
	return lab_pos,adj,labnam,surf_struct,datainfo

if __name__ == "__main__":
	#gc.set_debug(gc.DEBUG_LEAK)
	cvu_args = preproc()
	cvu = Cvu(cvu_args)
	cvu.configure_traits()
