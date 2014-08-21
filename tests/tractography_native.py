import tractography
import os
from options_struct import ParcellationChooserParameters

truff='/local_mount/space/truffles/1/users/rlaplant/'

s='hcps026'
subj='%s_FS'%s
subjects_dir=os.path.join(truff,'data/hcpnmr/')

pcp = self.parcellation_chooser_window.ctl
pcp.subjects_dir = subjects_dir
pcp.subject = subj
pcp.parcellation_name = 'aparc'
pcp.labelnames_file = 'orders/aparc_cmp.txt'
pcp.surface_type = 'pial'

self.parcellation_chooser_window.finished=True
self.parcellation_chooser_window.notify=True


trk=os.path.join(truff,'data/qbi/%s/tracts20k.trk'%s)
b0=os.path.join(truff,'data/qbi/%s/dset/b0.nii.gz'%s)
fs_script='/usr/local/freesurfer/nmr-stable53-env'

self.tark = tark = tractography.plot_fancily(trk)

tractography.apply_affines_carefully(tark, b0, trk, subj, subjects_dir, 
	fsenvsrc=fs_script)

ds = self.controller.ds_orig

tractography.fix_skewing(tark,use_fsavg5=False,
	lhsurf=ds.dv_3d.syrf_lh, rhsurf=ds.dv_3d.syrf_rh)
