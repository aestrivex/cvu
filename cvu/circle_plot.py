#    (C) Roan LaPlante 2013 rlaplant@nmr.mgh.harvard.edu
#
#	 This file is copied and modified from MNE Python.  MNE Python is (C) 
#	 copyright by the authors of MNE Python 2011.  This file was modified
#	 03/2013.  For more information, see
#	 https://github.com/mne-tools/mne-python
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

from __future__ import division
import numpy as np
from mne.fixes import tril_indices
import pylab as pl
import matplotlib.path as m_path
import matplotlib.patches as m_patches
import matplotlib.colors as m_col
from collections import OrderedDict
from color_map import CustomColormap

def plot_connectivity_circle_cvu(con, nodes_numberless, indices=None, 
    n_lines=10000, node_colors=None, colormap='YlOrRd', fig=None, reqrois=[],
    suppress_extra_rois=False,
    node_angles=None, node_width=None, facecolor='black',
    textcolor='white', node_edgecolor='black',linewidth=1.5,
    vmin=None,vmax=None, colorbar=False, title=None,
    fontsize_names='auto', bilateral_symmetry=True):
    """Visualize connectivity as a circular graph.

Note: This code is originally taken from public open-source
examples in matplotlib by Nicolas P. Rougier. It was adapted for use in
MNE python, primarily by Martin Luessi, but also by all the other contributors
to MNE python.

There are some differences between the current version and the MNE python
version. Most importantly, the current version offers less flexibility of the
layout of the plot and has algorithms to determine this layout automatically
given the ordering of the CVU dataset. Each hemisphere takes up roughly half
the space and the left hemisphere is always on the left side of the plot. Then
there is a very complex and poorly documented algorithm to randomly suppress 
extra label names so that all of the label names that result are readable.
Note that the suppression of label names can be overwritten in the GUI although
it is quite effortful, typically it is recommended to do image
postprocessing instead.

Parameters
----------
con : array
Connectivity scores. Can be a square matrix, or a 1D array. If a 1D
array is provided, "indices" has to be used to define the connection
indices.

nodes_numberless : list of str
Node names. The order corresponds to the order in con.

indices : tuple of arrays | None
Two arrays with indices of connections for which the connections
strenghts are defined in con. Only needed if con is a 1D array.

n_lines : int | None
If not None, only the n_lines strongest connections (strenght=abs(con))
are drawn.

node_angles : array, shape=(len(nodes_numberless,)) | None
Array with node positions in degrees. If None, the nodes are equally
spaced on the circle. See mne.viz.circular_layout.

node_width : float | None
Width of each node in degrees. If None, "360. / len(nodes_numberless)" is
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

fontsize_names : int | str
The fontsize for the node labels. If 'auto', the program attempts to determine
a reasonable size. 'auto' is the default value.

Returns
-------
fig : instance of pyplot.Figure
The figure handle.
"""
    n_nodes = len(nodes_numberless)

    #reverse the lower hemisphere so that the circle is bilaterally symmetric
    start_hemi = 'l'
    first_hemi = nodes_numberless[0][0]

    def find_pivot(ls, item):
        for i,l in enumerate(ls):
            if l[0]!=item:
                return i

    hemi_pivot = find_pivot(nodes_numberless, first_hemi)

    if bilateral_symmetry:
        if start_hemi==first_hemi:
            nodes_numberless = (nodes_numberless[:hemi_pivot] +
                nodes_numberless[:hemi_pivot-1:-1])

            node_colors = (node_colors[:hemi_pivot] +
                node_colors[:hemi_pivot-1:-1])

            if indices.size > 0:
                indices = indices.copy()
                indices[np.where(indices >= hemi_pivot)] = (
                    n_nodes-1 + hemi_pivot -
                    indices[np.where(indices >= hemi_pivot)])
        else:
            nodes_numberless = (nodes_numberless[hemi_pivot:] +
                nodes_numberless[hemi_pivot-1::-1])
        
            node_colors = (node_colors[hemi_pivot:] +
                node_colors[hemi_pivot-1::-1])

            if indices.size > 0:
                indices_x = indices.copy()
                indices_x[np.where(indices < hemi_pivot)] = (
                    n_nodes-1 - indices[np.where(indices < hemi_pivot)])
                indices_x[np.where(indices >= hemi_pivot)] = (
                    -hemi_pivot + indices[np.where(indices >= hemi_pivot)])
                indices = indices_x
                del indices_x
    #if bilateral symmetry is turned off, then still put the
    #left hemisphere on the left side
    else:
        if start_hemi!=first_hemi:
            nodes_numberless = (nodes_numberless[hemi_pivot:] +
                nodes_numberless[:hemi_pivot])
       
            node_colors = (node_colors[hemi_pivot:] +
                node_colors[:hemi_pivot])

            if indices.size > 0:
                indices_x = indices.copy()
                indices_x[np.where(indices < hemi_pivot)] = (
                    hemi_pivot + indices[np.where(indices < hemi_pivot)])
                indices_x[np.where(indices >= hemi_pivot)] = (
                    -hemi_pivot + indices[np.where(indices >= hemi_pivot)])
                indices = indices_x
                del indices_x

    if node_angles is not None:
        if len(node_angles) != n_nodes:
            raise ValueError('node_angles has to be the same length '
                             'as nodes_numberless')
        # convert it to radians
        node_angles = node_angles * np.pi / 180
    else:
        # uniform layout on unit circle
        node_angles = np.linspace(0, 2 * np.pi, n_nodes, endpoint=False)
    node_angles+=np.pi/2

    if node_width is None:
        node_width = 2 * np.pi / n_nodes
    else:
        node_width = node_width * np.pi / 180

    # handle 1D and 2D connectivity information
    if con.ndim == 1:
        if indices is None:
            raise ValueError('indices has to be provided if con.ndim == 1')
                #we use 1D indices
    elif con.ndim == 2:
        if con.shape[0] != n_nodes or con.shape[1] != n_nodes:
            raise ValueError('con has to be 1D or a square matrix')
        # we use the lower-triangular part
        indices = tril_indices(n_nodes, -1)
        con = con[indices]
    else:
        raise ValueError('con has to be 1D or a square matrix')

    # get the colormap
    if isinstance(colormap, CustomColormap):
        colormap = colormap._get__pl()
    elif isinstance(colormap, basestring):
        colormap = pl.get_cmap(colormap)

    # Make figure background the same colors as axes
    if fig==None:
        fig = pl.figure(figsize=(5, 5), facecolor=facecolor)
    else:
        fig = pl.figure(num=fig.number)
        
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

    axes.spines['polar'].set_visible(False)

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

    # input is already sorted
    #sort_idx = np.argsort(con_abs)
    #con_abs = con_abs[sort_idx]
    #con = con[sort_idx]
    #indices = [ind[sort_idx] for ind in indices]

    # Get vmin vmax for color scaling
    if np.size(con)>0:
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
                           / nodes_n_con[start])
        end_noise[i] *= ((nodes_n_con[end] - nodes_n_con_seen[end])
                         / nodes_n_con[end])

    # scale connectivity for colormap (vmin<=>0, vmax<=>1)
    if np.size(con)>0:
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
    text_angles = get_labels_avg_idx(nodes_numberless,n_nodes,frac=1,pad=np.pi/400)

    #print reqrois
    segments = get_tooclose_segments(text_angles,too_close,reqrois)
    
    for segment in segments:
        prune_segment(text_angles,segment,too_close)

    #print suppress_extra_rois, len(reqrois)
    if suppress_extra_rois and len(reqrois)>0:
        for name in text_angles.keys():
            if name not in reqrois:
                del text_angles[name]

        if fontsize_names=='auto':
            fontsize_names=10
                
    #TODO segments with many guaranteed ROIs are potentially spatially skewed
    #this is probably not worth fixing

    #now calculate how many pairs must be removed and remove them at equal
    #spacing.  there should be no more than theta/(n-1) >= pi/50 pairs where
    #theta is the extent and n is the number of pairs.
    #n-1 is used because each segment holds one item by default
    
    #for angles,hemi in [(text_angles_sh,start_hemi),(text_angles_eh,end_hemi)]:
    #	for name in angles:

    if fontsize_names=='auto':
        fontsize_names=8

    for name in text_angles:
        angle_rad = text_angles[name] + np.pi/2
        #if hemi is end_hemi:
        #	angle_rad+=np.pi
        angle_deg = 180*angle_rad/np.pi
        if angle_deg >= 270 or angle_deg < 90:
            ha = 'left'
        else:
            # Flip the label, so text is always upright
            angle_deg += 180
            ha = 'right'

        name_nonum=name.strip('1234567890')
        hemi=''
        axes.text(angle_rad, 8.2, hemi+name_nonum, size=fontsize_names,
            rotation=angle_deg,
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
    
    return fig, node_angles

def get_labels_avg_idx(lbs,n,frac=.5,pad=0.):
    """Takes:
lbs: a list of (type A) with repeats (e.g. 'supramarginal' appears 4 times)
n: where to stop
frac: fraction of 2*pi to use.  Defaults to .5 (equal length hemispheres)
pad: space to leave at the end

returns d: an ordered dictionary with (type A)/avgposition pairs
this dictionary is scaled to have values between 0 and 2*pi

example: get_labels_avg_idx(['A','B','B','C','D'],4)
returns OrderedDict({'A':0,'B':1.5,'C':3})"""

    d=OrderedDict()
    curlb=lbs[0]
    already=set()
    start=0 #2nd hemi needs to start at offset of too_close + end of 1st hemi
    theta=frac*(np.pi-pad)/n
    for i,e in enumerate(lbs):
        if e!=curlb:
            #get the position of the last label halfway between start and i-1
            ix=(start+i-1)*theta
            #2 cancels out from 2pi and avg of end+start/2
            while already.issuperset((curlb,)):
                #if the label is a duplicate, add meaningless numbers
                #to give it a unique spot on the circle.  We delete these
                #numbers later for display
                curlb+=str(np.random.randint(10))
            d.update({curlb:ix})
            already.add(curlb)
            #start the new label
            start=i
            curlb=e
    #add the last label
    ix=(start+i)*theta
    while already.issuperset((curlb,)):
        curlb+=str(np.random.randint(10))
    d.update({curlb:ix})
    return d

def get_tooclose_segments(angdict, too_close, required_rois=[]):
    """Takes:
angdict: an ordered dictionary with (type A)/avgposition pairs
too_close: a float

returns a list of segments, of consecutive pairs that are closer than
too_close.

A segment is a tuple as follows: 
    (start_item, end_item, extent, num_entries, req_rois)

The start item and end item are the names of the labels at the start and end
of the segment. The extent is the angle (theta) over the entire segment. The 
number of entries is the number of items in the segment. Req_rois is a list of
ROIs that are requied to be in the segment.

for instance: get_tooclose_segments({'A':3,'B':4,'C':5,'D':100},10)
will return [('A','C',2,3)].  There is one segment that has entries too close
together -- that from A to C.  The extent of this segment is 5-3=2.  In a real example the extent would be some fraction of 2*pi"""

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
            extent=np.abs(angdict[e]-angdict[keys[start]])
            segment=(keys[start],keys[i],extent,i-start+1,requires_here)
            segments.append(segment)
            start=None

        #we are now looking for a new segment, so dump the ROIs collected
        requires_here=[]

    return segments

def prune_segment(angdict,seg,too_close):
    """Remove all the labels that are too close together within a segment"""
    #print seg

    #calculate the number of labels to be removed
    extent=seg[2]
    cur_inhabitants=seg[3]
    requires=seg[4]

    max_inhabitants=1+int(np.floor(extent/too_close))
    n_removals=cur_inhabitants-max_inhabitants	

    if max_inhabitants < len(requires):
        import cvu_utils
        raise cvu_utils.CVUError('There is not enough space to display all of'
            ' the ROIs that are guaranteed to be shown.  There is enough space'
            ' for %i ROIs and you required the following ROIs:\n%s' % 
            (max_inhabitants, repr(requires)))

    #remove the remaining labels, starting at the back and using equal spacing

    if cur_inhabitants/n_removals >= 2:
        #calculate the number of nodes to skip, before removing something
        #remove node once every "every" nodes
        every=int(np.ceil( cur_inhabitants/n_removals))
    else:
        every=int(np.ceil( cur_inhabitants/(cur_inhabitants-n_removals)))
    #cap=int(np.ceil( cur_inhabitants/every))

    keys=angdict.keys()
    vals=angdict.values()

    end=seg[1]
    start=seg[0]
    start_idx=keys.index(start)
    end_idx=keys.index(end)

    seg_dict=OrderedDict(zip(keys[start_idx:end_idx+1],
        vals[start_idx:end_idx+1]))

    #print seg_dict
    #delete the entire segment and work with the temporary dict only
    for i in xrange(start_idx,end_idx+1):
        del angdict[keys[i]]

    keys=seg_dict.keys()

    start_idx=keys.index(start)#should be 0
    end_idx=keys.index(end)#should be cur_inhabitants

    start_ang=seg_dict[start]
    end_ang=seg_dict[end]

    guarantee_dict=OrderedDict()
    #for keys not permitted to be removed, remove them as candidates fo
    #every-other elimination
    for r in requires:
        guarantee_dict.update({r:seg_dict[r]})
        del seg_dict[r]

    #print seg_dict
    #print end

    keys=seg_dict.keys()

    #This is problem because end might have been removed from the segment if
    #was required. The purpose of not doing this another way is probably as a 
    #sanity check which can be safely removed now because this code works.

    #end_idx=keys.index(end) #should be cur_inhabitants-len(requires)
    #minus one for python indexing
    end_idx = cur_inhabitants-len(requires)-1
    #print end_idx

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
