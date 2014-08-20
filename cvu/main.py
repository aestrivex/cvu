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

#TODO handle command line arguments

from gui import CvuGUI,ErrorHandler
import sys
import os
import getopt
import signal
import numpy as np
from utils import CVUError

def usage():
    print ('Command line arguments are as follows:\n'
        '-p greg.gii --parc=greg: location of annotations *h.greg.annot\n'
        '-a greg.mat --adjmat=greg.mat: location of adjacency matrix\n'
        '-d greg.nii --subjects-dir=greg/: specifies SUBJECTS_DIR\n'
        '-s greg --surf=greg: loads the surface *h.greg\n'
        '-o greg.txt --order=greg.txt: specify the visualization order\n'
        '--surf-type=pial: specifies type of surface.  pial is used by'
        '\tdefault\n'
        '-q: specifies quiet flag\n'
        '-v: specifies verbose flag (currently does nothing)\n'
        '--max-edges 46000: discards all but the strongest ~46000 connections\n'
        '-f greg --field greg: uses the "greg" field of a .mat matrix for the '
        '\tinitial adjmat\n'
        '--adj-order greg: specify the adjmat order\n'
        '-h --help: display this help')
    exit(78)

def cli_args(argv):
    import getopt; import os
    adjmat_location=None; parcellation_name=None; subject_name=None;
    subjects_dir=None; parcellation_order=None; adjmat_order=None; 
    surface_type=None; field_name=None; max_edges=None; quiet=False;
    script=None

    #check for passed arguments
    try:
        opts,args=getopt.getopt(argv,'p:a:s:o:qd:hvf:',
            ["parc=","adjmat=","adj=","data=","datadir="\
            "surf=","order=","surf-type=","parcdir=",
            "help","field=","subjects-dir=","subject=",
            "max-edges=","max_edges","adj-order=","adj_order=",
            "script="])
    except getopt.GetoptError as e:
        print "Argument %s" % str(e)
        usage()
    for opt,arg in opts:
        if opt in ["-p","--parc"]:
            parcellation_name = arg
        elif opt in ["-a","--adjmat","--adj"]:
            adjmat_location = arg
        elif opt in ["-d","--data","--datadir","--subjects-dir","--parcdir"]:
            subjects_dir = arg
        elif opt in ["-o","--order"]:
            parcellation_order = arg
        elif opt in ["--adj-order","--adj_order"]:
            adjmat_order = arg
        elif opt in ["-s","--surf","--surf-type"]:
            surface_type = arg
        elif opt in ["--subject"]:
            subject_name = arg
        elif opt in ["-q"]:
            quiet = True
        elif opt in ["-v"]:
            pass
        elif opt in ["-h","--help"]:
            usage()
            sys.exit(0)
        elif opt in ["-f","--field"]:
            field_name = arg
        elif opt in ["--max-edges","--max_edges"]:
            max_edges = arg
        elif opt in ["--script"]:
            script = arg

    #assign default values
    if subjects_dir is None:
        subjects_dir = os.path.dirname(os.path.abspath(__file__))
    if adjmat_location is None:
        adjmat_location = 'data/sample_data.npy'
    if parcellation_name is None:
        parcellation_name = 'sparc'
    if parcellation_order is None:
        if parcellation_name != 'sparc':
            raise CVUError('A text file containing channel names must be'
                ' supplied with your parcellation')
        else:
            #TODO export this design pattern for relative paths where necessary
            parcellation_order=os.path.join(subjects_dir,'orders','sparc.txt')
    if surface_type is None:
        surface_type='pial'
    if subject_name is None:
        subject_name='fsavg5'
    if max_edges is None:
        max_edges=20000
    if not os.path.isfile(parcellation_order):
        raise CVUError('Channel names %s file not found' % parcorder)
    if not os.path.isfile(adjmat_location):
        raise CVUError('Adjacency matrix %s file not found' % adjmat)
    if not os.path.isdir(subjects_dir):
        raise CVUError('SUBJECTS_DIR %s file not found' % subjects_dir)
    if adjmat_order and not os.path.isfile(adjmat_order):
        raise CVUError('Adjancency matrix order %s file not found' % adjorder)

    return {'parc':parcellation_name,	'adjmat':adjmat_location,
        'subject':subject_name,			'subjdir':subjects_dir,
        'parcorder':parcellation_order,	'adjorder':adjmat_order,
        'surftype':surface_type,		'maxedges':max_edges,
        'field':field_name,				'quiet':quiet,
        'script':script}

