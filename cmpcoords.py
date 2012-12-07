import nibabel.gifti as gi
import numpy as np
import networkx as nx
from mayavi import mlab
from tvtk.api import tvtk

fol = '/autofs/cluster/neuromind/matt/cmtk_60grad/nmr00370/tp1/CMP/fibers/matrices/connectome_scale500.gpickle'


g = nx.read_gpickle(fol)
g_len = len(g.nodes())
pos = np.zeros((g_len,3))
for i in xrange(1,g_len,1):
	pos[i][:] = g.nodes(data=True)[i][1]['dn_position']











#surfs_lh = fol+'lh.pial.gii'
#surfs_rh = fol+'rh.pial.gii'
#
#annots_lh = fol+'lh.sparc.gii'
#annots_rh = fol+'rh.sparc.gii'
#
#
#surf_lh = gi.read(surfs_lh)
#surf_rh = gi.read(surfs_rh)
#annot_lh = gi.read(annots_lh)
#annot_rh = gi.read(annots_rh)
#vert_lh = surf_lh.darrays[0].data
#vert_rh = surf_rh.darrays[0].data

#ctr = np.vstack((vert_lh.mean(axis=0),vert_rh.mean(axis=0))).mean(axis=0)

#vert = np.vstack((vert_lh,vert_rh))
#print len(vert)

#x,y,z = vert[:,0],vert[:,1],vert[:,2]

x,y,z=pos[:,0],pos[:,1],pos[:,2]

print len(pos)
fig = mlab.figure()

nodesource = mlab.pipeline.scalar_scatter(x,y,z,name='noddy')

nodes = mlab.pipeline.glyph(nodesource,scale_mode='none',scale_factor=2.3,name='whatevernoddy',mode='point')
nodes.glyph.color_mode='color_by_scalar'






mlab.show()
