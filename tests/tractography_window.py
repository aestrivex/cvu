import tractography
import os
from options_struct import ParcellationChooserParameters

truff='/local_mount/space/truffles/1/users/rlaplant/'

subj='hcps030_FS'
subjects_dir=os.path.join(truff,'data/hcpnmr/')

pcp = self.parcellation_chooser_window.ctl
pcp.subjects_dir = subjects_dir
pcp.subject = subj
pcp.parcellation_name = 'laus125'
pcp.labelnames_file = 'orders/laus125_cmp.txt'
pcp.surface_type = 'pial'

self.parcellation_chooser_window.finished=True
self.parcellation_chooser_window.notify=True

trk=os.path.join(truff,'data/qbi/hcps030/tracts20k.trk')
b0=os.path.join(truff,'data/qbi/hcps030/dset/b0.nii.gz')
fs_script='/usr/local/freesurfer/nmr-stable53-env'

tcp = self.tractography_chooser_window.ctl
tcp.track_file = trk
tcp.b0_volume = b0
tcp.fs_setup = fs_script
tcp.subjects_dir = subjects_dir
tcp.subject = subj

self.tractography_chooser_window.finished=True
self.tractography_chooser_window.notify=True