#this reproduces work done in preprocessing that operates on a Parameters
#object that didn't exist yet.  That it didn't exist is bad design but there
#is no reason to change it now.
def preproc(args):
    import preprocessing as pp

    #load label names from specified text file for ordering
    labnam,_ = pp.read_ordering_file(args['parcorder'])
    
    #load adjacency matrix and put entries in order of labnam
    adj = pp.loadmat(args['adjmat'],args['field']) 
    adj = pp.flip_adj_ord(adj, args['adjorder'], labnam)

    #load surface for visual display
    surf_fname = os.path.join(
        args['subjdir'],args['subject'],'surf','lh.%s'%args['surftype'])
    srf=pp.loadsurf(surf_fname,args['surftype'])

    #load parcellation and vertex positions
    labels = pp.loadannot(
        args['parc'], args['subject'], args['subjdir'], labnam=labnam,
        surf_type=args['surftype'], surf_struct=srf, quiet=args['quiet'])

    #calculate label positions from vertex positions
    if args['subject']=='fsavg5':
        lab_pos,labv = pp.calcparc(labels,labnam,quiet=args['quiet'],
            parcname=args['parc'])
    else:
        lab_pos,labv = pp.calcparc(labels,labnam,quiet=args['quiet'],
            parcname=args['parc'],subjdir=args['subjdir'],
            subject=args['subject'],
            lhsurf=srf.lh_verts,rhsurf=srf.rh_verts)

    dataset_name='sample_data'

    from utils import DisplayMetadata	
    sample_metadata=DisplayMetadata(subject_name=args['subject'],
        parc_name=args['parc'],adj_filename=args['adjmat'])

    from dataset import Dataset
    sample_dataset=Dataset(dataset_name,lab_pos,labnam,srf,labv,
        adj=adj,soft_max_edges=args['maxedges'],
        gui=ErrorHandler(args['quiet']))
    # pass an ErrorHandler as the current GUI to handle errors. Replace it later.
    # Package dataloc and modality into tuple for passing

    exec_script = args['script']
    
    return sample_dataset,sample_metadata,exec_script

def main():
    #read the command line arguments or fetch the default values
    args=cli_args(sys.argv[2:])

    #generate the initial dataset
    #TODO collect the "name" of the sample dataset on the command line
    
    sample_dataset,sample_metadata,exec_script=preproc(args)
    
    g=CvuGUI(sample_dataset,sample_metadata,quiet=args['quiet'])
    sample_dataset.gui=g

    #Qt does not sys.exit in response to KeyboardInterrupt
    #we intercept KeyboardInterrupts in the interpreter, before even
    #reaching the Qt event loop and force them to call sys.exit
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    if exec_script is not None:
        from pyface.api import GUI
        gui=GUI()

        def run_script():
            gui.process_events()
            script(exec_script, cvu_gui=g, scriptdir=sys.argv[1])

        gui.invoke_later(run_script)

    g.configure_traits()

### scripting functions

def script(file, cvu_gui=None, scriptdir=os.getcwd()):
    '''
Execute a script in the context of a CVUGui object.

Arguments:  file: path to a script file containing commands to be executed
                serially
            scriptdir: working directory of the script's execution. Default
                value is /path/to/cvu/cvu
    '''
    curdir=os.getcwd()
    os.chdir(scriptdir)
    file=os.path.abspath(file)
    os.chdir(curdir)
    #print globals()['self']
    #self = cvu_gui
    with open(file) as fd: exec(fd)

