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
import nibabel as nib
import random

def read_header(track_file):
	"""Read header values from a .trk (TrackVis) file and store them in a dict.
	This function replicates functionality from umcp, the UCLA multimodal 
	connectivity package, by Jesse Brown at UCLA"""
	header_dict={}
	f=open(track_file, 'rb') # added 'rb' for Windows reading
	contents = f.read()
	dims=(struct.unpack('h',contents[6:8])[0],struct.unpack('h',contents[8:10])
		[0],struct.unpack('h',contents[10:12])[0])
	header_dict["dims"]=dims
	vox_size=(struct.unpack('f',contents[12:16])[0],struct.unpack('f',
		contents[16:20])[0],struct.unpack('f',contents[20:24])[0])
	header_dict["vox_size"]=vox_size
	origin=(struct.unpack('f',contents[24:28])[0],struct.unpack('f',
		contents[28:32])[0],struct.unpack('f',contents[32:36])[0])
	header_dict["origin"]=origin
	n_scalars=(struct.unpack('h',contents[36:38]))[0]
	header_dict["n_scalars"]=n_scalars
	n_properties=(struct.unpack('h',contents[238:240]))[0]
	header_dict["n_properties"]=n_properties
	vox_order=(struct.unpack('c',contents[948:949])[0],struct.unpack('c',
		contents[949:950])[0],struct.unpack('c',contents[950:951])[0])
	header_dict["vox_order"]=vox_order
	paddings=(struct.unpack('c',contents[952:953])[0],struct.unpack('c',
		contents[953:954])[0],struct.unpack('c',contents[954:955])[0])
	header_dict["paddings"]=paddings
	img_orient_patient=(struct.unpack('f',contents[956:960])[0],
		struct.unpack('f',contents[960:964])[0],struct.unpack('f',
		contents[964:968])[0],struct.unpack('f',contents[968:972])[0],
		struct.unpack('f',contents[972:976])[0],struct.unpack('f',
		contents[976:980])[0])
	header_dict["img_orient_patient"]=img_orient_patient
	inverts=(struct.unpack('B',contents[982:983])[0],struct.unpack('B',
		contents[983:984])[0],struct.unpack('B',contents[984:985])[0])
	header_dict["inverts"]=inverts
	swaps=(struct.unpack('B',contents[985:986])[0],struct.unpack('B',
		contents[986:987])[0],struct.unpack('B',contents[987:988])[0])
	header_dict["swaps"]=swaps
	num_fibers=(struct.unpack('i',contents[988:992])[0])
	header_dict["num_fibers"]=num_fibers
	f.close()
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
	
def rescale(x,y,z,invert_y=True):
	#fsavg5 dimensions 	-70 	70
	#					-105	70
	#					-50		80 before subcortical structures
	#								which is ok for tractography anyway

	xmax=np.ceil(np.max(x))
	xmin=np.floor(np.min(x))
	xrng=xmax-xmin+1

	ymax=np.ceil(np.max(y))
	ymin=np.floor(np.min(y))
	yrng=ymax-ymin+1

	zmax=np.ceil(np.max(z))
	zmin=np.floor(np.min(z))
	zrng=zmax-zmin+1

	xmap=lambda x:(x-xmin)*135/xrng-67
	if invert_y:
		ymap=lambda y:(y-ymin)*-170/yrng+67
	else:
		ymap=lambda y:(y-ymin)*170/yrng-102
	zmap=lambda z:(z-zmin)*125/zrng-47

	retx=xmap(x)
	rety=ymap(y)
	retz=zmap(z)
	
	return retx,rety,retz

def plot_well(fname,ang=-np.pi/18):
	s=plot_naively(fname)
	tx=s.mlab_source.x; ty=s.mlab_source.y; tz=s.mlab_source.z
	ry,rz=rotate(ty,tz,angle=ang)
	qx,qy,qz=rescale(tx,ry,rz)
	s.mlab_source.x=qx; s.mlab_source.y=qy; s.mlab_source.z=qz	

	s.actor.property.opacity=.1
	s.module_manager.scalar_lut_manager.lut_mode='Purples'
	s.module_manager.scalar_lut_manager.reverse_lut=True
	return s
