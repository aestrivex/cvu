# (C) Roan LaPlante 2013 rlaplant@nmr.mgh.harvard.edu



import numpy as np
from matplotlib.backends.backend_wxagg import *
from matplotlib.backends.backend_wx import *
from matplotlib.backends.backend_agg import *
from matplotlib import *
import wx
from mne.viz import plot_connectivity_circle
from mne.fixes import tril_indices
import pylab as pl
import matplotlib.path as m_path
import matplotlib.patches as m_patches
import matplotlib.colors as m_col
from collections import OrderedDict

#there are some minor changes in this function from the mne version
#namely the return arguments and the figure size which were hard coded in the
#mne function so i copied them

#credit largely goes to martin luessi who adapted this function to mne from
#whoever wrote it originally which is listed in the docstring
def plot_connectivity_circle2(con, node_names, indices=None, n_lines=10000,
	node_angles=None, node_width=None,node_colors=None, facecolor='black',
	textcolor='white', node_edgecolor='black',linewidth=1.5, colormap='YlOrRd',
	vmin=None,vmax=None, colorbar=False, title=None,fig=None,rois=[]):
	"""Visualize connectivity as a circular graph.

Note: This code is based on the circle graph example by Nicolas P. Rougier
http://www.loria.fr/~rougier/coding/recipes.html

The code was adapted from MNE python, credit to Martin Luessi for writing it in
MNE python and all the other MNE python devs

Parameters
----------
con : array
Connectivity scores. Can be a square matrix, or a 1D array. If a 1D
array is provided, "indices" has to be used to define the connection
indices.
node_names : list of str
Node names. The order corresponds to the order in con.
indices : tuple of arrays | None
Two arrays with indices of connections for which the connections
strenghts are defined in con. Only needed if con is a 1D array.
n_lines : int | None
If not None, only the n_lines strongest connections (strenght=abs(con))
are drawn.
node_angles : array, shape=(len(node_names,)) | None
Array with node positions in degrees. If None, the nodes are equally
spaced on the circle. See mne.viz.circular_layout.
node_width : float | None
Width of each node in degrees. If None, "360. / len(node_names)" is
used.
node_colors : list of tuples | list of str
List with the color to use for each node. If fewer colors than nodes
are provided, the colors will be repeated. Any color supported by
matplotlib can be used, e.g., RGBA tuples, named colors.
facecolor : str
Color to use for background. See matplotlib.colors.
textcolor : str
Color to use for text. See matplotlib.colors.
node_edgecolor : str
Color to use for lines around nodes. See matplotlib.colors.
linewidth : float
Line width to use for connections.
colormap : str
Colormap to use for coloring the connections.
vmin : float | None
Minimum value for colormap. If None, it is determined automatically.
vmax : float | None
Maximum value for colormap. If None, it is determined automatically.
colorbar : bool
Display a colorbar or not.
title : str
The figure title.

Returns
-------
fig : instance of pyplot.Figure
The figure handle.
"""
	#TODO	in principle, color code via a list of allowed regions
	# rather than by _div.  Important for compatibility with nonfreesurfer
	# parcellations in principle.  Punt on it for now.

	#TODO for compatibility with nonfreesurfer labels, don't assume that label
	#names begin with L or R

	n_nodes = len(node_names)

	#start_hemi = node_names[0][:3]
	#end_hemi = node_names[-1][:3]	
	#n_starthemi = sum(map(lambda lb:lb[:3]==start_hemi,node_names))
	#n_endhemi = sum(map(lambda lb:lb[:3]==end_hemi,node_names))

	if node_angles is not None:
		if len(node_angles) != n_nodes:
			raise ValueError('node_angles has to be the same length '
							 'as node_names')
		# convert it to radians
		node_angles = node_angles * np.pi / 180
	else:
		# uniform layout on unit circle
		node_angles = np.linspace(0, 2 * np.pi, n_nodes, endpoint=False)

	if node_width is None:
		node_width = 2 * np.pi / n_nodes
	else:
		node_width = node_width * np.pi / 180

	#assign a group to each node, in order already
	#TODO node_groups should be passed in as a dictionary

	nodes_numberless=map(lambda n:n.replace('div','').strip('1234567890_'),
		node_names)
	node_groups=map(lambda n:n[3:],nodes_numberless)
	n_groups=len(set(node_groups))

	# remove all duplicates and return in same order
	# set() is inherently unordered in py, it returns in order of hash values
	n_set=set()
	n_grp_uniqs=[i for i in node_groups if i not in n_set and not n_set.add(i)]

	# currently node_groups is a list of strings, we need unique ID #s
	# node_ids maps from strings to group id
	grp_ids = dict(zip(n_grp_uniqs,xrange(n_groups)))	

	#special=['#b016d8','#26ed1a','#0e89ee','#eaf60b','#ed7fe5','#6372f2',
 	#	'#05d5d5','#e726f4','#bbb27e','#641197','#068c40']
	special=['#26ed1a','#eaf60b','#e726f4','#002aff',
        '#05d5d5','#f4a5e0','#bbb27e','#641179','#068c40']

	hi_contrast=m_col.LinearSegmentedColormap.from_list('hi_contrast',special)

	# assign colors using colormap
	# group assignments and color assignments both refer to index in range
	#grp_colors = [pl.cm.Set3(i / float(n_groups)) for i in xrange(n_groups)]
	grp_colors = [hi_contrast(i/float(n_groups)) for i in xrange(n_groups)]

	node_colors=map(lambda n:grp_colors[grp_ids[n]],node_groups)
	#return node and grp colors to cvu

	# handle 1D and 2D connectivity information
	if con.ndim == 1:
		if indices is None:
			raise ValueError('indices has to be provided if con.ndim == 1')
	elif con.ndim == 2:
		if con.shape[0] != n_nodes or con.shape[1] != n_nodes:
			raise ValueError('con has to be 1D or a square matrix')
		# we use the lower-triangular part
		indices = tril_indices(n_nodes, -1)
		con = con[indices]
	else:
		raise ValueError('con has to be 1D or a square matrix')

	# get the colormap
	if isinstance(colormap, basestring):
		colormap = pl.get_cmap(colormap)

	# Make figure background the same colors as axes
	if fig==None:
		fig = pl.figure(figsize=(5, 5), facecolor=facecolor)
		
	# Use a polar axes
	axes = pl.subplot(111, polar=True, axisbg=facecolor)
	#else:
		# Use the first axis already in the figure
		#axes = fig.get_axes()[0]

	# No ticks, we'll put our own
	pl.xticks([])
	pl.yticks([])

	# Set y axes limit
	pl.ylim(0, 10)
	#pl.ylim(ymin=0)

	# Draw lines between connected nodes, only draw the strongest connections
	if n_lines is not None and len(con) > n_lines:
		con_thresh = np.sort(np.abs(con).ravel())[-n_lines]
	else:
		con_thresh = 0.

	# get the connections which we are drawing and sort by connection strength
	# this will allow us to draw the strongest connections first
	con_abs = np.abs(con)
	con_draw_idx = np.where(con_abs >= con_thresh)[0]

	con = con[con_draw_idx]
	con_abs = con_abs[con_draw_idx]
	indices = [ind[con_draw_idx] for ind in indices]

	# now sort them
	sort_idx = np.argsort(con_abs)
	con_abs = con_abs[sort_idx]
	con = con[sort_idx]
	indices = [ind[sort_idx] for ind in indices]

	# Get vmin vmax for color scaling
	if vmin is None:
		vmin = np.min(con[np.abs(con) >= con_thresh])
	if vmax is None:
		vmax = np.max(con)
	vrange = vmax - vmin

	# We want o add some "noise" to the start and end position of the
	# edges: We modulate the noise with the number of connections of the
	# node and the connection strength, such that the strongest connections
	# are closer to the node center
	nodes_n_con = np.zeros((n_nodes), dtype=np.int)
	for i, j in zip(indices[0], indices[1]):
		nodes_n_con[i] += 1
		nodes_n_con[j] += 1

	# initalize random number generator so plot is reproducible
	rng = np.random.mtrand.RandomState(seed=0)

	n_con = len(indices[0])
	noise_max = 0.25 * node_width
	start_noise = rng.uniform(-noise_max, noise_max, n_con)
	end_noise = rng.uniform(-noise_max, noise_max, n_con)

	nodes_n_con_seen = np.zeros_like(nodes_n_con)
	for i, (start, end) in enumerate(zip(indices[0], indices[1])):
		nodes_n_con_seen[start] += 1
		nodes_n_con_seen[end] += 1

		start_noise[i] *= ((nodes_n_con[start] - nodes_n_con_seen[start])
						   / float(nodes_n_con[start]))
		end_noise[i] *= ((nodes_n_con[end] - nodes_n_con_seen[end])
						 / float(nodes_n_con[end]))

	# scale connectivity for colormap (vmin<=>0, vmax<=>1)
	con_val_scaled = (con - vmin) / vrange

	# Finally, we draw the connections
	for pos, (i, j) in enumerate(zip(indices[0], indices[1])):
		# Start point
		t0, r0 = node_angles[i], 7

		# End point
		t1, r1 = node_angles[j], 7

		# Some noise in start and end point
		t0 += start_noise[pos]
		t1 += end_noise[pos]

		verts = [(t0, r0), (t0, 5), (t1, 5), (t1, r1)]
		codes = [m_path.Path.MOVETO, m_path.Path.CURVE4, m_path.Path.CURVE4,
				 m_path.Path.LINETO]
		path = m_path.Path(verts, codes)

		color = colormap(con_val_scaled[pos])

		# Actual line
		patch = m_patches.PathPatch(path, fill=False, edgecolor=color,
									linewidth=linewidth, alpha=1.)
		axes.add_patch(patch)

	# Draw ring with colored nodes
	#radii = np.ones(n_nodes) * 8
	radii=np.ones(n_nodes)-.2
	bars = axes.bar(node_angles, radii, width=node_width, bottom=7.2,
					edgecolor=node_edgecolor, linewidth=0, facecolor='.9',
					align='center',zorder=10)

	for bar, color in zip(bars, node_colors):
		bar.set_facecolor(color)

	# Draw node labels

	#basic idea -- check for "too close" pairs.  too close is pi/50
	#remove smallest "too close" pairs.  if multiple tied within a segment,
	#remove pairs at equal spacing.
	#calculate each segment individually and find the extent of the segment.

	#TODO this parameter, too_close, could be modified and adjusted for
	#a variety of sizes if ever the circle could be panned (or if it were
	#merely made bigger).  determining the proper value is a matter of 
	#userspace testing
	too_close = np.pi/50

	# get angles for text placement
	text_angles = avgidx(nodes_numberless,n_nodes,frac=1)

	segments = get_tooclose_segments(text_angles,too_close,rois)
	
	for segment in segments:
		prune_segment(text_angles,segment,too_close)
	#TODO segments with many guaranteed ROIs are potentially spatially skewed
	#this is probably not worth fixing

	#now calculate how many pairs must be removed and remove them at equal
	#spacing.  there should be no more than theta/(n-1) >= pi/50 pairs where
	#theta is the extent and n is the number of pairs.
	#n-1 is used because each segment holds one item by default
	
	#for angles,hemi in [(text_angles_sh,start_hemi),(text_angles_eh,end_hemi)]:
	#	for name in angles:
	for name in text_angles:
		angle_rad = text_angles[name]
		#if hemi is end_hemi:
		#	angle_rad+=np.pi
		angle_deg = 180*angle_rad/np.pi
		if angle_deg >= 270 or angle_deg < 90:
			ha = 'left'
		else:
			# Flip the label, so text is always upright
			angle_deg += 180
			ha = 'right'

		hemi=''
		axes.text(angle_rad, 8.2, hemi+name, size=8, rotation=angle_deg,
			rotation_mode='anchor', horizontalalignment=ha,
			verticalalignment='center', color=textcolor)

	if title is not None:
		pl.subplots_adjust(left=0.2, bottom=0.2, right=0.8, top=0.75)
		pl.figtext(0.03, 0.95, title, color=textcolor, fontsize=14)
	else:
		pl.subplots_adjust(left=0.2, bottom=0.2, right=0.8, top=0.8)

	if colorbar:
		sm = pl.cm.ScalarMappable(cmap=colormap,
								  norm=pl.normalize(vmin=vmin, vmax=vmax))
		sm.set_array(np.linspace(vmin, vmax))
		ax = fig.add_axes([.92, 0.03, .015, .25])
		cb = fig.colorbar(sm, cax=ax)
		cb_yticks = pl.getp(cb.ax.axes, 'yticklabels')
		pl.setp(cb_yticks, color=textcolor)
	
	return fig,indices,con,node_colors,n_grp_uniqs,grp_colors

