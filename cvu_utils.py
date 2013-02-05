def eqfun(x):
	return lambda y:y==x

def appendhemis(olddict,hemi):
	return dict(map(lambda (k,v):(k,hemi+str(v)),olddict.items()))

def rreplace(s,old,new,occurrence):
	li=s.rsplit(old,occurrence)
	return new.join(li)

def mangle_hemi(s):
	return s[-2:]+'_'+s[0:-3]

def hemineutral(s):
	lhind=s.find('lh')
	rhind=s.find('rh')
	if lhind>rhind:
		return rreplace(s,'lh','%s',1)
	elif rhind>lhind:
		return rreplace(s,'rh','%s',1)
	else:
		return s

def loadmat(fname,field=None,avg=True):
	import numpy as np
	# matlab
	if fname.endswith('.mat'):
		if not field:
			raise Exception("For .mat matrices, you must specify a field name")
		import scipy.io
		mat = scipy.io.loadmat(fname)[field]
		
		# TODO ask the developer/user to provide the right matrix rather than
		# assuming it needs to be averaged over
		if avg:
			mat = np.mean(mat,axis=2)
	# numpy
	elif fname.endswith('.npy'):
		mat = np.load(fname)
	else:
		raise IOError('File type not understood.  Only supported matrix'
			' formats are matlab and numpy.  File extensions not optional.')
		return
	return mat

def read_parcellation_textfile(fname):
	labnam=[]
	fd = open(fname,'r')
	for line in fd:
		l=line.strip()
		if l=='delete':
			continue
		labnam.append(l)
	return labnam

def loadannot(p,subj,subjdir):
	import mne
	annot=mne.labels_from_parc(parc=p,subject=subj,#surf_name='pial'
		subjects_dir=subjdir,verbose=False)
	return annot

def loadsurf(fname):
	import mne
	surf_lh,sfaces_lh=mne.surface.read_surface(hemineutral(fname)%'lh')
	surf_rh,sfaces_rh=mne.surface.read_surface(hemineutral(fname)%'rh')
	return (surf_lh,sfaces_lh,surf_rh,sfaces_rh)

def calcparc(labv,labnam,quiet=False):
	import numpy as np
	lab_pos=np.zeros((len(labnam),3))
	#an nlogn sorting algorithm is theoretically possible here but rather hard
	for lab in labv[0]:
		try:
			i=labnam.index(mangle_hemi(lab.name))
		except ValueError:
			continue
		lab_pos[i,:]=np.mean(lab.pos,axis=0)
	lab_pos*=1000
	#the data seems to be incorrectly scaled by a factor of 1000
	return lab_pos

#functions operating on GIFTI annotations are deprecated
def loadannot_gifti(fname):
	import nibabel.gifti
	annot_lh=nibabel.gifti.read(hemineutral(fname)%'lh')
	annot_rh=nibabel.gifti.read(hemineutral(fname)%'rh')
	
	#unpack the annotation data
	labdict_lh=appendhemis(annot_lh.labeltable.get_labels_as_dict(),"lh_")
	labv_lh=map(labdict_lh.get,annot_lh.darrays[0].data)

	labdict_rh=appendhemis(annot_rh.labeltable.get_labels_as_dict(),"rh_")
	labv_rh=map(labdict_rh.get,annot_rh.darrays[0].data)

	labv=labv_lh+labv_rh
	return labv

