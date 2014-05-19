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
        adj=adj,soft_max_edges=args['maxedges'], gui=ErrorHandler(args['quiet']))
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

    #Qt does not sys.exit in response to KeyboardInterrupt correctly like wx does
    #we intercept keyboard interrupts in the interpreter before it gets to the Qt loop
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    if exec_script is not None:
        from pyface.api import GUI
        gui=GUI()

        def run_script():
            gui.process_events()
            script(exec_script, cvu_gui=g, scriptdir=sys.argv[1])

        gui.invoke_later(run_script)

    g.configure_traits()

def script(file, cvu_gui=None, scriptdir=os.getcwd()):
    curdir=os.getcwd()
    os.chdir(scriptdir)
    #print scriptdir
    file=os.path.abspath(file)
    os.chdir(curdir)
    #print globals()
    self = cvu_gui
    with open(file) as fd: exec(fd)

if __name__=='__main__':
    main()
