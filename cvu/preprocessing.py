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

from __future__ import division
import os
import mne
import parsing_utils as parse
from utils import CVUError

def loadmat(fname,field=None,is_adjmat=True):
    import numpy as np
    # well_formed numpy matrix
    if isinstance(fname, np.ndarray) or isinstance(fname, np.matrix):
        mat = fname

    # matlab
    elif fname.endswith('.mat'):
        if not field:
            raise CVUError("For .mat matrices, you must specify a field name")
        import scipy.io
        mat = scipy.io.loadmat(fname)[field]
        
    # numpy
    elif fname.endswith('.npy'):
        mat = np.load(fname)
    elif fname.endswith('.npz'):
        if not field:
            raise CVUError("For .npz matrices, you must specify a field name")
        mat = np.load(fname)[field]

    # other
    elif fname.endswith('.pkl'):
        raise IOError('Pickled matrices are not supported yet')
    elif fname.endswith('.txt'):
        mat = np.loadtxt(fname)
    else:
        raise IOError('File type not understood.  Only supported matrix '
            'formats are matlab and numpy.  File extensions are used to '
            'differentiate file formats and are not optional.')
        return

    if is_adjmat:
        if mat.ndim != 2 or mat.shape[0] != mat.shape[1]:
            raise CVUError('Adjacency matrix is not square')
        if not np.allclose(mat, mat.T):
            raise CVUError('Adjacency matrix is not symmetric')

    return mat

def loadsurf(*args,**kwargs):
    try:
        return loadsurf_mne(*args,**kwargs)
    except:
        return loadsurf_gifti(*args,**kwargs)

def loadannot(*args,**kwargs):
    try:
        return loadannot_mne(*args,**kwargs)
    except:
        #return loadannot_gifti(*args,**kwargs)
        raise

def read_ordering_file(fname):
    if isinstance(fname, list):
        labnam=[]
        deleters=[]
        for i,item in enumerate(fname): 
            if item=='delete':
                deleters.append(i)
            else:
                labnam.append(item)
        return labnam,deleters

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

def loadsurf_mne(fname,surftype,quiet=True):
    from dataset import SurfData
    sverts_lh,sfaces_lh=mne.surface.read_surface(parse.hemineutral(fname)%'lh')
    sverts_rh,sfaces_rh=mne.surface.read_surface(parse.hemineutral(fname)%'rh')
    return SurfData(sverts_lh,sfaces_lh,sverts_rh,sfaces_rh,surftype)

def loadannot_mne(p,subj,subjdir,labnam=None,surf_type='pial',surf_struct=None,
        quiet=False):

    verbosity = 'ERROR' if quiet else 'WARNING'

    if float(mne.__version__[:3]) >= 0.8:
        annot = mne.read_labels_from_annot(parc=p, subject=subj, 
            surf_name=surf_type, subjects_dir=subjdir, verbose=verbosity)
    else:
        annot = mne.labels_from_parc(parc=p, subject=subj, surf_name=surf_type,
            subjects_dir=subjdir, verbose=verbosity)
        annot = annot[0] #discard the color table
    return annot

