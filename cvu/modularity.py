# (C) Roan LaPlante 2013 rlaplant@nmr.mgh.harvard.edu

import numpy as np
import scipy.linalg as lin

def threshold_prop(adjmat,threshold_p,delete_extras=False):
	adjmat=np.triu(adjmat)
	asort = np.sort(adjmat.ravel())
	cutoff = asort[int((1-threshold_p/2)*len(asort))]
	adjmat[adjmat<cutoff]=0
	adjmat=adjmat+adjmat.transpose()

	#delete any rows for which all the data has been removed
	if delete_extras:
		deleters=np.nonzero(np.sum(adjmat,axis=1)==0)[0]
		adjmat=np.delete(adjmat,deleters,axis=0)
		adjmat=np.delete(adjmat,deleters,axis=1)
		print "%i nodes were deleted from the graph due to null connections" % \
			len(deleters)
	else:
		deleters=np.array(())

	return adjmat,deleters

def comm2list(indices,zeroindexed=False):
	nr_indices=max(indices)
	ls=[]
	for c in xrange(0,nr_indices,1):
		ls.append([])
	i=0
	z=int(not zeroindexed)
	for i in xrange(0,len(indices),1):
		ls[indices[i]-z].append(i)
	return ls

def list2comm(mlist,zeroindexed=False):
	nr_indices=sum(map(len,mlist))
	ci=np.zeros((nr_indices,))	
	z=int(not zeroindexed)
	for i in xrange(0,len(mlist),1):
		for j in xrange(0,len(mlist[i]),1): #THIS IS BUGGED FIX IT
			ci[mlist[i][j]]=i+z
	return list(ci)

def unpermute(mods,perm,forward=False):
	mapper={}
	for i in xrange(0,len(perm),1):
		if forward:
			mapper.update({i:perm[i]})
		else:
			mapper.update({perm[i]:i})
	new_mods=[]
	for mod in mods:
		new_mods.append(map(mapper.get,mod))
	if forward:
		new_mods.remove
	return new_mods

def reacquire_olds(deleters,nr_nodes):
	olds=range(0,nr_nodes,1)
	c=0
	for i in xrange(0,nr_nodes+len(deleters),1):
		if i in deleters:
			c+=1
		else:
			olds[i-c]+=c
	return olds

def use_metis(adjmat,threshold_p=.3,nr_modules=8):
	#just make a call to metis asking to partition this graph
	import networkx as nx
	import metis
	adjmat,deleters=threshold_prop(adjmat,threshold_p)
	g=nx.Graph(adjmat)
	objval,parts=metis.part_graph(g,nr_modules)
	ret=[]
	for i in xrange(0,nr_modules,1):
		ret.append(np.array(np.nonzero(np.array(parts)==i)))
	return ret

	if len(deleters)==0: #skip this check if nothing was deleted
		return ret
	else:
		reinsert_olds_perm = reacquire_olds(deleters,len(adjmat))
		modules=unpermute(ret,reinsert_olds_perm,forward=True)
		return modules


def spectral_partition(adjmat,delete_extras=False,threshold_p=.3):
	#pythonization of brain connectivity toolkit
	adjmat,deleters=threshold_prop(adjmat,threshold_p,
		delete_extras=delete_extras)

	#import cvu_utils as ut
	#adjmat=ut.loadmat('/autofs/cluster/neuromind/rlaplant/pdata/adjmats/stretchy.mat',field='dat',avg=False)
	#deleters=[]

	nr_nodes=len(adjmat)
	#print np.shape(np.nonzero(adjmat))
	permutation=np.array(range(0,nr_nodes,1))
	#permutation=np.random.permutation(nr_nodes)
	#adjmat=adjmat[permutation][:,permutation]

	k=np.sum(adjmat,axis=0)
	m=np.sum(k)
	init_modmat=adjmat-np.outer(k,k)/(1.0*m)

	modules = []

	def recur(module,modmat):
		n=len(modmat)

		d,v=lin.eigh(modmat)
		i=np.nonzero(d==np.max(d))[0]
		#print d
		#print np.max(d)
		#print i
		#print np.nonzero(d==np.max(d))
		max_eigvec=v[:,i]
		#print max_eigvec.T

		mod_asgn=(max_eigvec>=0)*2-1
		#mod_asgn=mod_asgn.T		#make equations prettier by aligning s
		q=np.dot(mod_asgn.T,np.dot(modmat,mod_asgn))[0][0]
		#print q
		if q>0:		# change in modularity was positive
			qmax=q
			modmat=modmat-np.diag(np.diag(modmat))
			it=np.ma.masked_array(np.ones((n,1)),False)
			mod_asgn_iter=mod_asgn.copy()
			itr_num=0
			while np.any(it): # make some iterative fine tuning
				q_iter=qmax-4*mod_asgn_iter*(np.dot(modmat,mod_asgn_iter))
				qmax=np.max(q_iter*it)
				imax=np.nonzero(q_iter==qmax)
				mod_asgn_iter[imax]*=-1
				it[imax]=np.ma.masked 
				if qmax>q:
					q=qmax
					mod_asgn=mod_asgn_iter
				itr_num+=1
				if itr_num>2*n:
					raise Exception("DIEDIEDIE")
			if np.abs(np.sum(mod_asgn))==n: # iteration yielded null module
				modules.append(np.array(module).tolist())
				return
			else:
				mod1=module[np.nonzero(mod_asgn==1)[0]]
				mod2=module[np.nonzero(mod_asgn==-1)[0]]
				modmat1=init_modmat[mod1][:,mod1]
				modmat1-=np.diag(np.sum(modmat1,axis=0))
				modmat2=init_modmat[mod2][:,mod2]
				modmat2-=np.diag(np.sum(modmat2,axis=0))
				recur(mod1,modmat1)
				recur(mod2,modmat2)
				return
		else:		# change in modularity was negative
			modules.append(np.array(module).tolist())
			return

	recur(permutation,init_modmat.copy())
	#unpermute everything
	#modules=unpermute(modules,permutation)
	
	#reinsert the deleted elements so that CVU knows module indices
	#using unpermute()
	if len(deleters)==0: #skip this check if nothing was deleted
		return modules
	else:
		reinsert_olds_perm = reacquire_olds(deleters,nr_nodes)
		modules=unpermute(modules,reinsert_olds_perm,forward=True)
		return modules

