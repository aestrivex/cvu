if __name__=="__main__":
	print "Importing libraries"
import nibabel.gifti as gi
import numpy as np
from mayavi import mlab; from tvtk.api import tvtk
import os; import sys; import getopt
from enthought.traits.api import *; from enthought.traits.ui.api import *
from mayavi.core.ui.api import MlabSceneModel,MayaviScene,SceneEditor
from mne.surface import read_surface
import cvu_utils as util
from chaco.api import *; from enable.component_editor import ComponentEditor
from chaco.tools.api import *
from matplotlib.figure import Figure; from pylab import get_cmap
import circle_plot as circ; import mpleditor

quiet=False
if __name__=="__main__":
	print "All libraries loaded"

class CvuPlaceholder(HasTraits):
	conn_mat = Instance(Plot)

class ConnmatPointSelector(SelectTool):
	cvu=Instance(CvuPlaceholder)

	def __init__(self,holder,*args,**kwargs):
		super(SelectTool,self).__init__(*args,**kwargs)
		self.selection_mode='single'
		self.cvu=holder

	def _get_selection_state(self,event):
		return (False,True)

	def _select(self,token,append):
		x,y=self.cvu.conn_mat.map_data((token.x,token.y))
		cvu.display_node(int(np.floor(y)))

class Cvu(CvuPlaceholder):
	scene = Instance(MlabSceneModel, ())
	circ_fig = Instance(Figure,())
	group_by_strength = Enum('all','strong','medium','weak')
	thresh = Range(0.0,1.0,.95)
	up_node_button = Button('^')
	down_node_button = Button('v')
	all_node_button = Button('all')
	calc_mod_button = Button('Calculate modules')
	cycle_mod_button = Button('cycle\nmodule')
	load_adjmat_button = Button('Load an adjacency matrix')
	load_parc_button = Button('Load a parcellation')
	load_what = Enum(None,'adjmat','parcellation')
	curr_node = Trait(None,None,Int)
	cur_module = Trait(None,None,Int)
	extra_button = Button('clickme')
	file_chooser_window = Instance(HasTraits)
	#inherits connmat from placeholder
	python_shell = PythonValue

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
						#editor=CustomEditor(make_matplotlib_plot),
						editor=mpleditor.MPLFigureEditor(),
						height=500,width=500,show_label=False,resizable=True),
					Group(
						HSplit(
							Item(name='load_adjmat_button',show_label=False),
							Item(name='load_parc_button',show_label=False),
						),
						HSplit(
							Item(name='calc_mod_button',show_label=False),
							Item(name='extra_button',show_label=False),
						),
						Item(name='group_by_strength',show_label=False),
						Item(name='thresh'),
						Item(name='python_shell',show_label=False),
					)
				),
			),
			resizable=True)

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

		## SET UP ALL THE DATA TO FEED TO MLAB ##
		self.nr_labels=len(self.lab_pos)

		self.starts = np.zeros((0,3),dtype=float)
		self.vecs = np.zeros((0,3),dtype=float)
		self.edges = np.zeros((0,2),dtype=int)
		self.adjdat = np.zeros((0,1),dtype=float)

		for r1 in xrange(0,self.nr_labels,1):
			for r2 in xrange(0,self.nr_labels,1):
				if (r1<=r2):
					continue
				self.starts = np.vstack((self.starts,self.lab_pos[r1]))
				self.vecs = np.vstack((self.vecs,self.lab_pos[r2]-\
					self.lab_pos[r1]))
				self.adjdat = np.vstack((self.adjdat,self.adj_nulldiag[r1][r2]))
				self.edges = np.vstack((self.edges,np.array((r1,r2))))

		self.nr_edges = len(self.edges)
		if not quiet:
			print str(self.nr_edges)+" total connections"
	
	@on_trait_change('scene.activated')	
	def setup(self):
		## SET UP ALL THE MLAB VARIABLES FOR THE SCENE ##	
		self.fig = mlab.figure(bgcolor=(.36,.34,.30),
			figure=self.scene.mayavi_scene)

		self.syrf_lh = mlab.triangular_mesh(self.srf[0][:,0],self.srf[0][:,1],
			self.srf[0][:,2],self.srf[1],opacity=.15,color=(.4,.75,0),
			name='syrfl')
		self.syrf_rh = mlab.triangular_mesh(self.srf[2][:,0],self.srf[2][:,1],
			self.srf[2][:,2],self.srf[3],opacity=.15,color=(.4,.75,0),
			name='syrfr')

		self.nodesource = mlab.pipeline.scalar_scatter(self.lab_pos[:,0],
			self.lab_pos[:,1],self.lab_pos[:,2],name='noddy')
		self.nodes = mlab.pipeline.glyph(self.nodesource,scale_mode='none',
			scale_factor=3.0,name='noddynod',mode='sphere',colormap='cool')
		self.nodes.glyph.color_mode='color_by_scalar'
		self.txt = mlab.text3d(0,0,0,'',scale=4.0,color=(.8,.6,.98,))

		self.vectors_gen()

		## SET UP CHACO VARIABLES ##
		# set the diagonal of the adjmat to min(data) and not 0 so the
		# plot's color scheme is not completely messed up
		self.thresdiag_gen()
		self.conn_mat = Plot(ArrayPlotData(imagedata=self.adj_thresdiag))
		self.conn_mat.img_plot("imagedata",name='conmatplot',colormap=YlOrRd)
		self.conn_mat.tools.append(PanTool(self.conn_mat,drag_button="right"))
		self.conn_mat.tools.append(ZoomTool(self.conn_mat))
		self.conn_mat.tools.append(ConnmatPointSelector(self,self.conn_mat))

		## SET UP THE CIRCLE PLOT ##
		self.circ_fig_gen()

		## SET UP COLORS AND COLORMAPS ##
		self.yellow_map=get_cmap('YlOrRd')
		self.cool_map=get_cmap('cool')

		# reset_node_color() depends on the circle plot, but its purpose here
		# is setting node color for the mayavi plot
		self.reset_node_color()

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

	def vectors_clear(self):
		self.vectorsrc.remove()

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

	def thresdiag_gen(self):
		self.adj_thresdiag=self.adj_nulldiag.copy()
		self.adj_thresdiag[np.nonzero(self.adj_thresdiag==0)]=\
			np.min(self.adj_thresdiag[np.nonzero(self.adj_thresdiag)])

	def circ_clear(self):
		self.circ_fig.clf()

	# The figure parameter allows figure reuse. At startup, it should be None,
	# but if the user changes the data the existing figure should be preserved
	def circ_fig_gen(self,figure=None):
		fig_holdr,self.sorted_edges,self.sorted_adjdat,\
			self.circ_node_colors=\
			circ.plot_connectivity_circle2(
			np.reshape(self.adjdat,(self.nr_edges,)),self.labnam,
			indices=self.edges.T,colormap="YlOrRd",fig=figure)
		if figure==None or True:
			self.circ_fig=fig_holdr
		self.circ_data = self.circ_fig.get_axes()[0].patches

	## FUNCTIONS FOR LOADING NEW DATA ##
	def load_new_parcellation(self):
		pass

	def load_new_adjmat(self,fname):
		adj = util.loadmat(fname,"adj_matrices")
		if len(adj) != self.nr_labels:
			raise Exception("matrix of wrong size")
		self.adj_nulldiag = adj
		adjdat = np.zeros((0,1),dtype=float)
		for r1 in xrange(0,self.nr_labels,1):
			for r2 in xrange(0,self.nr_labels,1):
				if (r1<=r2): continue
				adjdat=np.vstack((adjdat,self.adj_nulldiag[r1][r2]))
		self.adjdat=adjdat
		print "Load %s successful" % fname

		self.vectors_clear()
		self.vectors_gen()
		self.thresdiag_gen()
		self.conn_mat.data.set_data("imagedata",self.adj_thresdiag)
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
		self.reset_node_color()

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
		self.reset_node_color()

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
		for n in xrange(0,self.nr_labels,1):
			self.circ_data[self.nr_edges+n].\
				set_fc(self.cool_map(new_colors[n]))
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

	def circ_click(self,event):
		#this event has xdata and ydata in reverse polar coordinates (theta,r)
		#do some algebra to figure out which ROI based on the angle
		if not quiet:
			print 'button=%d,x=%d,y=%d,xdata=%s,ydata=%s'%(event.button,event.x,
				event.y,str(event.xdata),str(event.ydata))
		if event.button==3:
			self.display_all()
		elif event.button==1 and event.ydata>=7 and event.ydata<=8:
			nod=self.nr_labels*event.xdata/(np.pi*2)+np.pi/self.nr_labels
			#the formula for the correct node, assuming perfect clicking,
			#is floor(n*theta/2pi).  however, matplotlib seems to not do great
			#with this, the clicking is often too high, so i add this correction
			self.display_node(int(np.floor(nod)))

	## TRAITS-DRIVEN INTERACTIONS ##
	@on_trait_change('thresh')
	def reset_thresh(self):	
		self.thresval = float(sorted(self.adjdat)\
			[int(round(self.thresh*self.nr_edges))-1])
		self.display_grouping()
		#display grouping takes care of circle plot 

	@on_trait_change('calc_mod_button')
	def calc_modules(self):
		import modularity
		if self.partitiontype=="metis":
			self.modules=modularity.use_metis(self.adj_nulldiag)
		elif self.partitiontype=="spectral":
			g = modularity.SpectralPartitioner(self.adj_nulldiag)
			self.modules=g.partition()
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

	@on_trait_change('load_adjmat_button')
	def load_adj_button(self):
		self.load_what='adjmat'
		util.fancy_file_chooser(self)

	@on_trait_change('file_chooser_window.f')
	def load_thing(self):
		if file_chooser_window==None or self.load_what==None or\
				 file_chooser_window.f=='':
			pass
		elif self.load_what=='adjmat':
			self.load_new_adjmat(self.file_chooser_window.f)
		else:
			pass
		self.file_chooser_window.f=''
		self.load_what==None

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

	@on_trait_change('up_node_button')
	def up_button(self):
		if self.curr_node==None:
			return
		elif self.curr_node==self.nr_labels-1:	
			self.display_node(0)
		else:
			self.display_node(self.curr_node+1)

	@on_trait_change('down_node_button')
	def down_button(self):
		if self.curr_node==None:
			return
		elif self.curr_node==0:
			self.display_node(self.nr_labels-1)
		else:
			self.display_node(self.curr_node-1)
	
	@on_trait_change('extra_button')
	def extra(self):
		print "zaerrrooo"
		return

	## DRAWING FUNCTIONS ##
	def edge_color_on(self):
		self.myvectors.actor.mapper.scalar_visibility=True

	def edge_color_off(self):
		self.myvectors.actor.mapper.scalar_visibility=False

	def reset_node_color(self):
		self.nodes.mlab_source.dataset.point_data.scalars=np.tile(.3,
			self.nr_labels)
		mlab.draw()
		for n in xrange(0,self.nr_labels,1):
			self.circ_data[self.nr_edges+n].set_fc(self.circ_node_colors[n])
		self.redraw_circ()	

	def redraw_circ(self):
		vrange=self.thres.upper_threshold-self.thres.lower_threshold
		for e,(a,b) in enumerate(zip(self.sorted_edges[0],
				self.sorted_edges[1])):
			if self.sorted_adjdat[e] <= self.thres.upper_threshold and \
					self.sorted_adjdat[e] >= self.thres.lower_threshold and \
					(self.curr_node==None or self.curr_node in [a,b]) and \
					(self.cur_module==None or self.cur_module<0 or 
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
	global quiet
	fol=None;adjmat=None;parc=None;parcfile=None;surftype=None;
	dataloc=None;modality=None;partitiontype=None
	try:
		opts,args=getopt.getopt(sys.argv[1:],'p:a:s:o:qd:',
			["parc=","adjmat=","adj=","modality=","data=","datadir="\
			"surf=","order=","surf-type=","parcdir=","surfdir=","use-metis",
			"use-spectral"])
	except HasTraits:
		pass
	#except getopt.GetoptError:
	#	raise Exception("You passed in the wrong arguments, you petulant fool!")
	for opt,arg in opts:
		if opt in ["-p","--parc"]:
			parc = arg
		elif opt in ["-a","--adjmat","--adj"]:
			adjmat = arg
		elif opt in ["-s","--surf","--parcdir","--surfdir"]:
			fol = arg
		elif opt in ["-o","--order"]:
			parcfile = arg
		elif opt in ["--surf-type"]:
			surftype = arg
		elif opt in ["-q"]:
			quiet=True
		elif opt in ["--modality"]:
			modality=arg.lower()
		elif opt in ["-d","--data","--datadir"]:
			dataloc=arg
		elif opt in ["--use-metis"]:
			partitiontype="metis"
		elif opt in ["--use-spectral"]:
			partitiontype="spectral"
	if not fol:
		fol = '/autofs/cluster/neuromind/rlaplant/mridat/fsaverage5c/gift/'
	if not adjmat:
		adjmat = '/autofs/cluster/neuromind/rlaplant/pdata/adjmats/pliA1.mat'
	if not parc:
		parc = 'sparc'
	if not parcfile:
		if parc != 'sparc':
			raise Exception('A text file containing channel names must be'
				' supplied with your parcellation')
		else:
			parcfile='/autofs/cluster/neuromind/rlaplant/mayavi/cvu/order_sparc'
	if modality not in ["meg","fmri","dti",None]:
		raise Exception('Modality %s is not supported' % modality)
	if modality in ["fmri","dti"]:
		raise Exception('Modality %s is not yet supported' % modality)
	if not surftype:
		surftype='pial'
	if not partitiontype:
		partitiontype="metis"

	## LOAD PARCELLATION ORDER AND LABEL NAMES ##
	labnam=[]
	if not os.path.isfile(parcfile):
		raise Exception('Channel names not found')
	if not os.path.isfile(adjmat):
		raise Exception('Adjacency matrix not found')
	if not os.path.isdir(fol):
		raise Exception('You must extract GIFTI annotatiions and surfaces to '
			'%s' % fol)
	if ((surftype!=None) and (not (surftype in ["pial","inflated"]))):
		raise Exception("Unrecognized surface type; try pial")

	fd = open(parcfile,'r')
	for line in fd:
		labnam.append(line.strip())

	## LOAD SURFACES USING GIBABEL AND MNE-PYTHON ##

	#surfs_lh = fol+'lh.%s.gii' % surftype
	#surfs_rh = fol+'rh.%s.gii' % surftype
	annots_lh = fol+'lh.%s.gii' % parc
	annots_rh = fol+'rh.%s.gii' % parc
	surfplots_lh = fol+'lh.%s' % surftype
	surfplots_rh = fol+'rh.%s' % surftype

	#surf_lh = gi.read(surfs_lh)
	#surf_rh = gi.read(surfs_rh)
	annot_lh = gi.read(annots_lh)
	annot_rh = gi.read(annots_rh)
	#vert_lh = surf_lh.darrays[0].data
	#vert_rh = surf_rh.darrays[0].data
	surfpos_lh,surffaces_lh = read_surface(surfplots_lh)
	surfpos_rh,surffaces_rh = read_surface(surfplots_rh)
	srfinfo=(surfpos_lh,surffaces_lh,surfpos_rh,surffaces_rh)

	## UNPACKING ANNOTATION DATA ##
	labdict_lh=util.appendhemis(annot_lh.labeltable.get_labels_as_dict(),"lh_")
	labv_lh=map(labdict_lh.get,annot_lh.darrays[0].data)

	labdict_rh=util.appendhemis(annot_rh.labeltable.get_labels_as_dict(),"rh_")
	labv_rh = map(labdict_rh.get,annot_rh.darrays[0].data)

	labv = labv_lh+labv_rh
	del labv_lh;del labv_rh;
	
	## DEFINE CONSTANTS AND RESHAPE SURFACES ##
	vert = np.vstack((surfpos_lh,surfpos_rh))

	nr_labels = len(labnam)
	nr_verts = len(labv)

	if nr_verts != len(vert):
		print nr_verts
		print len(vert)
		raise Exception('Parcellation has inconsistent number of vertices')

	print 'Surface has '+str(nr_verts)+' vertices'
	print "Parcellation has "+str(nr_labels)+" labels (before bad channel removal)"

	lab_counts = np.zeros(nr_labels)
	lab_pos = np.zeros((nr_labels,3))

	## CHECK FOR BAD CHANNELS AND DEFINE LABEL LOCATIONS AS VERTEX AVERAGES ##
	bad_labs=[]
	deleters=[]

	for i in xrange(0,nr_labels,1):
		if labnam[i]=='delete':
			deleters.append(i)
			continue
		curlab=np.flatnonzero(np.array(map(util.eqfun(labnam[i]),labv)))
		if len(curlab)==0:
			print ("Warning: label "+labnam[i]+' has no vertices in it.  This '
				'channel will be deleted')
			bad_labs.append(i)
			continue
		if not quiet:
			print "generating coordinates for "+labnam[i]
		lab_pos[i] = np.mean(vert[curlab],axis=0)

		## DELETE THE BAD CHANNELS ##
	if len(deleters)>0:
		print "Removed "+str(len(deleters))+" bad channels"
		lab_pos=np.delete(lab_pos,deleters,axis=0)
		labnam=np.delete(labnam,deleters,axis=0)
		nr_labels-=len(deleters)
	else:
		print "No bad channels"
	del deleters

	if (len(bad_labs)>0):
		lab_pos=np.delete(lab_pos,bad_labs,axis=0)
		labnam=np.delete(labnam,bad_labs,axis=0)
		nr_labels-=len(bad_labs)
	del bad_labs

	## LOAD THE ADJACENCY MATRIX ##
	adj = util.loadmat(adjmat,"adj_matrices") 

	## FINISH AND RETURN ##
	# Package dataloc and modality into tuple for passing
	datainfo =(dataloc,modality,partitiontype)

	# Return tuple with summary required data
	return (lab_pos,adj,labnam,srfinfo,datainfo)

if __name__ == "__main__":
	cvu_args = preproc()
	cvu = Cvu(cvu_args)
	cvu.configure_traits()