def calcparc_gifti(labnam,labv,surf_struct,quiet=False):
	import numpy as np
	# define constants and reshape surfaces
	vert = np.vstack((surf_struct[0],surf_struct[2]))

	nr_labels = len(labnam)
	nr_verts = len(labv)

	if nr_verts != len(vert):
		print nr_verts
		print len(vert)
		raise Exception('Parcellation has inconsistent number of vertices')
	if not quiet:
		print 'Surface has '+str(nr_verts)+' vertices'
		print ('Parcellation has '+str(nr_labels)+' labels (before bad channel'
			' removal)')

	lab_pos = np.zeros((nr_labels,3))

	## CHECK FOR BAD CHANNELS AND DEFINE LABEL LOCATIONS AS VERTEX AVERAGES ##
	bad_labs=[]
	deleters=[]

	for i in xrange(0,nr_labels,1):
		if labnam[i]=='delete':
			deleters.append(i)
			continue
		curlab=np.flatnonzero(np.array(map(eqfun(labnam[i]),labv)))
		if len(curlab)==0:
			print ("Warning: label "+labnam[i]+' has no vertices in it.  This '
				'channel will be deleted')
			bad_labs.append(i)
			continue
		if not quiet:
			print "generating coordinates for "+labnam[i]
		lab_pos[i] = np.mean(vert[curlab],axis=0)

		## DELETE THE BAD CHANNELS ##
	if len(deleters)>0:
		print "Removed "+str(len(deleters))+" bad channels"
		lab_pos=np.delete(lab_pos,deleters,axis=0)
		labnam=np.delete(labnam,deleters,axis=0)
		nr_labels-=len(deleters)
	else:
		print "No bad channels"

	if (len(bad_labs)>0):
		lab_pos=np.delete(lab_pos,bad_labs,axis=0)
		labnam=np.delete(labnam,bad_labs,axis=0)
		nr_labels-=len(bad_labs)

	return lab_pos

def file_chooser(main_window):
	from Tkinter import Tk
	Tk().withdraw()
	from tkFileDialog import askopenfilename
	return askopenfilename()

def fancy_file_chooser(main_window):
	from traits.api import HasPrivateTraits,File,Str,on_trait_change
	from traitsui.api import View,Item,FileEditor,OKCancelButtons

	class FileChooserWindow(HasPrivateTraits):
		f=File
		_fn=Str
		traits_view=View(
			Item(name='_fn',show_label=False),
			Item(name='f',editor=FileEditor(),style='custom',
				height=500,width=500,show_label=False),
			buttons=OKCancelButtons,kind='nonmodal',
			title="This should be extremely inconvenient")

		@on_trait_change('_fn')
		def f_chg(self):
			self.f=self._fn
	
	main_window.file_chooser_window=FileChooserWindow()
	main_window.file_chooser_window.edit_traits()

def parcellation_chooser(main_window):
	from traits.api import HasTraits,Directory,Str,File,on_trait_change
	from traitsui.api import View,Item,DirectoryEditor,OKCancelButtons,Group,\
		Handler

	class ParcellationChooserWindowHandler(Handler):
		def closed(self,info,is_ok):
			main_window.labelnames_f=info.object.label_ord
			main_window.parcname=info.object.parcellation
			main_window.subject=info.object.SUBJECT
			main_window.subjects_dir=info.object.SUBJECTS_DIR
			main_window.parc_chooser_window_finished=is_ok

	class ParcellationChooserWindow(HasTraits):
		Please_note=Str('Unless you are specifically interested in the'
			' morphology of an individual subject, it is recommended to use'
			' fsaverage5 and leave the first two fields alone.')
		SUBJECTS_DIR=Directory('./')
		SUBJECT=Str('fsavg5')
		#label_ord=File('order_sparc')
		label_ord=File
		parcellation=Str

		traits_view=View(
			Group(
				Item(name='Please_note',style='readonly',height=85,width=250),
				Item(name='SUBJECT'),
				Item(name='SUBJECTS_DIR'),
				Item(name='parcellation',label='Parcellation'),
				Item(name='label_ord',label='Label Order'),
			), kind='nonmodal',buttons=OKCancelButtons,
				handler=ParcellationChooserWindowHandler(),
				title="This should not be particularly convenient",)
		
	ParcellationChooserWindow().edit_traits()

def error_dialog(message="Error!"):
	from traits.api import HasTraits,Str
	from traitsui.api import View,Item,TextEditor,OKButton

	class ErrorDialogWindow(HasTraits):
		error=Str
		traits_view=View(Item(name='error',editor=TextEditor(),
			style='readonly'),
			buttons=[OKButton],kind='nonmodal',
			title='This should be convenient, but only slightly',)
		def _error_default(self):
			return message

	ErrorDialogWindow().edit_traits()

