#mporting NumPy
import numpy as np
# Importing Mayavi mlab and tvtk packages
from mayavi import mlab
from tvtk.api import tvtk

import pickle

# Retrieving the data and set parameters
# --------------------------------------

# load graph data
#g = cfile.obj.get_by_name("connectome_scale500").data

fol='/autofs/cluster/neuromind/rlaplant/mayavi/dtidata/'

nodes=np.load(fol+'dtinodes.npy')
edges=np.load(fol+'dtiedges.npy')

fd=open(fol+'dtiedgdat.obj','r')
edgesdata=pickle.load(fd)
fd.close()
position_array=np.load(fol+'dtipos.npy')

position_key = "dn_position"
edge_key = "fiber_length_mean"
node_label_key = "dn_fsname"

# Node ids you want to create labels for
create_label = []

# Assume node id's are integers
nr_nodes = len(nodes)

x, y, z = position_array[:,0], position_array[:,1], position_array[:,2]

# Retrieve the edges and create a Numpy array
#edges = np.array(g.edges())
nr_edges = len(edges)

# Retrieve edge values
ev = np.zeros( (nr_edges, 1) )
for i in xrange(nr_edges):
    ev[i] = edgesdata[i][2][edge_key]
    # ensure that we are setting the correct edge
#    assert edgesdata[i][0] == edges[i,0] and edgesdata[i][1] == edges[i,1]

# Need to subtract one because the array index starts at zero
edges=edges-1

# Create vectors which will become edges
start_positions = position_array[edges[:, 0]-1, :].T
end_positions = position_array[edges[:, 1]-1, :].T
vectors = end_positions - start_positions

# Perform task
# ------------

# create a new figure
fig = mlab.figure()

nodesource = mlab.pipeline.scalar_scatter(x, y, z, name = 'Node Source')
nodes = mlab.pipeline.glyph(nodesource, scale_factor=3.0, scale_mode='none',                              name = 'Nodes', mode='cube')
nodes.glyph.color_mode = 'color_by_scalar'

vectorsrc = mlab.pipeline.vector_scatter(start_positions[0], 
                             start_positions[1],
                             start_positions[2],
                             vectors[0],
                             vectors[1],
                             vectors[2],
                             name = 'Connectivity Source')


# add scalar array
da = tvtk.DoubleArray(name=edge_key)
da.from_array(ev)
		
#vectorsrc.mlab_source.dataset.point_data.add_array(da)
vectorsrc.mlab_source.dataset.point_data.scalars = da.to_array()
vectorsrc.mlab_source.dataset.point_data.scalars.name = edge_key

# need to update the boundaries
vectorsrc.outputs[0].update()

# Add a thresholding filter to threshold the edges
thres = mlab.pipeline.threshold(vectorsrc, name="Thresholding")
thres.auto_reset_lower = False
print thres.lower_threshold

myvectors = mlab.pipeline.vectors(thres,colormap='gist_heat',
										#mode='cylinder',
										name='Connections',
										#scale_factor=1,
										#resolution=20,
										# make the opacity of the actor depend on the scalar.
										#transparent=True,
										scale_mode = 'vector')

myvectors.glyph.glyph_source.glyph_source.glyph_type = 'dash'
# vectors.glyph.glyph_source.glyph_source.radius = 0.01
myvectors.glyph.color_mode = 'color_by_scalar'
myvectors.glyph.glyph.clamping = False

def display_all():
	vectorsrc.mlab_source.set(x=start_positions[0],y=start_positions[1],
				z=start_positions[2],u=vectors[0],v=vectors[1],w=vectors[2])
	vectorsrc.mlab_source.update()

def display_node(n):
	new_edges = np.zeros([nr_edges,2],dtype=int)	
	#new_ev = np.zeros([nr_edges,1],dtype=int)
	i = 0
	for e in edges:
		if n in [e[0],e[1]]:
			#new_ev[i] = ev[i]
			new_edges[i][:] = [e[0],e[1]]
		else:
			#new_ev[i] = -1
			new_edges[i] = [0,0]
		i += 1
	nr_new_edges = len(new_edges)
	#new_edges = new_edges - 1 # index adjustment was performed earlier
	new_starts = position_array[new_edges[:,0], :].T
	new_ends = position_array[new_edges[:,1], :].T
	newvecs = new_ends - new_starts

	vectorsrc.mlab_source.set(x=new_starts[0],y=new_starts[1],z=new_starts[2],
			u=newvecs[0],v=newvecs[1],w=newvecs[2])

	#da.from_array(new_ev)
	#vectorsrc.mlab_source.dataset.point_data.add_array(da)
	#vectorsrc.mlab_source.dataset.point_data.scalars = da.to_array()
	#vectorsrc.mlab_source.dataset.point_data.scalars.name = edge_key+str(n)
	
	vectorsrc.mlab_source.update()

# create labels
#for la in create_label:
#    row_index = la - 1
#    label = g.node[la][node_label_key]
#    mlab.text3d(position_array[row_index,0],
#                position_array[row_index,1],
#                position_array[row_index,2],
#                '     ' + label,
#               name = 'Node ' + label)

def leftpick_callback(picker_obj):
	if picker_obj.actor in nodes.actor.actors:
		point_id = picker_obj.point_id/nodes.glyph.glyph_source.glyph_source\
			.output.points.to_array().shape[0]
		if (point_id != -1):
			display_node(point_id)
				#the glyph appears to use 1-based indexing, numpy arrays dont
			print point_id + ' thres:' thresh.lower_threshold

def rightpick_callback(picker_obj):
    display_all()

picker = fig.on_mouse_pick(leftpick_callback)
picker.tolerance = .1

fig.on_mouse_pick(rightpick_callback,button='Right')

mlab.show()
