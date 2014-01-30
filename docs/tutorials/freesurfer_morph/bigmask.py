#!/usr/bin/env python

import os
import sys
import subprocess
import numpy as np
import nibabel as nib

def usage():
	print ("\tusage: ./bigmask.py SUBJECT MASKS_DIR PARC\n\n"
		"\tmasks dir is a directory with overlapping ROIs in nii.gz format\n"
		"\tparc is a string appended to the output volume e.g. 'laus125'")

def main():
	if sys.argv!=4:
		usage()
		return

	subj=sys.argv[1]
	masks_dir=sys.argv[2]
	parc=sys.argv[3]

	bigmask_creation(subj,masks_dir,parc)

#####################
def bigmask_creation(subj,masks_dir,parc):
	import nibabel as nib
	import numpy as np

	parc = 'laus125'

	centroids_dir=os.path.join(masks_dir)

	if not os.path.exists(masks_dir):
		raise ValueError('No volumes exist')

	mask_template_fname=os.listdir(centroids_dir)[0]
	mask_template=nib.load(mask_template_fname)

	mask_shape = mask_template.shape
	big_mask=np.zeros((mask_shape[0],mask_shape[1],mask_shape[2]),dtype=int)
	binary_mask=big_mask.copy()

	#create centroids
	print "collecting centroids"
	centroids={}
	for i,dirent in enumerate(os.listdir(centroids_dir)):
		try:
			r=nib.load(os.path.join(centroids_dir,dirent)).get_data()
			centroids.update({i:np.mean(np.where(r),axis=1)})
			big_mask+=r*i
			binary_mask+=r
		except nib.spatialimages.ImageFileError:
			continue

	print "all centroids collected"

	xi,yi,zi=np.where(binary_mask>1)

	for x,y,z in zip(xi,yi,zi):
		vox=np.array((x,y,z))
		closest_centroid=0
		dist=np.inf
		nr_collisions=2	#divisor starts at 2
						#ensuring that a random voxel will be chosen
		for i,centroid in centroids.items():
			#print vox,centroid
			cent_dist=np.linalg.norm(vox-centroid)
			if cent_dist<dist:
				dist=cent_dist
				closest_centroid=i+1

			if cent_dist==dist:
				if np.random.random() < 1./nr_collisions:
					dist=cent_dist
					closest_centroid=i+1
				nr_collisions+=1
				
		big_mask[x,y,z]=closest_centroid

	img=nib.Nifti1Image(big_mask,mask_template.get_affine(),
		mask_template.get_header())
	nib.save(img,os.path.join(masks_dir,'bigmask_%s.nii.gz'%parc))

	print 'bigmask saved'


if __name__=="__main__":
	main()
