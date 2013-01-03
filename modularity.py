import numpy as np
import scipy.linalg as lin

threshold_p=.1

class Partitioner():

	def __init__(self,adjmat,nr_edges=0):
		self.adjmat=adjmat
		self.nr_nodes=len(self.adjmat)

	def threshold_prop(self):
		self.adjmat=np.triu(self.adjmat)
		asort = np.sort(self.adjmat.ravel())
		cutoff = asort[int((1-threshold_p/2)*len(asort))]
 		self.adjmat[self.adjmat<cutoff]=0
		self.adjmat=self.adjmat+self.adjmat.transpose()

	def partition(self):
		self.threshold_prop()
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
		print np.shape(startgrp)
		self.ret_modules = []

		self.recur_partition(self.modmat,startgrp,startgrp.copy())
		#print self.ret_modules
		#print self.ret_modules[0].dtype

		return self.ret_modules

	def recur_partition(self,modmat,curgrp,curgrpinds):
		adjusted_modmat=modmat.copy()
		adjusted_modmat-=np.diag(np.diag(np.sum(modmat,axis=0)))
		
		#print np.shape(curgrp)
		grp1,grp2,eigvec=self.bipartition(modmat,len(curgrp))
		
		#print np.shape(grp1)
		#print np.shape(grp2)
		#print np.shape(eigvec)

		#calculate delta-q
		dq=np.dot(np.dot(eigvec.T,adjusted_modmat),eigvec)
		print dq
		if dq>0:
			modmat_grp1=np.delete(modmat,grp2,axis=0)
			modmat_grp1=np.delete(modmat_grp1,grp2,axis=1)
			#print "grp1 modmat" + str(np.shape(modmat_grp1))
			self.recur_partition(modmat_grp1,grp1,curgrpinds[grp1])

			modmat_grp2=np.delete(modmat,grp1,axis=0)
			modmat_grp2=np.delete(modmat_grp2,grp1,axis=1)
			#print "grp2 modmat" + str(np.shape(modmat_grp2))
			self.recur_partition(modmat_grp2,grp2,curgrpinds[grp2])
		else:
			print curgrp.T
			#print np.shape(curgrp)
			self.ret_modules.append(curgrpinds.T)

		return 

	def bipartition(self,modmat,nr_nodes):
		d,v=lin.eig(modmat)

		lambdamax=np.max(d)
		c=np.nonzero(d==lambdamax)

		#print nr_nodes
		#print np.shape(v[:,c])
		eigvec=np.reshape(v[:,c],(nr_nodes,))
		classify=np.sign(eigvec)
		grp1=np.nonzero(classify==1)
		grp2=np.nonzero(np.logical_or(classify==-1,classify==0))
		grp1=np.array(grp1);grp1=grp1.T
		grp2=np.array(grp2);grp2=grp2.T
		return (grp1,grp2,eigvec)
