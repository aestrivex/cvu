def eqfun(x):
	return lambda y:y==x

def appendhemis(olddict,hemi):
	return dict(map(lambda (k,v):(k,hemi+str(v)),olddict.items()))

def loadmat(fname,field=None):
	import numpy as np
	# matlab
	if fname.endswith('.mat'):
		if not field:
			raise Exception("For .mat matrices, you must specify a field name")
		import scipy.io
		mat = scipy.io.loadmat(fname)[field]
		
		# TODO ask the developer/user to provide the right matrix rather than
		# assuming it needs to be averaged over
		if True:
			mat = np.mean(mat,axis=2)
	# numpy
	elif fname.endswith('.npy'):
		mat = np.load(fname)
	else:
		raise Exception('Only supported formats for matrix loading are matlab '
			'and numpy')
		#TODO raise this exception much earlier so that processing of surfaces is not done
	return mat
