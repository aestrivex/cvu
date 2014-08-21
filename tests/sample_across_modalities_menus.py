#create the fMRI dataset
self.parcellation_chooser_window.ctl.new_dataset=True
self.parcellation_chooser_window.ctl.parcellation_name='laus125'
self.parcellation_chooser_window.ctl.labelnames_file='orders/laus125_cmp.txt'
self.parcellation_chooser_window.ctl.new_dataset_name='fMRI network'
self.parcellation_chooser_window.finished=True
self.parcellation_chooser_window.notify=True

#create the GQI dataset. Most parameters in the window are left unchanged.
self.parcellation_chooser_window.ctl.new_dataset_name=('Generalized Q-Space '
    'Imaging network')
self.parcellation_chooser_window.notify=True

#create the MEG dataset. Most parameters in the window are left unchanged.
self.parcellation_chooser_window.ctl.new_dataset_name=('MEG synchronization '
    'likelihood network')
self.parcellation_chooser_window.notify=True

#load the fMRI data into the fMRI dataset
self.adjmat_chooser_window._current_dataset_list = [
    self.controller.ds_instances['fMRI network']]
self.adjmat_chooser_window.ctl.adjmat='data/sample_fmri.npy'
#parcellation and matrix orderings are the same so we leave the ordering blank
self.adjmat_chooser_window.ctl.adjmat_order=''
self.adjmat_chooser_window.finished=True
self.adjmat_chooser_window.notify=True


#load the GQI data into the GQI dataset
self.adjmat_chooser_window._current_dataset_list = [
    self.controller.ds_instances['Generalized Q-Space Imaging network']]
self.adjmat_chooser_window.ctl.adjmat='data/sample_gqi.npy'
# we leave the ordering information the same
self.adjmat_chooser_window.notify=True


#load the fMRI data into the fMRI dataset
#to illustrate ordering operations the MEG sample dataset has been left in
#alphabetical ordering
self.adjmat_chooser_window._current_dataset_list = [
    self.controller.ds_instances['MEG synchronization likelihood network']] 
self.adjmat_chooser_window.ctl.adjmat='data/sample_meg.npy'
self.adjmat_chooser_window.ctl.adjmat_order='orders/laus125_alph.txt'
self.adjmat_chooser_window.ctl.ignore_deletes=True
self.adjmat_chooser_window.notify=True
