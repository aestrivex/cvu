fmri_ds = load_parc('laus125', 'orders/laus125_cmp.txt', new_dataset=True, 
    dataset_name='fMRI network')
gqi_ds = load_parc('laus125', 'orders/laus125_cmp.txt', new_dataset=True, 
    dataset_name='Generalized Q-space Imaging network')
meg_ds = load_parc('laus125', 'orders/laus125_cmp.txt', new_dataset=True, 
    dataset_name='MEG synchronization likelihood network')

#fMRI sample dataset is already in CMP ordering, no ordering arguments needed
load_adj('data/sample_fmri.npy', fmri_ds)

#GQI sample dataset is already in CMP ordering, no ordering arguments needed
load_adj('data/sample_gqi.npy', gqi_ds)

#to illustrate ordering operations the MEG sample dataset has been left in
#alphabetical ordering
load_adj('data/sample_meg_alphorder.npy', meg_ds, 
    ordering='orders/laus125_alph.txt',
    ignore_deletes=True)
