# (C) Roan LaPlante 2013 rlaplant@nmr.mgh.harvard.edu

import bct
import numpy as np
import scipy.io as sio
from collections import OrderedDict
from traits.api import HasTraits,Str,Any,List

class StatisticsDisplay(HasTraits):
	from traitsui.api import View,Item,TabularEditor
	#from traitsui.ui_editors.array_view_editor import ArrayViewEditor
	from traitsui.tabular_adapter import TabularAdapter
	name=Str
	stat=Any	#np.ndarray
	label_names=List(Str)

	def __init__(self,name,stat,labels,**kwargs):
		super(HasTraits,self).__init__(**kwargs)
		self.name=name
		if np.size(stat)==1:
			self.stat=np.array((('','%.3f'%stat,),))
		elif np.size(stat)!=len(labels):
			print np.size(stat),len(labels)
			raise ValueError('Size of graph statistic inconsistent')
		else:
			nr_labels=len(labels)
			self.stat=np.append(
				np.reshape(labels,(nr_labels,1)),
				np.reshape(map(lambda nr:'%.3f'%nr,stat),(nr_labels,1)),
				axis=1)
		#self.stat=np.reshape(stat,(np.size(stat),1))

	traits_view=View(
		#Item('stat',editor=ArrayViewEditor(show_index=False,format='%.4f'),
		#	height=350,width=225,show_label=False),
		Item('stat',editor=TabularEditor(
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
				'degree') and not mods:
			raise ValueError('Need Modules')
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

	elif option=='modularity':
		return bct.modularity_und(adj,mods)[1]
	elif option=='participation coefficient':
		return bct.participation_coef(adj,mods)
	elif option=='within-module degree':
		return bct.module_degree_zscore(adj,mods)
