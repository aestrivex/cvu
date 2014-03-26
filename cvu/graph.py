# (C) Roan LaPlante 2013 rlaplant@nmr.mgh.harvard.edu

import bct
import numpy as np
import scipy.io as sio
from collections import OrderedDict
from traits.api import HasTraits,Str,Any,List
from traitsui.api import View,Item,TabularEditor
from traitsui.tabular_adapter import TabularAdapter

class StatisticsDisplay(HasTraits):
	name=Str
	stat=Any	#np.ndarray
	display_chart=Any	#np.ndarray

	def __init__(self,name,stat,labels,**kwargs):
		super(HasTraits,self).__init__(**kwargs)
		self.name=name
		if np.size(stat)==1:
			self.stat=stat
			self.display_chart=np.array((('','%.3f'%stat,),))
		elif np.size(stat)!=len(labels):
			#print np.size(stat),len(labels)
			raise ValueError('Size of graph statistic inconsistent')
		else:
			nr_labels=len(labels)
			self.stat=stat.reshape((nr_labels,1))
			self.display_chart=np.append(
				np.reshape(labels,(nr_labels,1)),
				np.reshape(map(lambda nr:'%.3f'%nr,stat),(nr_labels,1)),
				axis=1)
		#self.stat=np.reshape(stat,(np.size(stat),1))

	traits_view=View(
		#Item('stat',editor=ArrayViewEditor(show_index=False,format='%.4f'),
		#	height=350,width=225,show_label=False),
		Item('display_chart',editor=TabularEditor(
			adapter=TabularAdapter(columns=['','']),
			editable=False,show_titles=True),
			height=300,width=225,show_label=False),
	)

def do_summary(adj,mods,opts):
	stats=OrderedDict()
	for opt in opts:
		#throw an error if modularity calculations were requested but no
		#community structure exists
		if opt in ('modularity','participation coefficient','within-module '
				'degree') and mods is None:
			import cvu_utils as util
			raise util.CVUError('Need Modules')
	for opt in opts:
		stats.update({opt:do_opt(adj,mods,opt)})
	return stats

def do_opt(adj,mods,option):
	if option=='global efficiency':
		return bct.efficiency_wei(adj)
	elif option=='local efficiency':
		return bct.efficiency_wei(adj,local=True)
	elif option=='average strength':
		return bct.strengths_und(adj)
	elif option=='clustering coefficient':
		return bct.clustering_coef_wu(adj)
	elif option=='eigenvector centrality':
		return bct.eigenvector_centrality_und(adj)
	elif option=='binary kcore':
		return bct.kcoreness_centrality_bu(adj)[0]

	elif option=='modularity':
		return bct.modularity_und(adj,mods)[1]
	elif option=='participation coefficient':
		return bct.participation_coef(adj,mods)
	elif option=='within-module degree':
		return bct.module_degree_zscore(adj,mods)
