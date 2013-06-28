#	 (C) Roan LaPlante 2013 rlaplant@nmr.mgh.harvard.edu
#
#	 This file is a modified version of UMCP, the UCLA Multimodal Connectivity
#	 Package.  UMCP is copyright (C) Jesse Brown 2012.  This file was modified
#	 06/2013.  For more information, see
#    http://www.ccn.ucla.edu/wiki/index.php/UCLA_Multimodal_Connectivity_Package
#
#    This file is part of cvu, the Connectome Visualization Utility.
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

import os
import struct
import numpy as np
import scipy.linalg as lin
import nibabel as nib
import random
from mayavi import mlab

def read_header(track_file):
	"""Read header values from a .trk (TrackVis) file and store them in a dict.
	This function replicates functionality from umcp, the UCLA multimodal 
	connectivity package, by Jesse Brown at UCLA"""
	header_dict={}
	f=open(track_file, 'rb') # added 'rb' for Windows reading
	contents = f.read()
	f.close()

	dims=(struct.unpack('3h',contents[6:12])[0])
	vox_size=(struct.unpack('3f',contents[12:24])[0])
	origin=(struct.unpack('3f',contents[24:36])[0])
	n_scalars=(struct.unpack('h',contents[36:38]))[0]
	n_properties=(struct.unpack('h',contents[238:240]))[0]
	vox_order=(struct.unpack('3c',contents[948:951])[0])
	paddings=(struct.unpack('3c',contents[952:955])[0])
	img_orient_patient=(struct.unpack('6f',contents[956:980])[0])
	inverts=(struct.unpack('3B',contents[982:985])[0])
	swaps=(struct.unpack('3B',contents[985:988])[0])
	num_fibers=(struct.unpack('i',contents[988:992])[0])
	header_dict["dims"]=dims
	header_dict["vox_size"]=vox_size
	header_dict["origin"]=origin
	header_dict["n_scalars"]=n_scalars
	header_dict["n_properties"]=n_properties
	header_dict["vox_order"]=vox_order
	header_dict["paddings"]=paddings
	header_dict["img_orient_patient"]=img_orient_patient
	header_dict["inverts"]=inverts
	header_dict["swaps"]=swaps
	header_dict["num_fibers"]=num_fibers

	#print np.array(contents[440:504],dtype=np.float32)
	#vox2ras=(struct.unpack('f',contents[440:504])[0])
	#print np.shape(vox2ras)
	#print vox2ras
	return header_dict

def read_tracks(track_file,display_nr=1500):
	"""Read tracks from a .trk file and store them in an array.  This function
	replicates functionality from the UCLA multimodal connectvity package,
	by Jesse Brown."""
	track_list=[]
	header=read_header(track_file)
	size=os.path.getsize(track_file)
	n_s=header['n_scalars']
	n_p=header['n_properties']
	f=open(track_file,'rb')
	contents=f.read(size)
	current=1000
	end=current+4
	nr_fibers=header['num_fibers']
	#calculate random indices
	selected_idxs=random.sample(xrange(nr_fibers),display_nr)

	i=0
	while end < size:		
		length = struct.unpack('i',contents[current:end])[0]
		current=end
		distance=length*(12+4*n_s)
		end = current+distance
		
		if end>size: #eof
			break
		if i not in selected_idxs:
			i+=1
			current=end+(4*n_p)
			end=current+4
			continue
		#else get the track
		floats=[]
		float_range = xrange(current,end,4)
		for float_start in float_range:
			float_end = float_start+4
			floats.append(struct.unpack('f',contents[float_start:float_end])[0])

		if n_p:
			properties_start=float_end
			property_start=properties_start
			#track_properties=[]	#properties are ignored
			for p in xrange(n_p):
				property_end=property_start+4
				#track_properties.append(struct.unpack(blah #properties ignored
				property_start=property_end+4
		
		floats=zip(*[iter(floats)] * 3)
		i+=1
		current=end+(4*n_p)
		end=current+4

		if len(floats)>0:
			track_list.append(np.array(floats))
	f.close()
	return track_list

