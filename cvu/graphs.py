# (C) Roan LaPlante 2013 rlaplant@nmr.mgh.harvard.edu


import graph_tool as gt
import numpy as np
import scipy.io as sio
from modularity import threshold_prop

def mkgraph(adj,thresh_prop):
	nr_nodes = len(adj)
	nr_edges = nr_nodes*(nr_nodes-1)/2.0

	g=gt.Graph(directed=False)
	g.add_vertex(nr_nodes)
	adj,ign=threshold_prop(adj,thresh_prop)

	proparr=np.zeros((nr_edges,))
	q=0
	for i in xrange(0,nr_nodes,1):
		for j in xrange(0,i,1):
			if adj[i,j]>0:
				g.add_edge(j,i)
				proparr[q]=adj[i][j]
				q+=1

	proparr=proparr[:q]

	ep=g.new_edge_property('float')
	ep.a=proparr
	return g,ep
		
def blockmodel(g,ep):
	import graph_tool.community as com
	import time
	print 'nasktoeb'
	tic=time.clock()
	c=com.minimize_blockmodel_dl(g)
	toc=time.clock()
	print toc-tic
	print c.a
	
def clusts(g,ep):
	import graph_tool.clustering as clu
	import time
	print 'zebra'
	tic=time.clock()
	lcl=clu.local_clustering(g)
	toc=time.clock()
	print toc-tic
	gcl=clu.global_clustering(g)
	tic=time.clock()
	print tic-toc
	ecl=clu.extended_clustering(g)
	toc=time.clock()
	print toc-tic
	return lcl,gcl,ecl

def centrality(g,ep):
	import graph_tool.centrality as cen
	#eigc=cen.eigenvector(g,weight=ep)
	#print eigc[1].a
	bc=cen.betweenness(g,weight=ep)
	print bc[1].a
	#hub=cen.hits(g,weight=ep)

ad=sio.loadmat('/autofs/cluster/neuromind/douw/scans/graph/controls/fmri/fmri_laus500_adj_matrices_wei.mat')['adj_matrices']
#ad = np.array(([3,4,9],[4,1,6],[5,3,2]))
ad=np.mean(ad,axis=2)
g,ep=mkgraph(ad,.5)
#print blockmodel(g,ep)
print clusts(g,ep)
#centrality(g,ep)
