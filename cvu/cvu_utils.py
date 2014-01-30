#    (C) Roan LaPlante 2013 rlaplant@nmr.mgh.harvard.edu
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

from traits.api import HasTraits,Event
import os

class EventHolder(HasTraits):
	e=Event

def eqfun(x):
	return lambda y:y==x

def appendhemis(olddict,hemi):
	return dict(map(lambda (k,v):(k,hemi+str(v)),olddict.items()))

def rreplace(s,old,new,occurrence):
	li=s.rsplit(old,occurrence)
	return new.join(li)

def hemineutral(s):
	lhind=s.find('lh')
	rhind=s.find('rh')
	if lhind>rhind:
		return rreplace(s,'lh','%s',1)
	elif rhind>lhind:
		return rreplace(s,'rh','%s',1)
	else:
		return s

def str2intlist(s):
	import re
	return re.split(',| |;',s.strip('[]'))

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
		if avg and hasattr(mat,'ndim') and mat.ndim==3:
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
	deleters=[]
	fd = open(fname,'r')
	i=0
	for line in fd:
		l=line.strip()
		if l=='delete':
			deleters.append(i)
		else:
			labnam.append(l)
		i+=1
	return labnam,deleters

def loadannot(p,subj,subjdir,surf_type='pial'):
	import mne
	annot=mne.labels_from_parc(parc=p,subject=subj,surf_name=surf_type,
		subjects_dir=subjdir,verbose=False)
	return annot

def loadsurf(fname,surftype):
	import mne
	surf_lh,sfaces_lh=mne.surface.read_surface(hemineutral(fname)%'lh')
	surf_rh,sfaces_rh=mne.surface.read_surface(hemineutral(fname)%'rh')
	return (surf_lh,sfaces_lh,surf_rh,sfaces_rh,surftype)

def mangle_hemi(s):
	return s[-2:]+'_'+s[0:-3]

def calcparc(labv,labnam,quiet=False,parcname=' ',subjdir='.',subject='fsavg5',
		lhsurf=None,rhsurf=None):
	#subjdir and subject are passed here in order to get subcortical
	#structures from a brain other than fsavg5
	import numpy as np
	lab_pos=np.zeros((len(labnam),3))
	#an nlogn sorting algorithm is theoretically possible here but rather hard
	labs_used=[]
	labv_ret=[] # for returning only the used labels
	for lab in labv[0]:
		try:
			i=labnam.index(mangle_hemi(lab.name))
			labs_used.append(mangle_hemi(lab.name))
			labv_ret.append(lab)
		except ValueError:
			if not quiet:
				print ("Label %s deleted as requested" % 
					lab.name)
			continue
		lab_pos[i,:]=np.mean(lab.pos,axis=0)
	#the data seems to be incorrectly scaled by a factor of roughly 1000
	lab_pos*=1000
	
	import volume
	valid_subcortical_keys=volume.aseg_rois.keys()
	asegd=None

	for i,lab in enumerate(labnam):
		if lab not in labs_used:
			#TODO get subcortical labels from the volume file
			if lab in valid_subcortical_keys:
				if asegd is None:
					import nibabel
					#import time
					#t1=time.clock()
					aseg=nibabel.load(os.path.join(subject,'mri','aseg.mgz'))
					asegd=aseg.get_data()
					#t2=time.clock()
					#print t2-t1
				lab_pos[i,:] = volume.roi_coords(lab,asegd,subjdir=subjdir,
					subject=subject,lhsurf=lhsurf,rhsurf=rhsurf)
			#let the user know if parc order file has unrecongized entries
			elif not quiet:
				print ("Warning: Label %s not found in parcellation %s" % 
					(lab,parcname))


	return lab_pos,labv_ret

class CVUError(Exception):
	pass

