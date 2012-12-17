def eqfun(x):
	return lambda y: y==x

def appendhemis(olddict,hemi):
	return dict(map(lambda (k,v): (k,hemi+str(v)), olddict.items()))

if __name__=="__main__":
	print "Importing modules"

import nibabel.gifti as gi
import numpy as np
import networkx as nx
from mayavi import mlab
from tvtk.api import tvtk
import scipy.io as sio
import os
import sys
import getopt
from enthought.traits.api import *
from enthought.traits.ui.api import *
from mayavi.core.ui.api import *
from mne.surface import read_surface

quiet=False

class Cvu(HasTraits):
	scene = Instance(MlabSceneModel, ())
	button = Button('This button does not yet do anything')
	thresh = Range(0.0,1.0,.9)
	view = View(VSplit( Item(name='scene',
							editor=SceneEditor(scene_class=MayaviScene),
							height=500,width=500,show_label=False,
							resizable=True),
					Group(
						Item(name='button',show_label=False),
						Item(name='thresh')
					)
				),
				resizable=True)

	# Intialize the Cvu Object
	# args are in order pos,adj,names,srfinfo,datainfo
	def __init__(self,args):
		super(Cvu,self).__init__()
		self.lab_pos=args[0]
		self.lab_pos_orig=self.lab_pos
		self.adj=args[1]
		self.labnam=args[2]
		self.nr_labels=len(self.lab_pos)
		self.nr_verts=len(self.adj)
		self.srf=args[3]
		self.dataloc=args[4][0]
		self.modality=args[4][1]

	@on_trait_change('scene.activated')	
	def setup(self):
		x,y,z = self.lab_pos[:,0],self.lab_pos[:,1],self.lab_pos[:,2]

		self.starts = np.zeros((0,3),dtype=float)
		self.vecs = np.zeros((0,3),dtype=float)
		self.edges = np.zeros((0,2),dtype=int)
		self.edgevals = np.zeros((0,2),dtype=float)
		self.adjdat = np.zeros((0,1),dtype=float)

		for r1 in xrange(0,self.nr_labels,1):
			for r2 in xrange(0,self.nr_labels,1):
				if (r1<=r2):
					continue
				self.starts = np.vstack((self.starts,self.lab_pos[r1]))
				self.vecs = np.vstack((self.vecs,self.lab_pos[r2]-\
					self.lab_pos[r1]))
				self.adjdat = np.vstack((self.adjdat,self.adj[r1][r2]))
				self.edges = np.vstack((self.edges,np.array((r1,r2))))

		self.nr_edges_old = len(self.edges)
		self.thresval = float(sorted(self.adjdat)\
			[int(round(self.thresh*self.nr_edges_old))-1])
		if not quiet:
			print "Initial threshold: "+str(self.thresh)

		#zi = np.nonzero(self.adjdat>self.thresh)
		#self.adjdat=self.adjdat[zi[0]]
		#self.starts=se,datainfolf.starts[zi[0],:]
		#self.vecs=self.vecs[zi[0],:]
		#self.edges=self.edges[zi[0],:]

		self.nr_edges = len(self.edges)
		if not quiet:
			print self.nr_edges

		self.fig = mlab.figure(bgcolor=(.36,.34,.30),
			figure=self.scene.mayavi_scene)

		self.syrf_lh = mlab.triangular_mesh(self.srf[0][:,0],self.srf[0][:,1],
			self.srf[0][:,2],self.srf[1],opacity=.15,color=(.4,.75,0),
			name='syrfl')
		self.syrf_rh = mlab.triangular_mesh(self.srf[2][:,0],self.srf[2][:,1],
			self.srf[2][:,2],self.srf[3],opacity=.15,color=(.4,.75,0),
			name='syrfr')

		self.nodesource = mlab.pipeline.scalar_scatter(x,y,z,name='noddy')
		self.nodes = mlab.pipeline.glyph(self.nodesource,scale_mode='none',
			scale_factor=3.0,name='noddynod',mode='sphere',color=(0,.6,1))

		self.vectorsrc = mlab.pipeline.vector_scatter(self.starts[:,0],
			self.starts[:,1],self.starts[:,2],self.vecs[:,0],self.vecs[:,1],
			self.vecs[:,2],name='connsrc')
		self.vectorsrc.mlab_source.dataset.point_data.scalars = self.adjdat 
		self.vectorsrc.mlab_source.dataset.point_data.scalars.name='edgekey'
		self.vectorsrc.outputs[0].update()
		self.thres = mlab.pipeline.threshold(self.vectorsrc,name='thresh',
			low=self.thresval)
		self.thres.auto_reset_lower=False

		self.myvectors = mlab.pipeline.vectors(self.thres,colormap='YlOrRd',
			name='cons',scale_mode='vector',transparent=False)
		self.myvectors.glyph.glyph_source.glyph_source.glyph_type='dash'
		self.myvectors.glyph.color_mode='color_by_scalar'
		self.myvectors.glyph.glyph.clamping=False

		self.myvectors.actor.property.opacity=.3

		self.txt = mlab.text3d(0,0,0,'',scale=4.0,color=(.8,.6,.98,))

		self.display()

	def display(self):
		pck = self.fig.on_mouse_pick(self.leftpick_callback)
		pck.tolerance = 10000
		self.fig.on_mouse_pick(self.rightpick_callback,button='Right')

	def display_all(self):
		self.vectorsrc.mlab_source.set(x=self.starts[:,0],y=self.starts[:,1],
			z=self.starts[:,2],u=self.vecs[:,0],v=self.vecs[:,1],
			w=self.vecs[:,2])
		self.myvectors.actor.property.opacity=.3
		self.vectorsrc.outputs[0].update()
		self.txt.set(text='')

	def display_node(self,n):
		new_edges = np.zeros([self.nr_edges,2],dtype=int)
		count_edges = 0
		for e in xrange(0,self.nr_edges,1):
			if n in self.edges[e]:
				new_edges[e]=self.edges[e]
				if self.adjdat[e] > self.thresval:
					count_edges+=1
			else:
				new_edges[e]=[0,0]

		print "expecting "+str(int(count_edges))+" edges"
		new_starts=self.lab_pos[new_edges[:,0]]
		new_vecs=self.lab_pos[new_edges[:,1]] - new_starts

		self.vectorsrc.mlab_source.reset(x=new_starts[:,0],y=new_starts[:,1],
			z=new_starts[:,2],u=new_vecs[:,0],v=new_vecs[:,1],w=new_vecs[:,2])
		self.myvectors.actor.property.opacity=.75
		self.vectorsrc.outputs[0].update()
		self.txt.set(position=self.lab_pos[n],text='  '+self.labnam[n])
		
	def leftpick_callback(self,picker):
		if picker.actor in self.nodes.actor.actors:
			ptid = picker.point_id/self.nodes.glyph.glyph_source.glyph_source.\
				output.points.to_array().shape[0]
			if (ptid != -1):
				print "node #%s: %s" % (str(ptid), self.labnam[ptid])
				self.display_node(ptid)

	def rightpick_callback(self,picker):
		self.display_all()

	@on_trait_change('thresh')
	def change_thresh(self):	
		self.thresval = float(sorted(self.adjdat)\
			[int(round(self.thresh*self.nr_edges_old))-1])
		self.thres.set(lower_threshold=self.thresval)
		self.vectorsrc.outputs[0].update()

	@on_trait_change('button')
	def button_press(self):
		if self.dataloc==None:
			raise Exception('No raw data was specified')
		elif self.modality==None:
			raise Exception('Which modality is this data?  Specify with'
				' --modality')
		raise Exception("I like exceptions")

