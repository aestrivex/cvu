import tractography
import os

truff='/local_mount/space/truffles/1/users/rlaplant/'

trk=os.path.join(truff,'data/qbi/hcps030/tracts20k.trk')
b0=os.path.join(truff,'data/qbi/hcps030/dset/b0.nii.gz')
subj='hcps030_FS'
subjects_dir=os.path.join(truff,'data/hcpnmr/')
fs_script='/usr/local/freesurfer/nmr-stable53-env'

self.tark = tark = tractography.plot_fancily(trk)

tractography.apply_affines_carefully(tark, b0, trk, subj, subjects_dir, 
	fsenvsrc=fs_script)

tractography.fix_skewing(tark)
