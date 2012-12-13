def eqfun(x):
	return lambda y: y==x

def appendhemis(olddict,hemi):
	return dict(map(lambda (k,v): (k,hemi+str(v)), olddict.items()))

import nibabel.gifti as gi
import numpy as np
import networkx as nx
from mayavi import mlab
from tvtk.api import tvtk
import scipy.io as sio
import os
from mne.surface import read_surface
from traits.trait_types import ReadOnly
from mayavi.core.scene import Scene

#mlab.options.backend='envisage'
fol = '/autofs/cluster/neuromind/rlaplant/mridat/fsaverage5c/gift/'
adjmat = '/autofs/cluster/neuromind/rlaplant/pdata/adjmats/pliT.mat'
parc = 'sparc'
parcfile='order_'+parc
srf = '/autofs/cluster/neuromind/rlaplant/mridat/fsaverage5c/surf/'

#LOADING PARCELLATION ORDER + LABEL NAMES FROM TEXT FILE WHICH MUST BE SUPPLIED

labnam=[]
if not os.path.isfile(parcfile):
	raise Exception('A text file must be supplied indicating order of '
		'labels in adjacency matrix')
fd = open(parcfile,'r')
for line in fd:
	labnam.append(line.strip())

## LOADING SURFACES USING NIPY/NIBABEL
surfs_lh = fol+'lh.pial.gii'
surfs_rh = fol+'rh.pial.gii'

annots_lh = fol+'lh.sparc.gii'
annots_rh = fol+'rh.sparc.gii'

plotsurfs_lh = srf+'lh.pial'
plotsurfs_rh = srf+'rh.pial'

adjmat_prop_thres = .1

surf_lh = gi.read(surfs_lh)
surf_rh = gi.read(surfs_rh)
annot_lh = gi.read(annots_lh)
annot_rh = gi.read(annots_rh)
vert_lh = surf_lh.darrays[0].data
vert_rh = surf_rh.darrays[0].data
surfpos_lh, surffaces_lh = read_surface(plotsurfs_lh)
surfpos_rh, surffaces_rh = read_surface(plotsurfs_rh)

## LOADING PARCELLATION DATA FROM NIPY
#currently this expects parcellation files to already be in gifti format,
#which may be improved later

labdict_lh = appendhemis(annot_lh.labeltable.get_labels_as_dict(),"lh_")
#labnam_lh = map(labdict_lh.get,labdict_lh)
labv_lh = map(labdict_lh.get,annot_lh.darrays[0].data)

labdict_rh = appendhemis(annot_rh.labeltable.get_labels_as_dict(),"rh_")
#labnam_rh = map(labdict_rh.get,labdict_rh)
labv_rh = map(labdict_rh.get,annot_rh.darrays[0].data)
#labnam = labnam_lh+labnam_rh
labv = labv_lh+labv_rh

#del labnam_lh;del labnam_rh;
del labv_lh;del labv_rh;

#ctr = np.vstack((vert_lh.mean(axis=0),vert_rh.mean(axis=0))).mean(axis=0)

vert = np.vstack((vert_lh,vert_rh))
print 'Surface has '+str(len(vert))+' vertices'

## LOADING ADJACENCY MATRIX VIA SCIPY.IO
#expects matrix in .mat form, might be adapted to multiple possible filetypes
#later

labels = sio.loadmat('/autofs/cluster/neuromind/rlaplant/mayavi/cvu/sparc.mat')

nr_labels = len(labnam)
nr_verts = len(labv)

print "Parcellation has "+str(nr_labels)+" labels (before bad channel removal)"

if nr_verts != len(vert):
	print nr_verts
	print len(vert)
	raise Exception('Parcellation has inconsistent number of vertices')

lab_counts = np.zeros(nr_labels)
lab_pos = np.zeros((nr_labels,3))

#for i in xrange(1,10,1):
#for i in xrange(1,nr_verts,1):
	#print labels['sparcv'][i]
	#curlab = np.flatnonzero(labels['labnames'] == labels['sparcv'][i])
	#print curlab
	#if len(curlab)>1:
	#	raise Exception('Internal Error:Vertex was assigned to >1 labels')
	#elif len(curlab)==0:
	#	continue
	#lab_counts[curlab] += 1
	#lab_pos[curlab] += vert[i]
#for i in xrange(0,nr_labels,1):
	#lab_pos[i,:] /= lab_counts[i]

#print labels['sparcv'][1:20]
#print labnam[1:20]

#print sum(map(eqfun(unicode(labnam[29])), map(labdict.get,labv)))
#print labnam[4]
#print map(labdict.get,labv)
#print labnam[4]==np.array(map(labdict.get,labv))

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
	print "generating coordinates for "+labnam[i]
	lab_pos[i] = np.mean(vert[curlab],axis=0)

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

#print lab_pos

x,y,z = lab_pos[:,0],lab_pos[:,1],lab_pos[:,2]

## LOADING ADJACENCY MATRIX VIA SCIPY.IO

adj = sio.loadmat(adjmat)
adj = adj['adj_matrices'][:,:,1]

starts = np.zeros((0,3),dtype=int)
vecs = np.zeros((0,3),dtype=int)
edges = np.zeros((0,2),dtype=int)
adjdat = np.zeros((0,1),dtype=int)

