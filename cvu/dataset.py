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

from __future__ import division
from traits.api import (HasTraits,Any,Range,Bool,Float,Enum,Str,List,Int,
    Instance,Dict,Either,Property,Method,Constant,cached_property,
    on_trait_change,TraitError)
import numpy as np
from color_map import CustomColormap
from color_legend import (ColorLegend,LegendEntry)
from matplotlib.colors import LinearSegmentedColormap
from dataview import (DataView,DVMayavi,DVMatrix,DVCircle)
from options_struct import (ScalarDisplaySettings,DisplayOptions)
from utils import CVUError
from threading import Thread

class SurfData(HasTraits):
    lh_verts=Any	#Vx3 np.ndarray
    lh_tris=Any		#?x3 np.ndarray(int)
    rh_verts=Any	#Vx3 np.ndarray
    rh_tris=Any		#?x3 np.ndarray(int)
    surftype=Str	

    def __init__(self,lhv,lht,rhv,rht,sft):
        super(SurfData,self).__init__()
        self.lh_verts=lhv;		self.lh_tris=lht
        self.rh_verts=rhv;		self.rh_tris=rht
        self.surftype=sft

class Dataset(HasTraits):
    ########################################################################
    # FUNDAMENTALLY NECESSARY DATA
    ########################################################################

    name=Str							#give this dataset a name
    
    gui=Any								#symbolic reference to a modular cvu

    nr_labels=Int
    nr_edges=Int

    labnam=List(Str)
    #adjlabfile=File
    #the adjlabfile is not needed.  this is only kept on hand to pass it
    #around if specified as CLI arg.  it is only used upon loading an adjmat.
    #so just have adjmat loading be a part of dataset creation and get rid of
    #keeping track of this

    adj=Any										#NxN np.ndarray	
    adj_thresdiag=Property(depends_on='adj')	#NxN np.ndarray
    
    @cached_property
    def _get_adj_thresdiag(self):
        adjt = self.adj.copy()
        adjt[np.where(np.eye(self.nr_labels))]=np.min(adjt[np.where(adjt)])
        return adjt

    starts=Any				#Ex3 np.ndarray
    vecs=Any				#Ex3 np.ndarray
    edges=Any				#Ex2 np.ndarray(int)

    srf=Instance(SurfData)

    #labv=List(Instance(mne.Label))

    #all that is needed from this is a map of name->vertex
    #this is a considerable portion of the data contained in a label but still
    #only perhaps 15%.  To make lightweight, extract this from labv
    #TODO convert it to that

    labv=Dict #is an OrderedDict in parcellation order

    lab_pos=Any	#Nx3 np.ndarray

    #########################################################################
    # CRITICAL NONADJUSTABLE DATA WITHOUT WHICH DISPLAY CANNOT EXIST
    #########################################################################

    dv_3d	= Either(Instance(DataView),None)
    dv_mat	= Either(Instance(DataView),None)
    dv_circ = Either(Instance(DataView),None)

    soft_max_edges=Int

    adjdat=Any		#Ex1 np.ndarray
    left=Any		#Nx1 np.ndarray(bool)
    right=Any		#Nx1 np.ndarray(bool)
    interhemi=Any	#Nx1 np.ndarray(bool)
    masked=Any		#Nx1 np.ndarray(bool)

    lhnodes=Property(depends_on='labnam')		#Nx1 np.ndarray(int)
    rhnodes=Property(depends_on='labnam')		#Nx1 np.ndarray(int)
    @cached_property
    def _get_lhnodes(self):
        return np.where(map(lambda r:r[0]=='l',self.labnam))[0]
    @cached_property
    def _get_rhnodes(self):
        return np.where(map(lambda r:r[0]=='r',self.labnam))[0]

    node_colors = Any	#Nx3 np.ndarray
    #node_colors represents the colors held by the nodes.  the current value of
    #node_colors depends on the current policy (i.e. the current display mode).
    #however, don't take this all too literally.  depending on the current
    #policy, the dataviews may choose to ignore what is in node_colors and
    #use some different color.
    #this is always true of Mayavi views, who can't use the node colors at all.
    #because mayavi doesn't play nice with true colors (this could be fixed
    #if mayavi is fixed). it is also true of the other plots in scalar mode, 
    #but when scalars are not specified for those dataviews.

    #node_colors_default will be set uniquely for each parcellation and can
    #thus be different for different datasets.

    #group_colors is more subtle; it can in principle be set uniquely for each
    #parcellation as long as the parcellations don't conform to aparc.  for
    #instance, destrieux parc has different group colors.  right now i'm a long
    #way away from dealing with this but i think in a month it will be prudent
    #to just have the dataset capture both of these variables
    node_colors_default=List
    node_labels_numberless=List(Str)

    group_colors=List
    nr_groups=Int
    group_labels=List(Str)
    color_legend=Instance(ColorLegend)

    module_colors=List
    default_glass_brain_color=Constant((.82,.82,.82))
    
    #########################################################################
    # ASSOCIATED STATISTICAL AND ANALYTICAL DATA
    #########################################################################

    node_scalars=Dict
    scalar_display_settings=Instance(ScalarDisplaySettings)
    #TODO make modules a dictionary
    modules=List
    nr_modules=Int
    graph_stats=Dict

    #########################################################################
    # ASSOCIATED DISPLAY OPTIONS AND DISPLAY STATE (ADJUSTABLE/TRANSIENT)
    #########################################################################

    opts=Instance(DisplayOptions)
    display_mode=Enum('normal','scalar','module_single','module_multi')
    reset_thresh=Property(Method)
    def _get_reset_thresh(self):
        if self.opts.thresh_type=='prop': return self.prop_thresh
        elif self.opts.thresh_type=='abs': return self.abs_thresh

    thresval=Float

    curr_node=Either(Int,None)
    cur_module=Either(Int,'custom',None)
    custom_module=List

    ########################################################################
    # SETUP
    ########################################################################

    def __init__(self,name,lab_pos,labnam,srf,labv,
            gui=None,adj=None,soft_max_edges=20000,**kwargs):
        super(Dataset,self).__init__(**kwargs)

        self.gui=gui

        self.name=name

        self.opts=DisplayOptions(self)
        self.scalar_display_settings=ScalarDisplaySettings(self)

        #this is effectively load_parc
        self.lab_pos=lab_pos
        self.labnam=labnam
        self.srf=srf
        self.labv=labv
        self.nr_labels=len(labnam)

        #load_parc redundantly sets the current display but oh well.
        #self.load_parc(lab_pos,labnam,srf,labv,
        #	init_display.subject_name,init_display.parc_name)

        #if adj is None, it means it will be guaranteed to be supplied later
        #by the user

        #this is load adj, except without initializing nonexistent dataviews
        if adj is not None:
            self.adj=adj
            self.soft_max_edges=soft_max_edges
            self.pos_helper_gen()
            #flip adj ord should already be done to the preprocessed adj
            self.adj_helper_gen()
    
        self.color_legend=ColorLegend()
        self.node_colors_gen()

        self.dv_3d=DVMayavi(self)
        self.dv_mat=DVMatrix(self)
        self.dv_circ=DVCircle(self)

        self.chg_scalar_colorbar()

    def __repr__(self): return 'Dataset: %s'%self.name
    def __getitem__(self,key):
        if key==0: return self
        elif key==1: return self.name
        else: raise KeyError('Invalid indexing to dataset.  Dataset indexing '
            'is implemented to appease CheckListEditor and can only be 0 or 1.')

    ########################################################################
    # GEN METHODS
    ########################################################################

    #preconditions: lab_pos has been set.
    def pos_helper_gen(self,reset_scalars=True):
        self.nr_labels = n = len(self.lab_pos)
        self.nr_edges = self.nr_labels*(self.nr_labels-1)//2
        #self.starts = np.zeros((self.nr_edges,3),dtype=float)
        #self.vecs = np.zeros((self.nr_edges,3),dtype=float)
        #self.edges = np.zeros((self.nr_edges,2),dtype=int)
        #i=0
        #for r2 in xrange(0,self.nr_labels,1):
        #	for r1 in xrange(0,r2,1):
                #self.starts[i,:] = self.lab_pos[r1]
                #self.vecs[i,:] = self.lab_pos[r2]-self.lab_pos[r1]
                #self.edges[i,0],self.edges[i,1] = r1,r2
                #i+=1

        tri_ixes = np.triu(np.ones((n,n)),1)
        ixes, = np.where(tri_ixes.flat)

        A_r = np.tile(self.lab_pos,(n,1,1))
        self.starts = np.reshape(A_r,(n*n,3))[ixes,:]
        self.vecs = np.reshape(A_r-np.transpose(A_r,(1,0,2)),(n*n,3))[ixes,:]

        self.edges = np.transpose(np.where(tri_ixes.T))[:,::-1]

        #pos_helper_gen is now only called from load adj. The reason it is
        #because it can change on all adj changes because of the soft
        #cap.  The number of edges can differ between adjmats because of the
        #soft cap and all of the positions need to be recalculated if it does.

        #pos_helper_gen really only has to do with edge positions.  Node and
        #surf positions dont depend on it at all.
        
        #TODO possibly, keep track of the soft cap and do nothing if it hasn't
        #changed
        #RESPONSE: yes but this check should be done in adj_load
        if reset_scalars:
            self.node_scalars = {}
        self.display_mode='normal'
    
    #precondition: adj_helper_gen() must be run after pos_helper_gen()
    def adj_helper_gen(self):
        self.nr_edges = self.nr_labels*(self.nr_labels-1)//2
        self.adjdat = np.zeros((self.nr_edges),dtype=float)
        self.interhemi = np.zeros((self.nr_edges),dtype=bool)
        self.left = np.zeros((self.nr_edges),dtype=bool)
        self.right = np.zeros((self.nr_edges),dtype=bool)
        self.masked = np.zeros((self.nr_edges),dtype=bool)
        i=0
    
        self.adj[xrange(self.nr_labels),xrange(self.nr_labels)]=0

        #for r2 in xrange(0,self.nr_labels,1):
            #self.adj[r2][r2]=0
            #for r1 in xrange(0,r2,1):
                #self.adjdat[i] = self.adj[r1][r2]
                #self.interhemi[i] = self.labnam[r1][0] != self.labnam[r2][0]
                #self.left[i] = self.labnam[r1][0]==self.labnam[r2][0]=='l'
                #self.right[i] = self.labnam[r1][0]==self.labnam[r2][0]=='r'
                #i+=1

        n = self.nr_labels
        ixes, = np.where(np.triu(np.ones((n,n)),1).flat)

        self.adjdat = self.adj.flat[::-1][ixes][::-1]

        from parsing_utils import same_hemi
        sh=np.vectorize(same_hemi)

        L_r = np.tile(self.labnam,(self.nr_labels,1))
        
        self.interhemi = np.logical_not(sh(L_r,L_r.T)).flat[::-1][ixes][::-1]
        self.left = sh(L_r,L_r.T,'l').flat[::-1][ixes][::-1]
        self.right = sh(L_r,L_r.T,'r').flat[::-1][ixes][::-1]

        #remove all but the soft_max_edges largest connections
        if self.nr_edges > self.soft_max_edges:
            cutoff = sorted(self.adjdat)[self.nr_edges-self.soft_max_edges-1]
            zi = np.where(self.adjdat>=cutoff)
            # if way way too many edges remain, make it a hard max
            # this happens in DTI data which is very sparse, the cutoff is 0
            if len(zi[0])>(self.soft_max_edges+200):
                zi=np.where(self.adjdat>cutoff)

            self.starts=self.starts[zi[0],:]
            self.vecs=self.vecs[zi[0],:]
            self.edges=self.edges[zi[0],:]
            self.adjdat=self.adjdat[zi[0]]

            self.interhemi=self.interhemi[zi[0]]
            self.left=self.left[zi[0]]
            self.right=self.right[zi[0]]
            
            self.nr_edges=len(self.adjdat)
            self.verbose_msg(str(self.nr_edges)+" total connections")

        #sort the adjdat
        sort_idx=np.argsort(self.adjdat,axis=0)
        self.adjdat=self.adjdat[sort_idx].squeeze()
        self.edges=self.edges[sort_idx].squeeze()

        self.starts=self.starts[sort_idx].squeeze()
        self.vecs=self.vecs[sort_idx].squeeze() 

        self.left=self.left[sort_idx].squeeze()
        self.right=self.right[sort_idx].squeeze()
        self.interhemi=self.interhemi[sort_idx].squeeze()
        self.masked=self.masked[sort_idx].squeeze()	#just to prune

        #try to auto-set the threshold to a reasonable value
        if self.nr_edges < 500:
            self.opts.pthresh=.01
        else:
            thr = (self.nr_edges - 500) / (self.nr_edges)
            self.opts.pthresh=thr
        self.opts.thresh_type = 'prop'

        self.display_mode='normal'

    def node_colors_gen(self):
        #node groups could change upon loading a new parcellation
        hi_contrast_clist= ('#26ed1a','#eaf60b','#e726f4','#002aff','#05d5d5',
            '#f4a5e0','#bbb27e','#641179','#068c40')
        hi_contrast_cmap=LinearSegmentedColormap.from_list('hi_contrast',
            hi_contrast_clist)

        #labels are assumed to start with lh_ and rh_
        self.node_labels_numberless=map(
            lambda n:n.replace('div','').strip('1234567890_'),self.labnam)
        node_groups=map(lambda n:n[3:],self.node_labels_numberless)

        #put group names in ordered set
        #n_set=set()
        #self.group_labels=(
        #    [i for i in node_groups if i not in n_set and not n_set.add(i)])

        node_groups_hemi1 = map(lambda n:n[3:],
            self.node_labels_numberless[:len(self.lhnodes)])

        node_groups_hemi2 = map(lambda n:n[3:],
            self.node_labels_numberless[-len(self.rhnodes):])

        a_set = set()
        self.group_labels=(
            [i for i in node_groups_hemi1 if not i in a_set and not a_set.add(i)])

        last_grp=None
        for grp in node_groups_hemi2:
            if grp not in self.group_labels:
                if last_grp is None:
                    self.group_labels.insert(grp, 0)
                else:
                    self.group_labels.insert( 
                        self.group_labels.index(last_grp)+1, grp)
            else:
                last_grp=grp
                

        self.nr_groups=len(self.group_labels)
        
        #get map of {node name -> node group}	
        grp_ids=dict(zip(self.group_labels,xrange(self.nr_groups)))

        #group colors does not change unless the parcellation is reloaded
        self.group_colors=(
            [hi_contrast_cmap(i/self.nr_groups) for i in range(self.nr_groups)])

        #node colors changes constantly, so copy and stash the result
        self.node_colors=map(lambda n:self.group_colors[grp_ids[n]],node_groups)
        self.node_colors_default=list(self.node_colors)

        #create the color legend associated with this dataset
        def create_color_legend_entry(zipped):
            label,color=zipped
            return LegendEntry(metaregion=label,col=color)

        self.color_legend.entries=map(create_color_legend_entry,
            zip(self.group_labels,self.group_colors))

        #set up some colors that are acceptably high contrast for modules
        #this is unrelated to node colors in any way, for multi-module mode
        self.module_colors=(
            [[255,255,255,255],[204,0,0,255],[51,204,51,255],[66,0,204,255],
             [80,230,230,255],[51,153,255,255],[255,181,255,255],
             [255,163,71,255],[221,221,149,255],[183,230,46,255],
             [77,219,184,255],[255,255,204,255],[0,0,204,255],[204,69,153,255],
             [255,255,0,255],[0,128,0,255],[163,117,25,255],[255,25,117,255]])

    ######################################################################
    # DRAW METHODS
    ######################################################################

    def draw(self, skip_circ=False):
        self.draw_surfs()
        self.draw_nodes(skip_circ=skip_circ)
        self.draw_conns(skip_circ=skip_circ)

    def draw_surfs(self):
        for data_view in (self.dv_3d, self.dv_mat, self.dv_circ):
            data_view.draw_surfs()

    def draw_nodes(self, skip_circ=False):
        self.set_node_colors()
        for data_view in (self.dv_3d, self.dv_mat, self.dv_circ):
            if skip_circ and data_view is self.dv_circ:
                continue
            data_view.draw_nodes()

    def set_node_colors(self):
        #set node_colors
        if self.display_mode=='normal':
            self.node_colors=list(self.node_colors_default)
        elif self.display_mode=='scalar':
        #node colors are not used here, instead the scalar value is set directly
            self.node_colors=list(self.node_colors_default)
        elif self.display_mode=='module_single':
            new_colors=np.tile(.3,self.nr_labels)
            new_colors[self.get_module()]=.8
            self.node_colors=list(self.opts.default_map._pl(new_colors))
        elif self.display_mode=='module_multi':
            while self.nr_modules > len(self.module_colors):
                i,j=np.random.randint(18,size=(2,))
                col=(np.array(self.module_colors[i])+self.module_colors[j])/2
                col=np.array(col,dtype=int)
                self.module_colors.append(col.tolist())
            perm=np.random.permutation(len(self.module_colors))
            #mayavi scalars depend on saving the module colors
            self.module_colors=np.array(self.module_colors)[perm].tolist()
            cols=self.module_colors[:self.nr_modules]
            import bct
            ci=bct.ls2ci(self.modules,zeroindexed=True)
            self.node_colors=((np.array(self.module_colors)[ci])/255).tolist()

    def draw_conns(self,conservative=False, skip_circ=False):
        if conservative: new_edges = None
        else: new_edges,count_edges = self.select_conns(skip_circ=skip_circ)
        for data_view in (self.dv_3d, self.dv_mat, self.dv_circ):
            if skip_circ and data_view is self.dv_circ:
                continue
            elif data_view is not None:
                data_view.draw_conns(new_edges)

    def select_conns(self, skip_circ=False):
        disable_circle = (skip_circ or self.opts.circle_render=='disabled')
        lo=self.thresval
        hi=np.max(self.adjdat)

        basic_conds=lambda e,a,b:(not self.masked[e] and 
            self.curr_node is None or self.curr_node in (a,b))

        if self.display_mode=='module_single':
            #find the right module
            module=self.get_module()
            #attach the right conditions
            if self.opts.module_view_style=='intramodular':
                conds = lambda e,a,b:(basic_conds(e,a,b) and 
                    (a in module and b in module))
            elif self.opts.module_view_style=='intermodular':
                conds = lambda e,a,b:(basic_conds(e,a,b) and
                    ((a in module) != (b in module))) #xor
            elif self.opts.module_view_stlye=='both':
                conds = lambda e,a,b:(basic_conds(e,a,b) and
                    (a in module or b in module))
        else:
            conds=basic_conds

        new_edges=np.zeros((self.nr_edges,2),dtype=int)
        count_edges=0
        for e,(a,b) in enumerate(zip(self.edges[:,0],self.edges[:,1])):
            if conds(e,a,b):
                new_edges[e]=(a,b)

                #do the threshold checking here.  This code breaks the
                #design spec; the dataset is checking the dataview and
                #messing with its internals.  obviously, the reason why
                #is that this code runs often and needs to be optimized
                if self.dv_circ is not None and not disable_circle:
                    ev=self.adjdat[e]
                    if (lo <= ev <= hi):
                        self.dv_circ.circ_data[e].set_visible(True)
                        ec=self.opts.activation_map._pl((ev-lo)/(hi-lo))
                        self.dv_circ.circ_data[e].set_ec(ec)
                        count_edges+=1
                    else:
                        self.dv_circ.circ_data[e].set_visible(False)
            else:
                new_edges[e]=(0,0)
                if self.dv_circ is not None and not disable_circle:
                    self.dv_circ.circ_data[e].set_visible(False)
    
        return new_edges,count_edges

    def center_adjmat(self):
        self.dv_mat.center()

    ######################################################################
    # I/O METHODS (LOADING, SAVING)
    ######################################################################

    def _load_parc(self,lab_pos,labnam,srf,labv):
        self.lab_pos=lab_pos
        self.labnam=labnam
        self.srf=srf
        self.labv=labv
        self.nr_labels=len(labnam)

        #there is no need to call pos_helper_gen here!  pos_helper_gen
        #only has to do with edges. previously it also reset scalars, but we
        #don't do that in load_adj so there is no reason for it

        #self.pos_helper_gen()
        self.node_scalars = {}

        self.color_legend=ColorLegend()
        self.node_colors_gen()

        self.adj=None	#whatever adj was before, it is now the wrong size

        self.reset_dataviews()

    def _load_adj(self,adj,soft_max_edges,reqrois,suppress_extra_rois):
        self.adj=adj
        self.soft_max_edges=soft_max_edges
        
        #it is necessary to rerun pos_helper_gen() on every load because the 
        #number of edges
        #is not constant from one adjmat to another and which edges are thrown
        #away under the soft cap may differ. pos_helper_gen is really all about 
        #edge positions.  we wouldnt have to do this if *all* previously 
        #subcutoff are still subcutoff (which is unlikely).
        
        #we could also potentially avoid having to do this if we knew that the
        #parcellation didnt change and only contained nr_edges < soft_max.  But
        #its not worth bothering
        self.pos_helper_gen()

        #flip adj ord should already be done to the preprocessed adj
        self.adj_helper_gen()
        
        self.dv_3d.vectors_clear()
        self.display_mode='normal'

        self.dv_3d.supply_adj()
        self.dv_mat.supply_adj()

        if self.opts.circle_render=='asynchronous':
            #first set up the 3D brain properly and then set the circle
            #to generate itself in a background thread
            self.display_all(skip_circ=True)
            self.dv_3d.zaxis_view()

            def threadsafe_circle_setup():
                self.dv_circ.supply_adj(reqrois=reqrois, 
                    suppress_extra_rois=suppress_extra_rois)
                self.select_conns()
                self.dv_circ.draw_conns()

            Thread(target=threadsafe_circle_setup).start()
        else:
        #otherwise set up the circle and display everything in a
        #single thread. If the circle is disabled this will not cause problems
            self.dv_circ.supply_adj(reqrois=reqrois,
                suppress_extra_rois=suppress_extra_rois)
            self.display_all()
            self.dv_3d.zaxis_view()

    #This method takes a TractographyChooserParameters
    def load_tractography(self,params):
        if not params.track_file:
            self.error_dialog('You must specify a valid tractography file') 
            return	
        if not params.b0_volume:
            self.error_dialog('You must specify a B0 volume from which the ' 
                'registration to the diffusion space can be computed')
            return
        if not params.subjects_dir or not params.subject:
            self.error_dialog('You must specify the freesurfer reconstruction ' 
                'for the individual subject for registration to the surface ' 
                'space.')
            return

        self.dv_3d.tracks_gen(params)

    #This method takes a GeneralMatrixChooserParameters
    def load_modules_or_scalars(self,params):
        if not params.mat:
            self.error_dialog('You must specify a valid matrix file'); return
        if params.whichkind=='scalars' and not params.measure_name:
            self.error_dialog('Cannot leave scalar name blank.  cvu uses '
                'this value as a dictionary index'); return

        import preprocessing
        try:
            ci=preprocessing.loadmat(params.mat, field=params.field_name, 
                is_adjmat=False)
        except (CVUError,IOError) as e: self.error_dialog(str(e)); return

        if params.mat_order:
            try:
                init_ord, bads = preprocessing.read_ordering_file(
                    params.mat_order)	
            except (IndexError,UnicodeDecodeError) as e:
                self.error_dialog(str(e)); return

            #delete the bads
            if not params.ignore_deletes:
                ci=np.delete(ci,bads)

            #perform the swapping
            try:
                ci_ord = preprocessing.adj_sort(init_ord, self.labnam)	
            except CVUError as e: self.error_dialog(str(e)); return
            except KeyError as e:
                self.error_dialog('Field not found: %s'%str(e)); return
            ci=ci[ci_ord]

        try:
            ci=np.reshape(ci,(self.nr_labels,))
        except ValueError as e:
            self.error_dialog('The %s file is of size %i after deletions, but '
                'the dataset has %i regions' %
                (params.whichkind, len(ci), self.nr_labels)); return

        if params.whichkind=='modules':	
            import bct
            self.modules=bct.ci2ls(ci)
            self.nr_modules=len(self.modules)
        elif params.whichkind=='scalars':
            self.save_scalar(params.measure_name,ci)
            params._increment_scalar_count()

    #this method destroys the current dataviews and resets them entirely
    def reset_dataviews(self):
        #in principle it might be useful to do some more cleanup here
        self.display_mode='normal'
        
        self.dv_3d=DVMayavi(self)
        self.dv_mat=DVMatrix(self)
        self.dv_circ=DVCircle(self)

        self.chg_scalar_colorbar()
        #scalar colorbar loading is tied to the surface and not to nodes
        #because the surface always has the same color scheme and the nodes
        #don't.  but it can't be in surfs_gen because the surf can get gen'd
        #when switching from cracked to glass. so it is here.

    #handles the scaling and size checking for new scalar datasets
    def save_scalar(self,name,scalars,passive=False):
        if np.squeeze(scalars).shape != (self.nr_labels,):
            if passive:
                self.verbose_msg("%s: Only Nx1 vectors can be saved as scalars"
                    %name)
                return
            else:
                self.error_dialog("%s: Only Nx1 vectors can be saved as scalars"
                    %name)
                #print np.squeeze(scalars).shape, self.nr_labels
                return
        ci=scalars.ravel().copy()
        #ci=(ci-np.min(ci))/(np.max(ci)-np.min(ci))
        self.node_scalars.update({name:ci})

    #this function takes a SnapshotParameters object and returns a
    #continuation -- a closure -- which saves the snapshot.  The CVU object
    #spawns the "Really overwrite file" window if the file exists, and then 
    #calls the continuation, or else just calls the continuation directly.
    def snapshot(self,params):
        def save_continuation():
            try:
                if params.whichplot=='3D brain': 
                    self.dv_3d.snapshot(params)
                elif params.whichplot=='connection matrix':
                    self.dv_mat.snapshot(params)		
                elif params.whichplot=='circle plot':
                    self.dv_circ.snapshot(params)
            except IOError as e:
                self.error_dialog(str(e))
            except KeyError as e:
                self.error_dialog('The library making the snapshot supports'
                    ' multiple file types and doesnt know which one you want.'
                    ' Please specify a file extension to disambiguate.')
        return save_continuation

    #this function takes a MakeMovieParameters object and returns a
    #continuation which records and takes the movie.  The CVU object is again
    #responsible for thinking about the "really overwrite file" case.
    def make_movie(self,params):
        def save_continuation(): self.dv_3d.make_movie(params)
        return save_continuation

    def make_movie_finish(self,params):
        self.dv_3d.make_movie_finish(params)
    
    ######################################################################
    # VISUALIZATION INTERACTIONS
    ######################################################################

    def display_all(self, skip_circ=False):
        self.display_mode='normal'
        self.curr_node=None
        self.cur_module=None
        self.center_adjmat()
        self.draw(skip_circ=skip_circ)

    def display_node(self,n):
        if n<0 or n>=self.nr_labels: return
        self.curr_node=n
        self.draw_conns()

    def display_scalars(self):
        self.display_mode='scalar'
        self.draw_surfs()
        self.draw_nodes()

    def display_module(self,module):
        self.display_mode='module_single'
        self.curr_node=None
        self.cur_module=module
        self.draw() #draw surf is needed to unset surf color

    def display_multi_module(self):
        if not self.modules:
            self.error_dialog('No modules defined')	
            return
        self.display_mode='module_multi'
        self.draw_nodes()

    def calculate_modules(self,thres):
        import graph, bct
        thres_adj=self.adj.copy()
        thres_adj[thres_adj < thres] = 0
        self.verbose_msg('Threshold for modularity calculation: %s'%str(thres))
        modvec = graph.calculate_modules(thres_adj)
        self.modules = bct.ci2ls(modvec)
        self.nr_modules = len(self.modules)
    
    def calculate_graph_stats(self,thres):
        import graph, bct
        thres_adj = self.adj.copy()
        thres_adj[thres_adj < thres] = 0
        self.verbose_msg('Threshold for graph calculations: %s'%str(thres))
        try:
            self.graph_stats=graph.do_summary(thres_adj,bct.ls2ci(self.modules),
                self.opts.intermediate_graphopts_list)

            for name,arr in self.graph_stats.iteritems():
                self.save_scalar(name,arr,passive=True)
        except CVUError:
            self.error_dialog("Community structure required for some of "
                "the calculations specified.  Try calculating modules first.")

    #save_graphstat_to_scalar is principally interaction between window and
    #dataset manager.  it should call a generic save_scalar method, same as
    #loading a scalar from a file

    ######################################################################
    # OPTIONS
    ######################################################################

    def prop_thresh(self):
        try:
            self.thresval=float(self.adjdat[
                int(round(self.opts.pthresh*self.nr_edges-1))])
        except TraitError as e:
            if self.opts.pthresh>1:
                self.warning_dialog("%s\nThreshold set to maximum"%str(e))
            elif self.opts.pthresh<0:
                self.warning_dialog("%s\nThreshold set to minimum"%str(e))
            else:
                self.error_dialog("Programming error")

    def abs_thresh(self):
        self.thresval=self.opts.athresh
        if self.adjdat[self.nr_edges-1] < self.opts.athresh:
            self.thresval=self.adjdat[self.nr_edges-1]
            self.warning_dialog("Threshold over maximum! Set to maximum.")
        elif self.adjdat[0] > self.opts.athresh:
            self.thresval=self.adjdat[0]
            self.warning_dialog("Threshold under minimum! Set to minimum.")

    #recall reset thresh is a cached property
    @on_trait_change('opts:pthresh')
    def chg_pthresh_val(self):
        if self.opts.thresh_type != 'prop': return
        self.reset_thresh()
        self.draw_conns(conservative=True)

    @on_trait_change('opts:athresh')
    def chg_athresh_val(self):
        if self.opts.thresh_type != 'abs': return
        self.reset_thresh()
        self.draw_conns(conservative=True)

    @on_trait_change('opts:thresh_type')
    def chg_thresh_type(self):
        self.draw_conns(conservative=True)

    @on_trait_change('opts:interhemi_conns_on')
    def chg_interhemi_connmask(self):
        self.masked[self.interhemi]=not self.opts.interhemi_conns_on

    @on_trait_change('opts:lh_conns_on')
    def chg_lh_connmask(self):
        self.masked[self.left]=not self.opts.lh_conns_on

    @on_trait_change('opts:rh_conns_on')
    def chg_rh_connmask(self):
        self.masked[self.right]=not self.opts.rh_conns_on

    #the following options operate on specific views only
    #they may fail if the view is not present (i dont know if this is true)
    @on_trait_change('opts:tube_conns')
    def chg_tube_conns(self):
        try: self.dv_3d.set_tubular_properties()
        except AttributeError: pass

    @on_trait_change('opts:circ_size')
    def chg_circ_size(self):
        try:
            self.dv_circ.circ.axes[0].set_ylim(0,self.opts.circ_size)
            self.dv_circ.circ.canvas.draw()
        except AttributeError: pass

    @on_trait_change('opts:show_floating_text')
    def chg_float_text(self):
        try: self.dv_3d.txt.visible=self.opts.show_floating_text
        except AttributeError: pass

    @on_trait_change('opts:scalar_colorbar')
    def chg_scalar_colorbar(self):
        try: self.dv_3d.set_colorbar(self.opts.scalar_colorbar,
                self.dv_3d.syrf_lh, orientation='vertical')
        except AttributeError: pass

    @on_trait_change('opts:render_style')
    def chg_render_style(self):
        try: self.dv_3d.set_surf_render_style(self.opts.render_style)
        except AttributeError: pass

    @on_trait_change('opts:surface_visibility')
    def chg_surf_opacity(self):
        try: 
            for syrf in (self.dv_3d.syrf_lh, self.dv_3d.syrf_rh):
                syrf.actor.property.opacity=self.opts.surface_visibility
        except AttributeError: pass

    @on_trait_change('opts:lh_nodes_on')
    def chg_lh_nodemask(self):
        try: self.dv_3d.nodes_lh.visible=self.opts.lh_nodes_on
        except AttributeError: pass

    @on_trait_change('opts:rh_nodes_on') 
    def chg_rh_nodemask(self):
        try: self.dv_3d.nodes_rh.visible=self.opts.rh_nodes_on
        except AttributeError: pass

    @on_trait_change('opts:lh_surfs_on')
    def chg_lh_surfmask(self):
        try: self.dv_3d.syrf_lh.visible=self.opts.lh_surfs_on
        except AttributeError: pass

    @on_trait_change('opts:rh_surfs_on')
    def chg_rh_surfmask(self):
        try: self.dv_3d.syrf_rh.visible=self.opts.rh_surfs_on
        except AttributeError: pass

    @on_trait_change('opts:conns_colors_on')
    def chg_conns_colors(self):
        try:
            if self.opts.conns_colors_on:
                self.dv_3d.vectors.glyph.color_mode='color_by_scalar'
            else:
                self.dv_3d.vectors.glyph.color_mode='no_coloring'
        except AttributeError: pass

    @on_trait_change('opts:conns_colorbar')
    def chg_conns_colorbar(self):
        try: self.dv_3d.set_colorbar(self.opts.conns_colorbar,
            self.dv_3d.vectors, orientation='horizontal')
        except AttributeError: pass

    @on_trait_change('opts:conns_width')
    def chg_conns_width(self):
        try: self.dv_3d.vectors.actor.property.line_width=self.opts.conns_width
        except AttributeError: pass

    @on_trait_change('opts:default_map.[cmap,reverse,fname,threshold]')
    def chg_default_map(self):
        try: 
            self.draw_nodes()
        except:
            map_def = self.opts.default_map
            if map_def.cmap == 'file' and not map_def.fname:
                pass
            else:
                raise

    @on_trait_change('opts:scalar_map.[cmap,reverse,fname,threshold]')
    def chg_scalar_map(self):
        try:
            self.draw_surfs()
            self.draw_nodes()
        except:
            map_sca = self.opts.scalar_map
            if map_sca.cmap == 'file' and not map_sca.fname:
                pass
            else:
                raise

    @on_trait_change('opts:activation_map.[cmap,reverse,fname,threshold]')
    def chg_activation_map(self): 
        #we don't touch the circle plot here since circle redraw is expensive
        try:
            self.dv_3d.draw_conns()
        except:
            map_act = self.opts.activation_map
            if map_act.cmap == 'file' and not map_act.fname:
                pass
            else:
                raise
        
    @on_trait_change('opts:connmat_map.[cmap,reverse,fname,threshold]')
    def chg_connmat_map(self): 
        try:
            self.dv_mat.change_colormap()
        except:
            map_mat = self.opts.connmat_map
            if map_mat.cmap == 'file' and not map_mat.fname:
                pass
            else:
                raise

    ######################################################################
    # MISCELLANEOUS HELPERS
    ###################################################################### 
    def error_dialog(self,str):
        return self.gui.error_dialog(str)
    
    def warning_dialog(self,str):
        return self.gui.warning_dialog(str)

    def verbose_msg(self,str):
        return self.gui.verbose_msg(str)
    
    def get_module(self):
        if self.cur_module=='custom':
            return self.custom_module
        elif isinstance(self.cur_module,int) and self.modules is not None:
            return self.modules[self.cur_module]

    ## END DATASET