def plot_naively(fname):
	from mayavi import mlab	

	f=read_tracks(fname)
	
	x=list()
	y=list()
	z=list()
	c=list()

	i=0
	for track in f:
		x.append(track[:,0])
		y.append(track[:,1])
		z.append(track[:,2])
		c.append([[j,j+1] for j in xrange(i,i+len(track)-1)])
		i+=len(track)

	x=np.hstack(x)
	y=np.hstack(y)
	z=np.hstack(z)
	c=np.vstack(c)

	s=np.zeros(len(x))

	src=mlab.pipeline.scalar_scatter(x,y,z,s,name='tractsrc')
	src.mlab_source.dataset.lines=c
	l=mlab.pipeline.stripper(src)
	sf=mlab.pipeline.surface(l,name='tractography')
	return sf

def rotate(x_like,y_like,angle=np.pi/9):
	#angle is in radians and clockwise

	xmap = lambda x,y:np.cos(angle)*x+np.sin(angle)*y
	ymap = lambda x,y:-np.sin(angle)*x+np.cos(angle)*y
	
	x=xmap(x_like,y_like)
	y=ymap(x_like,y_like)

	return x,y
	
def rescale(x,y,z,invert_y=True,**surf_properties_kwargs):
	import volume
	surf_xmin,surf_ymin,surf_zmin,surf_xmax,surf_ymax,surf_zmax=(
		volume.surf_properties(**surf_properties_kwargs))
	pad_nr=2
	surf_xmin+=pad_nr;	surf_xmax-=pad_nr
	surf_ymin+=pad_nr;	surf_ymax-=pad_nr
	surf_zmin+=pad_nr;	surf_zmax-=pad_nr

	xmax=np.max(x)
	xmin=np.min(x)
	xrng=xmax-xmin+1

	ymax=np.max(y)
	ymin=np.min(y)
	yrng=ymax-ymin+1

	zmax=np.max(z)
	zmin=np.min(z)
	zrng=zmax-zmin+1

	xmap=lambda x:(x-xmin)*(surf_xmax-surf_xmin+1)/xrng+surf_xmin
	if invert_y:
		ymap=lambda y:(y-ymin)*(surf_ymin-surf_ymax-1)/yrng+surf_ymax
		print surf_ymin-surf_ymax-1
		print yrng
	else:
		ymap=lambda y:(y-ymin)*(surf_ymax-surf_ymin+1)/yrng+surf_ymin
	zmap=lambda z:(z-zmin)*(surf_zmax-surf_zmin+1)/zrng+surf_zmin

	retx=xmap(x)
	rety=ymap(y)
	retz=zmap(z)
	
	return retx,rety,retz

def affine(affine_trans_file):
	a=np.loadtxt(affine_trans_file)
	return a

def reverse_affine(a):
	#this is equivalent to simply returning lin.inv(a) but has slightly better
	#performance, albeit on the order of .2 ms better
	r=a[0:3,0:3]
	t=a[0:3,3]

	ri=lin.inv(r)
	api=np.zeros((4,4))
	api[0:3,0:3]=ri
	api[0:3,3]=np.dot(ri,t*-1)
	api[3,3]=1
	return api

def apply_affine(a,s):
	tx,ty,tz=s.mlab_source.x,s.mlab_source.y,s.mlab_source.z

	ones=np.ones(len(tx))
	dat=np.array(zip(tx,ty,tz,ones))

	for i,d in enumerate(dat):
		dat[i]=np.dot(a,d)

	s.mlab_source.x,s.mlab_source.y,s.mlab_source.z,_ = dat.T

def plot_well(fname,affine_trans_file=None,ang=-np.pi/18):
	s=plot_naively(fname)

	#ai=reverse_affine(affine(affine_trans_file))
	#a=affine(affine_trans_file)

	#ry,rz=rotate(ty,tz,angle=ang)
	#qx,qy,qz=rescale(tx,ry,rz)
	#s.mlab_source.x=qx; s.mlab_source.y=qy; s.mlab_source.z=qz	

	#apply_affine(a,s)

	s.actor.property.opacity=.1
	s.module_manager.scalar_lut_manager.lut_mode='Purples'
	s.module_manager.scalar_lut_manager.reverse_lut=True
	mlab.view(focalpoint='auto')
	return s