def adj_sort(adj_ord,desired_ord):
	#if len(adj_ord) != len(desired_ord):
	#	raise CVUError('Parcellation and adjmat label orderings do not match.  '
	#		'Parc lab_ord has %i non-delete entries, adj lab_ord %i non-delete '			
	#		'entries' % (len(adj_ord),len(desired_ord)))
	if len(adj_ord) < len(desired_ord):
		raise CVUError('Parcellation order is larger than adjmat order.  Parc '
			'ordering has %i (non-delete) entries and adjmat order has %i ' %
			(len(adj_ord),len(desired_ord)))
	keys={}
	for i,k in enumerate(desired_ord):
		keys.update({k:i})
	#return sorted(adj_ord,key=keys.get)
	return map(keys.get,adj_ord)
		
# acts on intermediate computation adjacency matrix, then given to instance
def flip_adj_ord(adj,adjlabfile,labnam,ign_dels=False):
	import numpy as np
	if adjlabfile == None or adjlabfile == '':
		return adj
	init_ord,bads=read_parcellation_textfile(adjlabfile)
	#delete the extras
	if not ign_dels:
		adj=np.delete(adj,bads,axis=0)
		adj=np.delete(adj,bads,axis=1)
	#if adj ordering is a different size than the new adjmat, we can't
	#possibly know how to fix it.  crash outright.
	if len(init_ord) != len(adj):
		raise CVUError('The adjmat ordering file %s has %i entries '
			'after deletions, but the adjmat specified has %i regions.'
			 % (adjlabfile,len(init_ord),len(adj)))
	adj_ord=adj_sort(init_ord,labnam)
	#get rid of the None items, regions not in parc ordering	
	ord_extras_rm=np.ma.masked_equal(adj_ord,None)
	adj_ord=np.array(ord_extras_rm.compressed(),dtype=int)
	#swap the new order
	adj=adj[adj_ord][:,adj_ord]
	#warn about the omitted entries
	if len(adj_ord)!=len(init_ord):
		for lab in init_ord:
			if lab not in labnam:
				print ("Warning: Label %s present in adjmat ordering %s "
					"was not in the current parcellation. It was omitted." 
					% (lab, adjlabfile))
	return adj

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
		raise CVUError('Parcellation has inconsistent number of vertices')
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

# FILE CHOOSER functions are not currently used.  There are some bugs in
# handling of file viewers in traitsui (and probably also enaml).  Also the
# default custom file selector in traitsui is really annoying.  At some point
# it may be convenient to make a wx file editor that works. 
def file_chooser(**kwargs):
	# use kwarg initialdir='/some_path'
	from Tkinter import Tk
	Tk().withdraw()
	from tkFileDialog import askopenfilename
	return askopenfilename(**kwargs)

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

def sh_cmd(cmd):
	import subprocess; import os
	with open(os.devnull,'wb') as devnull:
		try:
			subprocess.check_call(cmd,#stdout=devnull,stderr=subprocess.STDOUT,
				shell=True)
		except subprocess.CalledProcessError as e:
			raise CVUError(str(e))	

def sh_cmd_grep(cmd,grep):
	#this function is inspired by a similar function from connectomemapper
	import subprocess; import os; import random; import time; import tempfile
	t=random.randint(1,10000000)
	try: os.mkdir(os.path.join(tempfile.gettempdir(),'cvu'))
	except OSError: pass
	fname=os.path.join(tempfile.gettempdir(),"out_fifo_%s" % str(t))

	try: os.unlink(fname)
	except: pass

	retln=[]
	os.mkfifo(fname)
	try:
		fifo=os.fdopen(os.open(fname,os.O_RDONLY|os.O_NONBLOCK))
		newcmd="( %s ) 1>%s"%(cmd,fname)
		process=subprocess.Popen( newcmd, shell=True, stdout=subprocess.PIPE,
			stderr=subprocess.PIPE )
		
		while process.returncode == None:
			time.sleep(.5)
			process.poll()
			try:
				ln=fifo.readline().strip()
			except: continue
			if ln and grep in ln:
				retln.append(ln)
		rem=fifo.read()
		if rem:
			for ln in [ln for ln in rem.split('\n') if ln.strip()]:
				if grep in ln:
					retln.append(ln)
		if process.returncode:
			raise CVUError('%s failed with error code %s' % 
				(cmd,process.returncode))	
	finally:
		try: os.unlink(fname)
		except: pass
		return retln