def load_parc(parcellation, ordering, new_dataset=False, dataset_name = None,
        dataset=None,
        subjects_dir='.', subject='fsavg5', surface_type='pial'):
    '''
    Loads a parcellation, either onto a dataset or creating a new dataset.
    This function is a scripting helper. In other words,
    instead of clicking on the GUI or simulating button presses, this
    function is provided for scripting purposes to just simulate the
    process of loading a parcellation.

    Parameters
    ----------

    parcellation : str
        The parcellation name. For instance, if your parcellation's annotation
        files are called lh.aparc.annot, the parcellation name is 'aparc'.
        Similarly if the annotation file is called lh.aparc.gii, enter 'aparc'.
    ordering : str | list(str)
        The name of a text file containing the parcellation ordering.
        Alternately, a list of label names.
    new_dataset : bool
        If True, spawns a new dataset instead of placing the parcellation on
        an existing dataset. Default value is False.
    dataset_name : str | None
        Required if and only if new_dataset is True.
        If new_dataset is True, specifies the name of the new dataset.
        Otherwise, has no effect.
    dataset : instance(cvu.dataset.Dataset) | None
        Required if and only if new_dataset is False.
        If new_dataset is False, specifies the dataset onto which to load this
        parcellation. If new_dataset is True, has no effect.
    subjects_dir : str
        The superordinate directory used to load the annotation, surface,
        and segmentation files at $SUBJECTS_DIR/$SUBJECT/{surf|label|mri}/* .
        The default value is '.', the current working directory. Under
        normal circumstances this is the working directory relative to cvu's
        main.py file, which is /path/to/cvu/cvu.
    subject : str
        The subject name used to load the annotation, surface, and segmentation
        files at $SUBJECTS_DIR/$SUBJECT/{surf|label|mri}/*
        The default value is 'fsavg5'. Some files for fsavg5 are provided in
        the cvu installation.
    surface_type
        The surface to load. The default value is 'pial'.

    Returns
    -------
    dataset : instance(cvu.dataset.Dataset)
        The instance of the dataset now holding this parcellation. Helpful
        if new_dataset is True.
    '''
    gui = globals()['self']        #explicitly allow dynamic scope
    err_handler = ErrorHandler(quiet=True)

    from preprocessing import process_parc
    from options_struct import ParcellationChooserParameters
    from utils import DisplayMetadata
    from dataset import Dataset

    if new_dataset and dataset_name is None:
        print "Must specify a dataset name!"
        return
    elif new_dataset and dataset_name in gui.controller.ds_instances:
        print "Dataset name is not unique"
        return
    elif not new_dataset and not isinstance(dataset, Dataset):
        print "Must either supply an existing dataset or create a new one"
        return

    parc_params = ParcellationChooserParameters( ds_ref = dataset,
        new_dataset = new_dataset,
            new_dataset_name = dataset_name if dataset_name is not None else '',
        subjects_dir = subjects_dir,
        subject = subject, surface_type = surface_type, 
        labelnames_file = ordering, parcellation_name = parcellation)
    parc_struct = process_parc(parc_params, err_handler)
    if parc_struct is None: return #preprocessing errored out

    lab_pos, labnam, srf, labv, _, _ = parc_struct
    if new_dataset:
        display_metadata = DisplayMetadata(subject_name = subject,
            parc_name = parcellation, adj_filename='')
        dataset = Dataset(dataset_name, lab_pos, labnam, srf, labv, gui=gui)
        gui.controller.add_dataset(dataset, display_metadata)

    else:
        from viewport import Viewport

        dataset._load_parc(lab_pos, labnam, srf, labv)
        gui.controller.update_display_metadata(dataset.name, 
            subject_name = subject, parc_name = parcellation)

        #update the viewports associated with this dataset
        ds_interface = gui.controller.find_dataset_views(dataset)
        ds_interface.mayavi_port = Viewport(dataset)
        ds_interface.matrix_port = Viewport(dataset)
        ds_interface.circle_port = Viewport(dataset)

    return dataset