for r1 in xrange(0,nr_labels,1):
	for r2 in xrange(0,nr_labels,1):
		if (r1<=r2):
			continue
		#print r1
		#print r2
		starts = np.vstack((starts,lab_pos[r1]))
		vecs = np.vstack((vecs,lab_pos[r2]-lab_pos[r1]))
		adjdat = np.vstack((adjdat,adj[r1][r2]))
		edges = np.vstack((edges,np.array((r1,r2))))

nr_edges = len(edges)
thresval = sorted(adjdat)[int(round((1-adjmat_prop_thres)*nr_edges))]
print thresval

#print adjdat
zi = np.nonzero(adjdat>thresval)
adjdat=adjdat[zi[0]]
starts=starts[zi[0],:]
vecs=vecs[zi[0],:]
edges=edges[zi[0],:]

nr_edges = len(edges)
print nr_edges

#print adjdat
#TODO  ensure the data points are correctly

#print nr_edges
#print len(vecs)
#print len(starts)
#print len(adjdat)

fig = mlab.figure()

syrf_lh = mlab.triangular_mesh(surfpos_lh[:,0],surfpos_lh[:,1],surfpos_lh[:,2],
	surffaces_lh,opacity=.2,color=(.4,.75,.0))
syrf_rh = mlab.triangular_mesh(surfpos_rh[:,0],surfpos_rh[:,1],surfpos_rh[:,2],
	surffaces_rh,opacity=.2,color=(.4,.75,0))

nodesource = mlab.pipeline.scalar_scatter(x,y,z,name='noddy')
nodes = mlab.pipeline.glyph(nodesource,scale_mode='none',scale_factor=3.0,name='noddynod',mode='sphere',color=(0,.6,1))
#nodes.glyph.color_mode='color_by_scalar'
#nodes.mlab_source.dataset.point_data.scalars=np.tile(.1,nr_labels)

vectorsrc = mlab.pipeline.vector_scatter(starts[:,0],starts[:,1],
			starts[:,2],vecs[:,0],vecs[:,1],vecs[:,2],name='connsrc')
vectorsrc.mlab_source.dataset.point_data.scalars = adjdat 
vectorsrc.mlab_source.dataset.point_data.scalars.name='edgekey'
vectorsrc.outputs[0].update()
thres = mlab.pipeline.threshold(vectorsrc,name='thresh',)
thres.auto_reset_lower=False
print thres.lower_threshold

myvectors = mlab.pipeline.vectors(thres,colormap='YlOrRd',name='cons',
		scale_mode='vector',transparent=False)
myvectors.glyph.glyph_source.glyph_source.glyph_type='dash'
myvectors.glyph.color_mode='color_by_scalar'
myvectors.glyph.glyph.clamping=False

myvectors.actor.property.opacity=.3

#print dir(myvectors)

#print vectorsrc.outputs.name_items
#print vectorsrc.outputs[0]

txt = mlab.text3d(0,0,0,'',scale=4.0,color=(.96,.73,1),line_width=9)

def display_all():
	vectorsrc.mlab_source.set(x=starts[:,0],y=starts[:,1],z=starts[:,2],
		u=vecs[:,0],v=vecs[:,1],w=vecs[:,2])
	myvectors.actor.property.opacity=.3
	vectorsrc.outputs[0].update()
	txt.set(text='')
	#thres.mlab_source.update()

def display_node(n):
	new_edges = np.zeros([nr_edges,2],dtype=int)	
	for e in xrange(0,nr_edges,1):
		if n in edges[e]:
			new_edges[e]=edges[e]
		else:
			new_edges[e]=[0,0]

	#print np.nonzero(new_edges[:,0]|new_edges[:,1])
	print "expecting "+str(len(np.nonzero(new_edges[:,0]|new_edges[:,1])[0]))+" edges"
	#print np.nonzero(new_edges)
	#print new_edges[14,:]
	#print edges[14,:]
	new_starts=lab_pos[new_edges[:,0]]
	new_vecs=lab_pos[new_edges[:,1]] - new_starts

	#for r1 in xrange(0,nr_labels,1):
	#	for r2 in xrange(0,nr_labels,1):			
	#		if n<=r2:
	#			continue
	#		elif r1!=n:
	#			new_vecs=np.vstack((new_vecs,np.array((0,0,0))))
	#		else:
	#			new_vecs = np.vstack((new_vecs,lab_pos[r2]-lab_pos[n]))	
	#print np.shape(new_starts)
	vectorsrc.mlab_source.reset(x=new_starts[:,0],y=new_starts[:,1],
		z=new_starts[:,2],u=new_vecs[:,0],v=new_vecs[:,1],w=new_vecs[:,2])
	#vectorsrc.mlab_source.update()
	myvectors.actor.property.opacity=.75
	vectorsrc.outputs[0].update()
	#print thres.lower_threshold
	txt.set(position=lab_pos[n],text='  '+labnam[n])
	#print dir(txt)
	
def leftpick_callback(picker):
	if picker.actor in nodes.actor.actors:
		ptid = picker.point_id/nodes.glyph.glyph_source.glyph_source.\
			output.points.to_array().shape[0]
		if (ptid != -1):
			print "node #%s: %s" % (str(ptid), labnam[ptid])
			display_node(ptid)
			#poppy()

def rightpick_callback(picker):
	display_all()
	#display_node(17)

pck = fig.on_mouse_pick(leftpick_callback)
pck.tolerance = 100
fig.on_mouse_pick(rightpick_callback,button='Right')

mlab.show()
