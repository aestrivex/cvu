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

import os
import mne
import parsing_utils as parse
from utils import CVUError

def loadmat(fname,field=None):
	import numpy as np
	# matlab
	if fname.endswith('.mat'):
		if not field:
			raise CVUError("For .mat matrices, you must specify a field name")
		import scipy.io
		mat = scipy.io.loadmat(fname)[field]
		
	# numpy
	elif fname.endswith('.npy'):
		mat = np.load(fname)
	elif fname.endswith('.txt'):
		mat = np.loadtxt(fname)
	else:
		raise IOError('File type not understood.  Only supported matrix '
			'formats are matlab and numpy.  File extensions are used to '
			'differentiate file formats and are not optional.')
		return
	return mat

def read_ordering_file(fname):
	labnam=[]
	deleters=[]
	with open(fname,'r') as fd:
		i=0
		for line in fd:
			l=line.strip().lower()
			if l=='delete':
				deleters.append(i)
			else:
				labnam.append(l)
			i+=1

	#try to raise an exception if this is not a real text file
	try:
		str(unicode(labnam[0]))
	except UnicodeDecodeError as e:
		raise CVUError("This doesn't look like a text file: %s" % fname)
	except IndexError:
		raise CVUError('Ordering file %s is empty or has only deletes' % fname)

	return labnam,deleters

def loadsurf(fname,surftype):
	from dataset import SurfData
	surf_lh,sfaces_lh=mne.surface.read_surface(parse.hemineutral(fname)%'lh')
	surf_rh,sfaces_rh=mne.surface.read_surface(parse.hemineutral(fname)%'rh')
	return SurfData(surf_lh,sfaces_lh,surf_rh,sfaces_rh,surftype)

def loadannot(p,subj,subjdir,surf_type='pial'):
	annot=mne.labels_from_parc(parc=p,subject=subj,surf_name=surf_type,
		subjects_dir=subjdir,verbose=False)
	return annot[0]	#discard the color table

def calcparc(labels,labnam,quiet=False,parcname=' ',subjdir='.',
		subject='fsavg5',lhsurf=None,rhsurf=None):
	#subjdir and subject are passed here in order to get subcortical
	#structures from a brain other than fsavg5
	import numpy as np
	lab_pos=np.zeros((len(labnam),3))
	#an nlogn sorting algorithm is theoretically possible here but rather hard
	labs_used=[]
	labv={} 	# return the vertices associated with the label.
				# the label file has a lot more unneeded information than this.
	for lab in labels:
		try:
			i=labnam.index(parse.mangle_hemi(lab.name))
			labs_used.append(parse.mangle_hemi(lab.name))
			labv.update({lab.name:lab.vertices})
		except ValueError:
			if not quiet:
				print ("Label %s deleted as requested" % 
					lab.name)
			continue
		lab_pos[i,:]=np.mean(lab.pos,axis=0)
		#print lab.name,lab_pos[i,:]
	#the data seems to be incorrectly scaled by a factor of roughly 1000
	lab_pos*=1000
	
	import volume
	valid_subcortical_keys=volume.aseg_rois.keys()
	asegd=None

	for i,lab in enumerate(labnam):
		if lab not in labs_used:
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

	return lab_pos,labv

def adj_sort(adj_ord,desired_ord):
	if len(adj_ord) < len(desired_ord):
		raise CVUError('Parcellation order is larger than adjmat order.  Parc '
			'ordering has %i (non-delete) entries and adjmat order has %i ' %
			(len(adj_ord),len(desired_ord)))
	keys={}
	for i,k in enumerate(adj_ord):
		keys.update({k:i})	
	return map(keys.get,desired_ord)

	#this is purely wrong, just a bug.
	#at such time as cvu seems to work really well and it is even more obvious
	#this is a purely wrong bug, delete these lines
	#for i,k in enumerate(desired_ord):
	#	keys.update({k:i})
	#return map(keys.get,adj_ord)

#operates on a ParcellationChooserParameters
#the gui is passed in to provide direct error handling
def process_parc(params,err_handler):
	try:
		labnam,_ =  read_ordering_file(params.labelnames_file)
	except (IOError,CVUError) as e:
		err_handler.error_dialog(str(e)); return
	
	try:
		srf_file_lh = os.path.join(params.subjects_dir,params.subject,'surf',
			'lh.%s' % params.surface_type)
	except OSError as e:
		err_handler.error_dialog(str(e)); return

	try:
		srf = loadsurf(srf_file_lh, params.surface_type)
	except TypeError as e:
		err_handler.error_dialog(
			"%s: This doesn't look like a surface file" % srf_file_lh); return
	except IOError as e:
		err_handler.error_dialog(str(e)); return

	try:
		labels = loadannot(params.parcellation_name,
			params.subject, 
			params.subjects_dir,
			params.surface_type)
	except IOError as e:
		err_handler.error_dialog(str(e)); return

	try:
		lab_pos,labv = calcparc(labels,
			labnam,
			parcname=params.parcellation_name,
			subjdir=params.subjects_dir,
			subject=params.subject,
			lhsurf=srf.lh_verts, rhsurf=srf.rh_verts)
	except IOError as e:
		err_handler.error_dialog(str(e)); return

	return lab_pos,labnam,srf,labv,params.subject,params.parcellation_name

#operates on an AdjmatChooserParameters
#the gui is passed to provide direct error handling
def process_adj(params,err_handler):
		if not params.adjmat:
			err_handler.error_dialog('You must specify the adjacency matrix')
		
		try:
			adj=loadmat(params.adjmat,field=params.field_name)
		except (CVUError,IOError) as e:
			err_handler.error_dialog(str(e)); return
		except KeyError as e:
			err_handler.error_dialog('Field not found: %s' % str(e)); return

		if params.adjmat_order:
			adjlabfile=params.adjmat_order
			try:
				adj=flip_adj_ord(
					adj,adjlabfile,params.ds_ref.labnam,
					ign_dels=params.ignore_deletes)
			except CVUError as e:
				err_handler.error_dialog(str(e)); return
			except (ValueError,IndexError) as e:
				err_handler.error_dialog(
					'Mismatched channels: %s' % str(e)); return

		if params.max_edges > 0:
			soft_max_edges = params.max_edges
		else:
			soft_max_edges=20000

		if len(adj) != params.ds_ref.nr_labels:
			err_handler.error_dialog(
				'The adjmat specified is of size %i and the '
				'parcellation size is %i' % 
				(len(adj),params.ds_ref.nr_labels)); return
	
		return adj,soft_max_edges,params.adjmat

# acts on intermediate computation adjacency matrix, then given to instance
def flip_adj_ord(adj,adjlabfile,labnam,ign_dels=False):
	import numpy as np
	if adjlabfile == None or adjlabfile == '':
		return adj
	init_ord,bads=read_ordering_file(adjlabfile)
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

#BELOW THIS POINT ARE FUNCTIONS FOR PROCESSING GIFTI FILES WHICH IS DEPRECATED
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