def avgidx(lbs,n,frac=.5):
	"""Takes:
lbs: a list of (type A) with repeats (e.g. 'supramarginal' appears 4 times)
n: where to stop
frac: fraction of 2*pi to use.  Defaults to .5 (equal length hemispheres)

returns d: an ordered dictionary with (type A)/avgposition pairs
this dictionary is scaled to have values between 0 and 2*pi

example: avgidx(['A','B','B','C','D'],4)
returns OrderedDict({'A':0,'B':1.5,'C':3})"""

	d=OrderedDict()
	curlb=lbs[0]
	start=0 #2nd hemi needs to start at offset of too_close + end of 1st hemi
	theta=frac*np.pi/n
	for i,e in enumerate(lbs):
		if e!=curlb:
			#get the position of the last label halfway between start and i-1
			ix=(start+i-1)*theta
			#2 cancels out from 2pi and avg of end+start/2
			d.update({curlb:ix})
			#start the new label
			start=i
			curlb=e
	#add the last label
	ix=(start+i)*theta
	d.update({curlb:ix})
	return d

def get_tooclose_segments(angdict, too_close, required_rois=[]):
	"""Takes:
angdict: an ordered dictionary with (type A)/avgposition pairs
too_close: a float

returns a list of segments, of consecutive pairs that are closer than
too_close.  a segment contains the start index (in the dictionary), the end 
index, the extent (theta), and the number of entries.  The last index of the
segment is for required ROIs that must be displayed.

for instance: get_tooclose_segments({'A':3,'B':4,'C':5,'D':100},10)
will return [('A','C',2,3)]"""

	segments=[]
	keys=angdict.keys()
	nextlb=None
	start=None
	requires_here=[]

	for i,e in enumerate(angdict):
		if e in required_rois:
			requires_here.append(e)

		#try to set the next label
		if i+1<len(angdict):
			nextlb=keys[i+1]
		else:
			nextlb=None

		#check to see if we are too close to the next label
		if nextlb is not None:
			if angdict[nextlb]-angdict[e] < too_close:
				if start is None:
					#we are too close and not in a segment, start one	 
					start=i
				#move on to the next label
				continue
		
		#we aren't too close, close off the segment if needed
		if start is not None:
			extent=angdict[e]-angdict[keys[start]]
			segment=(keys[start],keys[i],extent,i-start+1,requires_here)
			segments.append(segment)
			start=None

		#we are now looking for a new segment, so dump the ROIs collected
		requires_here=[]

	return segments