def load_adj(matrix, dataset, ordering=None, ignore_deletes=False, max_edges=0, 
        field_name=None, required_rois=[], suppress_extra_rois=False):
    """
    Loads a matrix. This function is a scripting helper. In other words,
    instead of clicking on the GUI or simulating button presses, this
    function is provided for scripting purposes to just simulate the
    process of loading a matrix into a dataset.

    Parameters
    ----------

    matrix : str | instance(np.ndarray)
        Filename of an adjacency matrix in a supported format (numpy, matlab,
        or plaintext). Can also be a numpy matrix.
    dataset : instance(cvu.dataset.Dataset)
        The dataset into which to place this adjacency matrix
    ordering : None | str | list(str)
        Filename of an ordering file describing the matrix order. Default
        value is None. If None, matrix is assumed to be in parcellation order.
        Can just be a list of label names.
    ignore_deletes : bool
        If True, 'delete' entries in the ordering file are ignored.
        Default value is False.
    max_edges : int
        Default 0. Leave as default or see wiki documentation.
    field_name : None | str
        Needed to tell the field name of a matlab matrix. Required for
        matlab matrices, otherwise ignored
    required_rois : list(str)
        A list of ROIs whose labels must be shown in the circle plot.
        The default value is the empty list, signifying no restrictions.
    suppress_extra_rois : bool
        If true, only the ROIs in required_rois are shown on the circle
        plot.
    """


#    '''
#Loads a matrix. This function is meant to be a scripting helper. In
#other words, instead of clicking on the GUI buttons (or simulating button 
#presses) one could provide the requisite files for this operation inside a 
#script by just calling this function).
#
#Arguments:
#    matrix,         Filename of an adjacency matrix in a supported format 
#                    (numpy, matlab, plaintext). Can also just be a numpy
#                    matrix.
#    dataset,        A reference to the dataset that should contain this
#    ordering,       Filename of an ordering file. Defaults to None. If None,
#                    the matrix is assumed to be in parcellation order. Can also
#                    simply be a list of ROIs.
#    ignore_deletes  If true, 'delete' entries in the ordering file are
#                    ignored. Defaults to false.
#    max_edges       A number. Defaults to 0. If in doubt see wiki documentation.
#    field_name      Only needed for matlab .mat files. Specifies the field name
#                    of the matrix. 
#    required_rois   A list of ROIs that must be included in the circle plot.
#                    Defaults to the empty list.
#    suppress_extra_rois     If true, only the ROIs in required_rois are shown
#                    on the circle plot.
#
#Returns:
#    None
#    '''

    gui = globals()['self']     #explicitly allow dynamic scope
    err_handler = ErrorHandler(quiet=True)

    from preprocessing import process_adj
    from options_struct import AdjmatChooserParameters
    from dataset import Dataset

    if not isinstance(dataset, Dataset):
        print "must supply a valid dataset!"
        return

    adjmat_params = AdjmatChooserParameters(adjmat = matrix,
        adjmat_order = ordering, ignore_deletes = ignore_deletes,
        max_edges=max_edges, field_name=field_name, require_ls=required_rois,
        suppress_extra_rois=suppress_extra_rois, ds_ref = dataset)

    adj_struct = process_adj(adjmat_params, err_handler)
    if adj_struct is None:      #preprocessing errored out
        return
    adj, soft_max_edges, _ = adj_struct 
    dataset._load_adj(adj, soft_max_edges, required_rois, suppress_extra_rois)
    gui.controller.update_display_metadata(dataset.name,
        adj_filename=matrix if isinstance(matrix,str) else 'custom')

if __name__=='__main__':
    main()