def preproc():
	global quiet
	fol=None;adjmat=None;parc=None;parcfile=None;surftype=None;
	dataloc=None;modality=None
	try:
		opts,args=getopt.getopt(sys.argv[1:],'p:a:s:o:qd:',
			["parc=","adjmat=","adj=","modality=","data=","datadir="\
			"surf=","order=","surf-type=","parcdir=","surfdir="])
	except getopt.GetoptError:
		raise Exception("You passed in the wrong arguments, you petulant fool!")
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
	if not fol:
		fol = '/autofs/cluster/neuromind/rlaplant/mridat/fsaverage5c/gift/'
	if not adjmat:
		adjmat = '/autofs/cluster/neuromind/rlaplant/pdata/adjmats/pliT.mat'
	if not parc:
		parc = 'sparc'
	if not parcfile:
		if parc != 'sparc':
			raise Exception('A text file containing channel names must be'
				' supplied with your parcellation')
		else:
			parcfile = '/autofs/cluster/neuromind/rlaplant/mayavi/cvu/order_sparc'
	if modality not in ["meg","fmri","dti",None]:
		raise Exception('Modality %s is not supported' % modality)
	if modality in ["fmri","dti"]:
		raise Exception('Modality %s is not yet supported' % modality)
	if not surftype:
		surftype='pial'

	#Loading parcellation order and label names
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

	## Loading surfaces using gibabel and MNE-python

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

	## Unpacking annotation data
	labdict_lh = appendhemis(annot_lh.labeltable.get_labels_as_dict(),"lh_")
	labv_lh = map(labdict_lh.get,annot_lh.darrays[0].data)

	labdict_rh = appendhemis(annot_rh.labeltable.get_labels_as_dict(),"rh_")
	labv_rh = map(labdict_rh.get,annot_rh.darrays[0].data)

	labv = labv_lh+labv_rh
	del labv_lh;del labv_rh;
	
	#Defining constants and reshaping surfaces
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

	##Check for bad channels and extract label positions as average of vertices
	bad_labs=[]
	deleters=[]

	for i in xrange(0,nr_labels,1):
		if labnam[i]=='delete':
			deleters.append(i)
			continue
		curlab=np.flatnonzero(np.array(map(eqfun(labnam[i]),labv)))
		if len(curlab)==0:
			print ("Warning: label "+labnam[i]+' has no vertices in it.  This '
				'channel will be deleted')
			bad_labs.append(i)
			continue
		if not quiet:
			print "generating coordinates for "+labnam[i]
		lab_pos[i] = np.mean(vert[curlab],axis=0)

	## Delete the bad channels
	if (deleters>0):
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

	## Loading the adjacency matrix

	#Check for valid file types
	if adjmat.endswith('.mat'):
		adj = sio.loadmat(adjmat)
		adj = np.mean(adj['adj_matrices'],axis=2)
		#TODO some .mat files may have other field names e.g.	
		#adj = adj['corrected_imagcoh']
		#In general though it is the user's responsibility to provide a working
		#adjmat of proper formatting, there's simply too much to check for
	elif adjmat.endswith('.npy'):
		adj = np.load(adjmat)
	else:
		raise Exception('Currently only formats supported for adjacency matrix'
			'are .mat and .npy')
		#TODO could raise this exception earlier to facilitate user debugging

	# Package dataloc and modality into tuple for passing
	datainfo =(dataloc,modality)

	##Return tuple with summary required data
	return (lab_pos,adj,labnam,srfinfo,datainfo)

if __name__ == "__main__":
	cvu_args = preproc()
	cvu = Cvu(cvu_args)
	cvu.configure_traits()
