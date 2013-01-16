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

def file_chooser(main_window):
	from Tkinter import Tk
	Tk().withdraw()
	from tkFileDialog import askopenfilename
	return askopenfilename()

def fancy_file_chooser(main_window):
	from enthought.traits.api import HasTraits,File,List,on_trait_change
	from enthought.traits.ui.api import View,Item,FileEditor,OKCancelButtons

	class FileChooserWindow(HasTraits):
		f=File
		traits_view=View(Item(name='f',editor=FileEditor(),style='custom',
			height=500,width=500,show_label=False),
			buttons=OKCancelButtons,kind='nonmodal')

	main_window.file_chooser_window=FileChooserWindow()
	main_window.file_chooser_window.edit_traits()