def calcparc(labels,labnam,quiet=False,parcname=' ',subjdir='.',
        subject='fsavg5',lhsurf=None,rhsurf=None):
    #subjdir and subject are passed here in order to get subcortical
    #structures from a brain other than fsavg5
    import numpy as np
    lab_pos=np.zeros((len(labnam),3))
    #an nlogn sorting algorithm is theoretically possible here but rather hard
    labs_used=[]
    labv={} 

    # return just the vertices associated with the label.
    for lab in labels:
        try:
            i=labnam.index(parse.mangle_hemi(lab.name.lower()))
            labs_used.append(parse.mangle_hemi(lab.name.lower()))
            labv.update({lab.name.lower():lab.vertices})
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
                    try:
                        import nibabel as nib
                    except ImportError as e:
                        raise CVUError('Nibabel is required for handling of '
                            'parcellations with subcortical structures')
                    aseg=nib.load(os.path.join(subject,'mri','aseg.mgz'))
                    asegd=aseg.get_data()
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
            labnam=labnam,
            surf_type=params.surface_type,
            surf_struct=srf)
    except (IOError,ValueError) as e:
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
        try:
            if not params.adjmat:
                err_handler.error_dialog('You must specify the adjacency '
                    'matrix')
        except ValueError as e:     # the adjmat is a numpy ndarray
            pass                    # which has no single truth value
        
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
                'parcellation size is %i. This is probably because some regions '
                'in the adjmat ordering were not found in the parcellation.' % 
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
    #adj=adj[adj_ord][:,adj_ord]
    adj=adj[np.ix_(adj_ord,adj_ord)]
    #warn about the omitted entries
    if len(adj_ord)!=len(init_ord):
        for lab in init_ord:
            if lab not in labnam:
                print ("Warning: Label %s present in adjmat ordering %s "
                    "was not in the current parcellation. It was omitted." 
                    % (lab, adjlabfile))
    return adj

def match_gifti_intent(fname_stem, intent):
    ''' This function takes a stem of a filename, such as
        'lh.test.%sgii'. The format string is for the intent.
        This may be blank, or it may match the intent argument. '''

    intent = '%s.'%intent
    if os.path.exists(fname_stem%''):
        return fname_stem%''
    elif os.path.exists(fname_stem%intent):
        return fname_stem%intent
    else:
        raise ValueError("No GIFTI file %s with matching intent %s was found.\n"
            "This can be caused by intermixing freesurfer and GIFTI files (which cannot "
            "be done)"	%  (fname_stem%'',intent))

def loadannot_gifti(parcname, subject, subjects_dir, labnam=None, surf_type='pial',
        surf_struct=None, quiet=False):

    import numpy as np
    from nibabel import gifti

    fname = os.path.join(subjects_dir, subject, 'label', 'lh.%s.%sgii'%(parcname,'%s'))
    fname = match_gifti_intent(fname, 'label')

    annot_lh = gifti.read(parse.hemineutral(fname)%'lh')
    annot_rh = gifti.read(parse.hemineutral(fname)%'rh')
    
    #unpack the annotation data
    labdict_lh=parse.appendhemis(annot_lh.labeltable.get_labels_as_dict(),"lh_")
    labv_lh=map(labdict_lh.get,annot_lh.darrays[0].data)

    labdict_rh=parse.appendhemis(annot_rh.labeltable.get_labels_as_dict(),"rh_")
    labv_rh=map(labdict_rh.get,annot_rh.darrays[0].data)

    labv=labv_lh+labv_rh

    #return labv
    #The objective is now to create MNE label files for these on the fly

    vertices = np.vstack((surf_struct.lh_verts, surf_struct.rh_verts))
    mne_labels = []

    for lab in labnam:
        cur_lab_verts = np.flatnonzero(np.array(labv)==lab)
        cur_lab_pos = vertices[cur_lab_verts]

        cur_lab = mne.Label(cur_lab_verts, pos=cur_lab_pos/1000, hemi=lab[:2],
            name = parse.demangle_hemi(lab))
        mne_labels.append(cur_lab)
        
    return mne_labels	

def loadsurf_gifti(fname,surftype,quiet=True):
    from nibabel import gifti
    from dataset import SurfData
    fname = '%s.%sgii'%(fname,'%s')
    fname = match_gifti_intent(fname, 'surface')

    surf_lh = gifti.read(parse.hemineutral(fname)%'lh')
    surf_rh = gifti.read(parse.hemineutral(fname)%'rh')
    
    sverts_lh,sfaces_lh = surf_lh.darrays[0].data, surf_lh.darrays[1].data
    sverts_rh,sfaces_rh = surf_rh.darrays[0].data, surf_rh.darrays[1].data

    return SurfData(sverts_lh,sfaces_lh,sverts_rh,sfaces_rh,surftype)

#this function is deprecated
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
