#!/usr/bin/env python

import numpy as np
import mne

names_file='nki_region_names.txt'
centers_file='nki_region_centers.txt'
surface='pial'

new_names_file='nki_region_names_fix.txt'
annot_name='nki'


names=[]

with open(names_file,'r') as fd:
	for ln in fd:
		names.append(ln.strip())

centers=np.loadtxt(centers_file)

lhsurf=mne.read_surface('lh.%s'%surface)
rhsurf=mne.read_surface('rh.%s'%surface)

labs_lh=[]
labs_rh=[]
region_nums={}

with open(new_names_file,'w') as fd:
	#find correct number for this label
	for i,(c,n) in enumerate(zip(centers,names)):
		if n in region_nums:
			nr=region_nums[n]+1
		else:
			nr=1
		region_nums[n]=nr

		if n[0]=='L':
			hemi='lh'	
			#name=n[5:]
			surf=lhsurf[0]
		elif n[0]=='R':
			hemi='rh'
			#name=n[6:]
			surf=rhsurf[0]
		else:
			fd.write('delete\n')
			continue

		#create unique entry in new names file
		name=('%s_%i'%(n,nr)).strip().replace(' ','_').lower()
		fd.write('%s_%s\n'%(hemi,name))

		#find closest vertex
		closest_vertex=-1
		dist=np.inf
		nr_collisions=2
		for i,v in enumerate(surf):
			vert_dist=np.linalg.norm(v-c)
			if vert_dist<dist:
				dist=vert_dist
				closest_vertex=i
			
			if vert_dist==dist:
				if np.random.random() < 1./nr_collisions:
					dist=vert_dist
					closest_vertex=i
				nr_collisions+=1

		#create label file with 1 vertex at closest vertex
		lab = mne.Label(vertices=(closest_vertex,),pos=c.reshape(1,3),hemi=hemi,
			name=name)
		if hemi=='lh':
			labs_lh.append(lab)
		else:
			labs_rh.append(lab)

mne.parc_from_labels(labs_lh, None, annot_fname='lh.%s.annot'%annot_name,
	overwrite=True)
mne.parc_from_labels(labs_rh, None, annot_fname='rh.%s.annot'%annot_name,
	overwrite=True)
