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

from traits.api import (HasTraits,Int,Instance,Range,List,Str,Range,Property,
    Enum,Any,DelegatesTo,Bool,on_trait_change)
from traitsui.api import (View,Item,Group,VSplit,HSplit,NullEditor,Handler,
    InstanceEditor,UIInfo)

from mayavi.core.ui.api import (MayaviScene,SceneEditor,MlabSceneModel)
from dialogs import InteractiveSubwindow
from enable.component_editor import ComponentEditor
from mpleditor import MPLFigureEditor
from utils import CVUError
from chaco.api import Plot
from matplotlib.figure import Figure

class Viewport(Handler):
    ds=Any

    #FIXME there is no reason to have modular viewports anymore since as
    #it turns out the viewport has to be rebuilt in order to update the view.
    #this is something that could be modularly managed.
    #The benefit of changing what now works is however low.  It is basically
    #a very weak form of static type checking, and a way to save a miniscule
    #amount of time and space on managing pointers.




    #by keeping these views on the viewport object itself, we can change
    #the dataset without making traitsui think that the view is inaccessible
    #and it is time to be thrown away immediately upon loading a new dataset
    scene=Instance(MlabSceneModel)
    conn_mat=Instance(Plot)
    circ=Instance(Figure)

    view_type=Enum('dummy','3D Brain','Connection Matrix','Circular plot')

    dummy_view=View(
        Item(editor=NullEditor(),height=500,width=500,label='empty'))

    mayavi_view=View(
        Item(name='scene',
            editor=SceneEditor(scene_class=MayaviScene),
            height=500,width=500,show_label=False,resizable=True))

    matrix_view=View(
        Item(name='conn_mat',
            editor=ComponentEditor(),
            height=500,width=500,show_label=False,resizable=True))

    circle_view=View(
        Item(name='circ',
            editor=MPLFigureEditor(),
            height=500,width=500,show_label=False,resizable=True))

    def __init__(self,ds,**kwargs):
        super(Viewport,self).__init__(**kwargs)
        self.ds=ds

        #it is ok to assign the editors while initializing the viewport
        self.scene=ds.dv_3d.scene
        self.conn_mat=ds.dv_mat.conn_mat
        self.circ=ds.dv_circ.circ

    #MPLEditor wants its interactions to be on the model object
    #this is the "fake" model object so we forward them to the real model object
    def circle_click(self,event): 
        self.ds.dv_circ.circle_click(event)
    def circle_mouseover(self,event,tooltip):
        self.ds.dv_circ.circle_mouseover(event,tooltip)

#more general port layout

#class ViewPanelPortList(HasTraits):
#	ports=List(Instance(Viewport))
#
#	def __getattr__(self,attr):
#		try:
#			if attr[0]=='p':
#				return self.ports[int(attr[1:])]
#			else:
#				raise ValueError
#		except (AttributeError,ValueError,TypeError,IndexError):
#			return self.__getattribute__(attr)

class DatasetViewportInterface(HasTraits):
    mayavi_port,matrix_port,circle_port = (Instance(Viewport),)*3	
    panel_name = Str

class DatasetViewportLayout(DatasetViewportInterface):
    def mkitems(dummies=False):
        if dummies: view_order=('dummy','dummy','dummy')
        else: view_order=('mayavi','matrix','circle')
        for it in view_order:
            yield Item(name='%s_port'%it,style='custom',show_label=False,
                editor=InstanceEditor(view='%s_view'%it),height=500,width=500)

    single_view = View(HSplit(content=[it for it in mkitems()],columns=3),
        height=500,width=1500)
    square_view = View(VSplit(HSplit(content=[it for it in mkitems()][:-1],
        columns=2),HSplit(content=[it for it in mkitems()][-1:],columns=2)),
        height=1000,width=1000)