class NaiveSpectralPartitioner():
	#old attempts at writing a Newman 2006
	def __init__(self,adjmat,nr_edges=0):
		self.adjmat=adjmat
		self.nr_nodes=len(self.adjmat)

	def partition(self):
		self.adjmat = threshold_prop(self.adjmat)
		adj = self.adjmat
		nr_edges=len(np.nonzero(adj)[1])
		degvec = np.zeros([len(adj),1])
		for i in xrange(0,len(adj),1):
			degvec[i]=int(len(np.transpose(np.nonzero(adj[i,:]))))
	
		degmat = np.zeros([len(adj),len(adj)])	
		for i in xrange(0,len(self.adjmat),1):
			for j in xrange(0,len(adj),1):
				degmat[i,j]=degvec[i]*degvec[j]

		self.modmat=adj-(degmat/(2*nr_edges))
		startgrp=np.arange(self.nr_nodes,dtype=int).T
		#print np.shape(startgrp)
		self.ret_modules = []

		self.recur_partition(self.modmat,startgrp,startgrp.copy())
		#print self.ret_modules
		#print self.ret_modules[0].dtype

		return self.ret_modules

	def recur_partition(self,modmat,curgrp,curgrpinds):
		adjusted_modmat=modmat.copy()
		adjusted_modmat-=np.diag(np.diag(np.sum(modmat,axis=0)))
		print np.diag(adjusted_modmat)
		print np.diag(modmat)
		print adjusted_modmat[:,0]


		#print np.shape(curgrp)
		grp1,grp2,eigvec=self.bipartition(adjusted_modmat,len(curgrp))
		
		print np.shape(grp1)
		print np.shape(grp2)
		print np.shape(eigvec)
		
		print eigvec
		#calculate delta-q
		dq=np.dot(np.dot(eigvec.T,adjusted_modmat),eigvec)
		print dq
		if dq>0 and not len(curgrp)<=7:
			modmat_grp1=np.delete(modmat,grp2,axis=0)
			modmat_grp1=np.delete(modmat_grp1,grp2,axis=1)
			print "grp1 modmat" + str(np.shape(modmat_grp1))
			self.recur_partition(modmat_grp1,grp1,curgrpinds[grp1])

			modmat_grp2=np.delete(modmat,grp1,axis=0)
			modmat_grp2=np.delete(modmat_grp2,grp1,axis=1)
			print "grp2 modmat" + str(np.shape(modmat_grp2))
			self.recur_partition(modmat_grp2,grp2,curgrpinds[grp2])
		else:
			print curgrp.T
			print np.shape(curgrp)
			self.ret_modules.append(curgrpinds.T)

		return 

	def bipartition(self,modmat,nr_nodes):
		if nr_nodes==0:
			return
		d,v=lin.eig(modmat)

		lambdamax=np.max(d)
		c=np.nonzero(d==lambdamax)

		#print nr_nodes
		#print np.shape(v[:,c])
		eigvec=np.reshape(v[:,c],(nr_nodes,))
		classify=np.sign(eigvec)
		classify[classify==0]=-1
		grp1=np.nonzero(classify==1)
		grp2=np.nonzero(classify==-1)
		grp1=np.array(grp1);grp1=grp1.T
		grp2=np.array(grp2);grp2=grp2.T
		return (grp1,grp2,classify)