def sh_cmd_retproc(cmd):
	import subprocess; import os
	with open(os.devnull,'wb') as devnull:
		process=subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,
			stdout=devnull,stderr=devnull)
		#checks to see if the specified command was bad
		if process.poll():
			process.kill()
			raise CVUError('% failed with error code %s' % 
				(cmd,process.returncode))
		return process

def tcsh_env_interpreter(source_fname):
	import subprocess; import os
	
	cmd=['tcsh','-c','source %s && env' % source_fname]

	proc = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=False)
	for ln in proc.stdout:
		ln=ln.strip()
		k,_,v=ln.partition("=")
		os.environ[k]=v

	#proc.communicate()

def usage():
	print ('Command line arguments are as follows:\n'
		'-p greg.gii --parc=greg: location of annotations *h.greg.annot\n'
		'-a greg.mat --adjmat=greg.mat: location of adjacency matrix\n'
		'-d greg.nii --subjects-dir=greg/: specifies SUBJECTS_DIR\n'
		'-s greg --surf=greg: loads the surface *h.greg\n'
		'-o greg.txt --order=greg.txt: location of text file with label order\n'
		'--surf-type=pial: specifies type of surface.  pial is used by '
		'default\n'
		'-q: specifies quiet flag\n'
		'-v: specifies verbose flag (currently does nothing)\n'
		'--use-greg: uses the "greg" method for graph partitioning.  this is '
		'pointless currently; the only choice is use-spectral'
		'--max-edges 46000: discards all but the strongest ~46000 connections\n'
		'-f greg --field greg: uses the "greg" field of a .mat matrix for the '
		'initial adjmat\n'
		'-h --help: display this help')
	exit(78)

def cli_args(argv,):
	import getopt; import os
	subjdir=None;adjmat=None;parc=None;parcorder=None;surftype=None;
	field=None;dataloc=None;modality=None;partitiontype=None;
	subject=None;maxedges=None;adjorder=None;quiet=False
	try:
		opts,args=getopt.getopt(argv,'p:a:s:o:qd:hvf:',
			["parc=","adjmat=","adj=","modality=","data=","datadir="\
			"surf=","order=","surf-type=","parcdir=",
			"use-spectral","help","field=","subjects-dir=","subject=",
			"max-edges=","adj-order="])
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
			parcorder = arg
		elif opt in ["--adj-order"]:
			adjorder = arg
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
		elif opt in ["--use-spectral"]:
			partitiontype="spectral"
		elif opt in ["-h","--help"]:
			usage()
		elif opt in ["-f","--field"]:
			field=arg
		elif opt in ["--max-edges"]:
			maxedges=arg
	if not subjdir:
		subjdir = os.path.dirname(__file__)
	if not adjmat:
		adjmat = 'data/sample_data.npy'
	if not parc:
		parc = 'sparc'
	if not parcorder:
		if parc != 'sparc':
			raise Exception('A text file containing channel names must be'
				' supplied with your parcellation')
		else:
			#TODO export this design pattern for relative paths where necessary
			parcorder=os.path.join(os.path.dirname(__file__),
				'orders','sparc.txt')
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
	if not maxedges:
		maxedges=20000
	if not os.path.isfile(parcorder):
		raise Exception('Channel names %s file not found' % parcorder)
	if not os.path.isfile(adjmat):
		raise Exception('Adjacency matrix %s file not found' % adjmat)
	if not os.path.isdir(subjdir):
		raise Exception('SUBJECTS_DIR %s file not found' % subjdir)
	if adjorder and os.path.isfile(adjorder):
		raise Exception('Adjancency matrix order %s file not found' % adjorder)
	return {'parc':parc,'adjmat':adjmat,'parcorder':parcorder,
		'modality':modality,\
		'surftype':surftype,'partitiontype':partitiontype,'quiet':quiet,\
		'dataloc':dataloc,'field':field,'subjdir':subjdir,\
		'subject':subject,'maxedges':maxedges,'adjorder':adjorder}