class ViewPanel(InteractiveSubwindow):
    panel_name=Str('Extra View 1')
    layout=Enum('single','double','square')
    #configurations allowed: 2x3, 1x3, 2x2 (like main window)

    group_1,group_2 = 2*(Instance(DatasetViewportLayout),)

    def __repr__(self): return self.panel_name

    def is_full(self,group=None):
        if group is None and self.layout=='double':
            return self.group_1 is not None and self.group_2 is not None
        elif group in (None,1):
            return self.group_1 is not None
        elif group=='2':
            return self.group_2 is not None
        else: raise ValueError('Invalid value of group')
    
    #TODO determine based on self.layout
    def populate_dummies(self,two_groups=True):
        grps=(self.group_1,self.group_2) if two_groups else (self.group_1,)
        for group in grps:
            group=DatasetViewportLayout()
            group.mayavi_port=Viewport(ds=None)
            group.matrix_port=Viewport(ds=None)
            group.circle_port=Viewport(ds=None)

    #TODO determine based on self.layout
    def populate(self,ds,ds2=None,group=None,force=False):
        if ds2 is not None: grps=('group_1','group_2')	
        elif group==1 or group is None: grps=('group_1',)
        elif group==2: grps=('group_2',)
        elif self.is_full(): raise CVUError('Panel is full')
        else: raise ValueError('Cannot populate ViewPanel with group >=2')

        if not force:
            for group in grps:
                if self.__getattribute__(group) is not None:
                    raise CVUError('Group specified is full, overwrite with '
                        'force=True')

        datasets=( (ds,ds2) if (ds2 is not None) else (ds,) )

        for group,d in zip(grps,datasets):
            dvl=DatasetViewportLayout()
            dvl.mayavi_port=Viewport(ds=d)
            dvl.matrix_port=Viewport(ds=d)
            dvl.circle_port=Viewport(ds=d)
            self.__setattr__(group,dvl)
                 
    def produce_view(self,layout=None):
        produce_item=(lambda ht,wd,grp,lb,vw:
            Item(name=lb,style='custom',show_label=False,#height=ht,width=wd,
                editor=InstanceEditor(view=vw)))

        if layout=='double' or (layout is None and self.layout=='double'):
            return View(
                produce_item(500,1500,self.group_1,'group_1','single_view'),
                produce_item(500,1500,self.group_2,'group_2','single_view'),
                resizable=True,height=1000,width=1500)
        elif layout=='single' or (layout is None and self.layout=='single'):
            return View(
                produce_item(500,1500,self.group_1,'group_1','single_view'),
                resizable=True,height=500,width=1500,title=self.panel_name)
        elif layout=='square' or (layout is None and self.layout=='square'):
            return View(
                produce_item(1000,1000,self.group_1,'group_1','square_view'),
                resizable=True,height=1000,width=1000)
        else: raise ValueError('Invalid layout')

    #handler methods
    def init_info(self,info):
        self.info=info
        self.window_active=True
        self._change_title()

    def conditionally_dispose(self):
        if self.window_active:
            self.info.ui.dispose()
            self.window_active=False

    @on_trait_change('panel_name')
    def _change_title(self):
        try:
            self.info.ui.title=self.panel_name
        #if the panel is renamed when not shown
        #this also occurs on initialization
        except AttributeError: pass

    #this is code written that in principle, permits a maximally generic
    #infrastructure for what viewports should go where on the extra window.
    #
    #in the end allowing maximally generic viewports is not really possible or
    #strictly necessary.  this is a complex problem that might draw slightly
    #from the weirdnesses with scene editor and recreating windows, but mostly
    #from how damn hard it is to deal with tables in traitsui
    #
    #instead, i am going to implement it so that there are a small number of
    #allowed possible configurations showing 3 or 6 views.  The following
    #function tries to do this as well, but doesn't do a great job at it --
    #it is complex, clunky, and requires several arguments to do everything
    #correctly in a few cases.  Which is not the worst thing ever, but is
    #too silly to manage when it is just fine to hardcode the three reasonable
    #possibilities
    #
    #so don't use this function
#	def produce_view(self,nr_groups,cols,dummies=False):
#
#		def generate_items(self,second_group=False,dummies=False):
#			if not dummies:
#				view_order=('mayavi_view','matrix_view','circle_view')
#			else:
#				view_order=('dummy_view','dummy_view','dummy_view')
#			for i,(port,view) in enumerate(zip(self.ports.ports,view_order)):
#				yield Item(name='p%i'%(i+second_group*3),
#					object='object.ports',style='custom',
#					show_label=False,editor=InstanceEditor(view=view),
#					height=500,width=500)
#
#		items=[]	
#		for i in xrange(nr_groups):
#			items.extend([j for j in self.generate_items(i,dummies)])
#		return View(Group(content=items,columns=cols))