def prune_segment(angdict,seg,too_close):
	print seg

	#calculate the number of labels to be removed
	extent=seg[2]
	cur_inhabitants=seg[3]
	requires=seg[4]

	max_inhabitants=1+int(np.floor(extent/too_close))
	n_removals=cur_inhabitants-max_inhabitants	

	if max_inhabitants < len(requires):
		import cvu_utils
		raise cvu_utils.CVUError('There is not enough space to display all of'
			' the ROIs that are guaranteed to be shown.')

	#remove the remaining labels, starting at the back and using equal spacing

	if cur_inhabitants/float(n_removals)>=2:
		#calculate the number of nodes to skip, before removing something
		#remove node once every "every" nodes
		every=int(np.ceil( cur_inhabitants/float(n_removals)))
	else:
		every=int(np.ceil( cur_inhabitants/(cur_inhabitants-float(n_removals))))
	#cap=int(np.ceil( cur_inhabitants/float(every)))

	keys=angdict.keys()
	vals=angdict.values()

	end=seg[1]
	start=seg[0]
	start_idx=keys.index(start)
	end_idx=keys.index(end)

	seg_dict=OrderedDict(zip(keys[start_idx:end_idx+1],
		vals[start_idx:end_idx+1]))
	#delete the entire segment and work with the temporary dict only
	for i in xrange(start_idx,end_idx+1):
		del angdict[keys[i]]

	keys=seg_dict.keys()

	start_idx=keys.index(start)#should be 0
	end_idx=keys.index(end)#should be cur_inhabitants

	start_ang=seg_dict[start]
	end_ang=seg_dict[end]

	guarantee_dict=OrderedDict()
	#remove keys not permitted to be removed
	for r in requires:
		guarantee_dict.update({r:seg_dict[r]})
		del seg_dict[r]

	keys=seg_dict.keys()
	end_idx=keys.index(end)#should be cur_inhabitants-len(requires)

	counter=0
	k=0
	#print start_idx,end_idx,n_removals
	#print seg_dict
	while counter<n_removals:
		#print "counter %i" % counter
		for i in xrange(end_idx-counter,start_idx-1,-every+k):
			#print i
			del seg_dict[keys[i]]
			counter+=1
			if counter>=n_removals:
				break
		k+=1
		keys=seg_dict.keys()

	#recalculate the angles of the remaining nodes

	seg_dict.update(guarantee_dict)

	#sort the remaining items by angle
	seg_dict=OrderedDict(sorted(seg_dict.iteritems(),
		key=lambda item:seg_dict[item[0]]))

	angs=np.linspace(start_ang,end_ang,max_inhabitants)
	keys=seg_dict.keys()

	#in theory all of this nonsense with getting the keys by keys() could be
	#made faster by passing around lots of lists and offsets.  its not pythonic
	#and probably not worthwhile (90% of optimize 10% of code etc)

	for i,theta in enumerate(angs):
		seg_dict[keys[start_idx+i]]=theta	

	#the segment is added to the end.  this is fine
	angdict.update(seg_dict)