def usage():
	print 'Command line arguments are as follows:\n'+\
		'-p greg.gii --parc=greg: location of annotations *h.greg.annot\n'+\
		'-a greg.mat --adjmat=greg.mat: location of adjacency matrix\n'+\
		'-d greg.nii --subjects-dir=greg/: specifies SUBJECTS_DIR\n'+\
		'-s greg --surf=greg: loads the surface *h.greg\n'+\
		'-o greg.txt --order=greg.txt: loads text file with label order\n'+\
		'--surf-type=pial: specifies type of surface.  pial is used by '+\
		'default\n'+\
		'-q: specifies quiet flag\n'+\
		'-v: specifies verbose flag (currently does nothing)\n'+\
		'--use-greg: uses the "greg" method for graph partitioning.  valid '+\
		'choices are: --use-spectral, --use-metis\n'+\
		'-h --help: display this help'
	exit(78)

def cli_args(argv,):
	import getopt; import os
	subjdir=None;adjmat=None;parc=None;parcfile=None;surftype=None;
	field=None;dataloc=None;modality=None;partitiontype=None;
	subject=None;maxedges=None;quiet=False
	try:
		opts,args=getopt.getopt(argv,'p:a:s:o:qd:hvf:',
			["parc=","adjmat=","adj=","modality=","data=","datadir="\
			"surf=","order=","surf-type=","parcdir=","use-metis",
			"use-spectral","help","field=","subjects-dir=","subject=",
			"max-edges="])
	except getopt.GetoptError as e:
		print "Argument %s" % str(e)
		usage()
	for opt,arg in opts:
		if opt in ["-p","--parc"]:
			parc = arg
		elif opt in ["-a","--adjmat","--adj"]:
			adjmat = arg
		elif opt in ["-d","--data","--datadir","--subjects-dir","--parcdir"]:
			subjdir = arg
		elif opt in ["-o","--order"]:
			parcfile = arg
		elif opt in ["-s","--surf","--surf-type"]:
			surftype = arg
		elif opt in ["--subject"]:
			subject = arg
		elif opt in ["-q"]:
			quiet=True
		elif opt in ["-v"]:
			pass
		elif opt in ["--modality"]:
			modality=arg.lower()
		elif opt in ["--use-metis"]:
			partitiontype="metis"
		elif opt in ["--use-spectral"]:
			partitiontype="spectral"
		elif opt in ["-h","--help"]:
			usage()
		elif opt in ["-f","--field"]:
			field=arg
		elif opt in ["--max-edges"]:
			maxedges=arg
	if not subjdir:
		subjdir = './'
	if not adjmat:
		adjmat = '/autofs/cluster/neuromind/rlaplant/pdata/adjmats/pliA1.mat'
	if not parc:
		parc = 'sparc'
	if not parcfile:
		if parc != 'sparc':
			raise Exception('A text file containing channel names must be'
				' supplied with your parcellation')
		else:
			parcfile='order_sparc'
	if modality not in ["meg","fmri","dti",None]:
		raise Exception('Modality %s is not supported' % modality)
	if modality in ["fmri","dti"]:
		raise Exception('Modality %s is not yet supported' % modality)
	if not surftype:
		surftype='pial'
	if not subject:
		subject='fsavg5'
	if not partitiontype:
		partitiontype="spectral"
	if not field:
		field="adj_matrices"
	if not maxedges:
		maxedges=20000
	if not os.path.isfile(parcfile):
		raise Exception('Channel names not found')
	if not os.path.isfile(adjmat):
		raise Exception('Adjacency matrix not found')
	if not os.path.isdir(subjdir):
		raise Exception('SUBJECTS_DIR not found')
	return {'parc':parc,'adjmat':adjmat,'parcfile':parcfile,'modality':modality\
		,'surftype':surftype,'partitiontype':partitiontype,'quiet':quiet,\
		'dataloc':dataloc,'field':field,'subjdir':subjdir,\
		'subject':subject,'maxedges':maxedges}
