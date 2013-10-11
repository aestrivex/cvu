# (C) Roan LaPlante 2013 rlaplant@nmr.mgh.harvard.edu

import bct
import numpy as np
import scipy.io as sio
from collections import OrderedDict
from traits.api import HasTraits,Str,Any

class StatisticsDisplay(HasTraits):
	from traitsui.api import View,Item
	from traitsui.ui_editors.array_view_editor import ArrayViewEditor
	name=Str
	stat=Any	#np.ndarray

	def __init__(self,name,stat,**kwargs):
		super(HasTraits,self).__init__(**kwargs)
		self.name=name
		self.stat=np.reshape(stat,(np.size(stat),1))

	traits_view=View(
		Item('stat',editor=ArrayViewEditor(show_index=False,format='%.4f'),
			height=350,width=225,show_label=False),
	)

def do_summary(adj,mods,opts):
	stats=OrderedDict()
	for opt in opts:
		#throw an error if modularity calculations were requested but no
		#community structure exists
		if opt in ('modularity','participation coefficient','within-module '
				'degree') and not mods:
			raise ValueError('Need Modules')
	for opt in opts:
		stats.update({opt:do_opt(adj,mods,opt)})
	return stats

def do_opt(adj,mods,option):
	if option=='global efficiency':
		return bct.efficiency_wei(adj)
	elif option=='local efficiency':
		print 'ghaattn hierr'
		return bct.efficiency_wei(adj,local=True)
	elif option=='average strength':
		return bct.strengths_und(adj)
	elif option=='clustering coefficient':
		return bct.clustering_coef_wu(adj)
	elif option=='eigenvector centrality':
		return bct.eigenvector_centrality_und(adj)

	elif option=='modularity':
		return bct.modularity_und(adj,mods)[1]
	elif option=='participation coefficient':
		return bct.participation_coef(adj,mods)
	elif option=='within-module degree':
		return bct.module_degree_zscore(adj,mods)
