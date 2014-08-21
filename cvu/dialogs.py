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

from traits.api import (HasTraits,Bool,Event,File,Int,Str,Directory,Function,
    Enum,List,Button,Range,Instance,Float,Trait,Any,CFloat,Property,Either,
    on_trait_change)
from traitsui.api import (Handler,View,Item,OKCancelButtons,OKButton,
    CancelButton,Spring,InstanceEditor,
    Group,ListStrEditor,CheckListEditor,HSplit,FileEditor,VSplit,Action,HGroup,
    TextEditor,ImageEnumEditor,UIInfo,Label,VGroup,ListEditor,TableEditor,
    ObjectColumn)
from traitsui.file_dialog import open_file
import os; import traceback
from utils import DatasetMetadataElement,CVUError
from color_map import CustomColormap
from custom_file_editor import CustomFileEditor, CustomDirectoryEditor

#this is pretty scary that this works in the global namespace and not if the
#Item is a child attribute of InteractiveSubwindow.
current_dataset_item=Item('_current_dataset_list',show_label=False,
    editor=CheckListEditor(name='all_datasets'),style='simple',height=25)

#UNUSED TITLES

class InteractiveSubwindow(Handler):
    finished=Bool(False)
    notify=Event
    info=Instance(UIInfo)
    window_active=Bool(False)
    def __init__(self,**kwargs):
        super(InteractiveSubwindow,self).__init__(**kwargs)
    def init_info(self,info):
        self.info=info
        self.finished=False
        self.window_active=True
    def closed(self,info,is_ok):
        info.object.finished=is_ok
        info.object.notify=True
        self.window_active=False
    def reconstruct(self):
        #self.window_active=False

        #maybe the user spawned multiple copies and closed some himself
        if self.info.ui is not None:
            self.info.ui.dispose()
        self.info.object.edit_traits()
    def conditionally_dispose(self):
        if self.window_active:
            self.info.ui.dispose()

class DatasetSpecificSubwindow(DatasetMetadataElement,InteractiveSubwindow):
    ctl=Any				#window control for this window
    def __init__(self,ctl,controller,**kwargs):
        super(DatasetSpecificSubwindow,self).__init__(controller,**kwargs)
        self.ctl=ctl	
    #this is handler init, called on traitsui initialization
    def init_info(self,info):
        if self.current_dataset is None:
            self._current_dataset_list=[self._controller.ds_orig]
        super(DatasetSpecificSubwindow,self).init_info(info)

class UnstableDatasetSpecificSubwindow(DatasetSpecificSubwindow):
    @on_trait_change('current_dataset')
    def _chg_ds_ref(self):
        try: self.ctl.ds_ref=self.current_dataset
        #this fails on setup before ctl is initialized so ignore error messages
        except AttributeError: pass 

############################################################################
class OptionsWindow(DatasetSpecificSubwindow):
    conns_disclaimer=Str
    initial_graphopts_list=List(Str)

    edit_cmap_button=Button('Colormap customizer')
    reset_default_cmaps_button=Button('Reset defaults')

    _stupid_listener,_stupid_listener_2=Bool,Bool

    def cmap_group_view(m):
        return Group(Item(name='label',object='object.ctl.%s'%m,
                        style='readonly'),
                    Item(name='cmap',object='object.ctl.%s'%m,
                        editor=ImageEnumEditor(path=CustomColormap.imgs_path,
                            values=CustomColormap.lut_list,cols=7)),
                    Item(name='fname',object='object.ctl.%s'%m,
                        editor=CustomFileEditor(),
                        enabled_when='ctl.%s.cmap==\'file\''%m),
                    HGroup(
                        Item(name='reverse',object='object.ctl.%s'%m)
                    ),
                    Item(name='threshold',object='object.ctl.%s'%m,
                        enabled_when='ctl.%s.cmap==\'custom_heat\''%m),
                    show_labels=False)

    traits_view=View(
        VGroup(
            current_dataset_item,
            HSplit(
                Item(name='pthresh',object='object.ctl',
                    label='percent threshold',
                    enabled_when='object.ctl.thresh_type==\'prop\''),
                Item(name='athresh',object='object.ctl',
                    label='absolute threshold',
                    enabled_when='object.ctl.thresh_type==\'abs\''),
                Item(name='thresh_type',object='object.ctl',
                    label='threshold type'),
            ),
            HSplit(
                Item(name='module_view_style',object='object.ctl',
                    label='module connection style'),
            ),
            HSplit(
                Item(name='conns_colors_on',object='object.ctl',
                    label='color on'),
                Item(name='conns_colorbar',object='object.ctl',
                    label='colorbar'),
                Item(name='tube_conns',object='object.ctl',label='use tubes'),
                Item(name='conns_width',object='object.ctl',label='width'),
            ),
            HSplit(
                Item(name='interhemi_conns_on',object='object.ctl',
                    label='interhemispheric_conns_on'),
                Item(name='lh_conns_on',object='object.ctl',
                    label='LH conns on'),
                Item(name='rh_conns_on',object='object.ctl',
                    label='RH conns on'),
            ),
            HSplit(
                Item(name='conns_disclaimer',style='readonly',height=10,
                    width=550,show_label=False)
            ),
            label='Connection settings',show_labels=False),
        VGroup(
            current_dataset_item,
            HSplit(
                Item(name='show_floating_text',object='object.ctl',
                    label='floating 3D text on'),
                Item(name='scalar_colorbar',object='object.ctl',
                    label='show scalar colorbar'),
            ),
            HSplit(
                Item(name='render_style',object='object.ctl',
                    label='surface style'),
                Item(name='surface_visibility',object='object.ctl',
                    label='surface opacity'),
            ),
            HSplit(
                Item(name='lh_nodes_on',object='object.ctl',
                    label='LH nodes on'),
                Item(name='rh_nodes_on',object='object.ctl',
                    label='RH nodes on'),
            ),
            HSplit(
                Item(name='lh_surfs_on',object='object.ctl',
                    label='LH surfaces on'),
                Item(name='rh_surfs_on',object='object.ctl',
                    label='RH surfaces on'),
            ),
            HSplit(
                Item(name='circ_symmetry',object='object.ctl',
                    label='circle symmetry type'),
                Item(name='circle_render',object='object.ctl',
                    label='circle rendering'),
                #Item(name='circ_size',object='object.ctl'),
            ),
            label='Display settings',show_labels=False
        ),
        VGroup(
            current_dataset_item,
            HGroup(
                cmap_group_view('default_map'),
                cmap_group_view('scalar_map'),
                cmap_group_view('activation_map'),
                cmap_group_view('connmat_map'),
            ),
            HGroup(
                Item(name='edit_cmap_button'),
                Item(name='reset_default_cmaps_button'),
                show_labels=False
            ),
            label='Colors',show_labels=False
        ),
        VGroup(
            current_dataset_item,
            Item(name='intermediate_graphopts_list',object='object.ctl',
                editor=CheckListEditor(name='initial_graphopts_list'),			
                show_label=False, style='custom'),
            label='Graph statistics',show_labels=False
        ),
        kind='panel',buttons=OKCancelButtons,
        title='Select your desired destiny',
    )

    #def __init__(self,ctl,controller,**kwargs):
    #	super(OptionsWindow,self).__init__(ctl,controller,**kwargs)

        #setup stupid listeners for colormap traits
    #	for cmap in ('default','scalar','activation','connmat'):
    #		self.on_trait_change(lambda:self._stupid_listen_1('%s_map'%cmap),
    #			'ctl:%s_map:cmap'%cmap)

    def _initial_graphopts_list_default(self):
        return ['global efficiency', 'local efficiency', 'average strength',
            'clustering coefficient', 'eigenvector centrality', 'binary kcore',
             'modularity', 
            'participation coefficient', 'within-module degree']
    def _conns_disclaimer_default(self):
        return ("Note changing conn visibility is not applied immediately as "
            "it can be costly. To force application, click 'Reset Display'")

    def _edit_cmap_button_fired(self):
        from tvtk import util as tvtk_util; import sys,subprocess
        script=os.path.join(os.path.dirname(tvtk_util.__file__),
            '%s_gradient_editor.py')
        try:
            import Tkinter, tkFileDialog
            script=script%'tk'
        except ImportError:
            raise NotImplementedError('Tk not available for gradient editor toolkit')
            script=script%'wx'
        subprocess.Popen([sys.executable, script])
    def _reset_default_cmaps_button_fired(self,info):
        for map in (self.default_map,self.scalar_map,self.activation_map,
                self.connmat_map):
            map.reset_traits(['cmap','fname','reverse','threshold'])

    @on_trait_change('ctl:thresh_type')
    def _stupid_listen_1(self):
        self._stupid_listener=self.ctl.thresh_type=='abs'

    @on_trait_change('ctl:default_map:cmap')
    def _stupid_listen_2(self):
        self._stupid_listener=self.ctl.default_map.cmap=='file'
        self._stupid_listener_2=self.ctl.default_map.cmap=='custom_heat'

    @on_trait_change('ctl:scalar_map:cmap')
    def _stupid_listen_3(self):
        self._stupid_listener=self.ctl.scalar_map.cmap=='file'
        self._stupid_listener_2=self.ctl.scalar_map.cmap=='custom_heat'

    @on_trait_change('ctl:activation_map:cmap')
    def _stupid_listen_4(self):
        self._stupid_listener=self.ctl.activation_map.cmap=='file'
        self._stupid_listener_2=self.ctl.activation_map.cmap=='custom_heat'

    @on_trait_change('ctl:connmat_map:cmap')
    def _stupid_listen_5(self):
        self._stupid_listener=self.ctl.connmat_map.cmap=='file'
        self._stupid_listener_2=self.ctl.connmat_map.cmap=='custom_heat'

###########################################################################
class CalculateWindow(UnstableDatasetSpecificSubwindow):
    _stupid_listener=Bool
    traits_view=View(
        current_dataset_item,
        Item(name='calculation_type',object='object.ctl'),
        Item(name='athresh',object='object.ctl',
            enabled_when='object.ctl.thresh_type==\'abs\''),
        Item(name='pthresh',object='object.ctl',
            enabled_when='object.ctl.thresh_type==\'prop\''),
        Item(name='thresh_type',object='object.ctl'),
        kind='panel',buttons=OKCancelButtons,width=350,height=200,
        title='log(pi^pi) with base pi is exactly 3')

    @on_trait_change('ctl:thresh_type')
    def _stupid_listen(self):
        self._stupid_listener=self.ctl.thresh_type=='abs'

###########################################################################
class GraphTheoryWindow(UnstableDatasetSpecificSubwindow):
    RecalculateButton=Action(name='Recalculate',action='do_recalculate')
    SaveToScalarButton=Action(name='Save to scalar',action='do_sv_scalar')
    
    new_view=View(
        current_dataset_item,
        VGroup(
            HGroup(
                Item(name='graph_stats',object='object.ctl',style='custom',
                    editor=ListEditor(use_notebook=True,page_name='.name',
                        selected='object.ctl.current_stat'),
                    show_label=False,),
            ),
            HGroup(
                Item(name='scalar_savename',object='object.ctl',
                    label='Scalar name',height=25,width=180),
            ),
        ),
        height=400,width=350,
        title='Mid or feed',kind='panel',
        buttons=[SaveToScalarButton,OKButton,])

    #before version 4.4.1 of traitsui there was a bug such that list editors
    #in notebook mode crash when the model object is specified in extended
    #name notation. so instead we create a view with a local model object
    old_view=View(
        VGroup(
            HGroup(
                Item(name='ctl',style='custom',
                    editor=InstanceEditor(view='old_traitsui_view')),
            ),
            HGroup(
                Item(name='scalar_savename',object='object.ctl',
                    label='Scalar name',height=25,width=180),
            ),
        ),
        height=400,width=350,
        title='Mid or feed',kind='panel',
        buttons=[SaveToScalarButton,OKButton,])

    from traitsui import __version__ as version
    if version[:3] < 4.4 or (version[:3]==4.4 and version[4]==0):
        traits_view=old_view
    else:
        traits_view=new_view

    #handler methods
    def do_sv_scalar(self,info):
        self.ctl._proc_save_to_scalar()
    def do_recalculate(self,info):
        self.ctl._proc_recalculate()

############################################################################
class AdjmatChooserWindow(UnstableDatasetSpecificSubwindow):
    please_note=Str("All but first field are optional.  Specify adjmat order "
        "if the desired display order differs from the existing matrix order."
        "  Specify unwanted channels as 'delete' in the label order.  Data "
        "field name applies to the data field for .mat matrices only.")
    require_note=Str('Enter any ROIs you would like to force to display on the '
        'circle plot.  You must spell them precisely, e.g. "lh_frontalpole"')
    open_adjmat_order=Button('Browse')
    RequireButton=Action(name='clear all req\'d ROIs',action='do_rqls_clear')

    traits_view=View(
        Group(
            current_dataset_item,
            Item(name='please_note',style='readonly',height=140,width=250),
            Item(name='adjmat',object='object.ctl',label='Adjmat',
                editor=CustomFileEditor()),
            Item(name='adjmat_order',object='object.ctl',label='Label Order',
                editor=CustomFileEditor()),
            Item(name='max_edges',object='object.ctl',label='Max Edges'),
            Item(name='field_name',object='object.ctl',
                label='Field (.mat files)',editor=TextEditor()),
            Item(name='ignore_deletes',object='object.ctl',
                label='Ignore deletes'),
        label='Matrix'),
        Group(
            VGroup(
                current_dataset_item,
                Item(name='require_note',style='readonly',height=50,width=250,
                    label='Please note'),
                Item(name='require_ls',object='object.ctl',
                    editor=ListStrEditor(auto_add=True,editable=True),
                    label='List ROIs here'),
            ),
            VGroup(
                Item(name='suppress_extra_rois',object='object.ctl',
                    label='Show only labels listed here'),
            ),
        label='required ROIs'),
    
        kind='panel',buttons=[RequireButton,OKButton,CancelButton],
        title='Report all man-eating vultures to security',)

    #handler methods
    def do_rqls_clear(self,info):
        info.object.ctl.require_ls=[]

############################################################################
class ParcellationChooserWindow(UnstableDatasetSpecificSubwindow):
    _stupid_listener=Bool
    Please_note=Str('fsaverage5 is fine unless individual morphology '
        'is of interest.  Visualizing tractography requires individual '
        'morphology. Using the pial surface is recommended.')
    traits_view=View(
        current_dataset_item,
        HGroup(
            Item(name='new_dataset',object='object.ctl',label='new dataset'),
            Item(name='new_dataset_name',object='object.ctl',
                enabled_when='object.ctl.new_dataset'),
        ),
        Group(
            Item(name='Please_note',style='readonly',height=85,width=250),
            Item(name='subject',object='object.ctl',label='SUBJECT'),
            Item(name='subjects_dir',object='object.ctl',label='SUBJECTS_DIR',
                editor=CustomDirectoryEditor()),
            Item(name='parcellation_name',object='object.ctl',
                label='Parcellation'),
            Item(name='labelnames_file',object='object.ctl',
                label='Label Display Order',editor=CustomFileEditor()),
            Item(name='surface_type',object='object.ctl'),
        ), kind='panel',buttons=OKCancelButtons,
            title="This should not be particularly convenient",)

    #what! why does this work since the stupid listener is actually ignored
    @on_trait_change('ctl:new_dataset')
    def _stupid_listen(self):
        self._stupid_listener=self.ctl.new_dataset

############################################################################
class TractographyChooserWindow(UnstableDatasetSpecificSubwindow):
    Please_note=Str(
        'Tractography registration is approximate and it is strongly recommended that '
        'individual subject morphology be used rather than the fsaverage5 surface.\n'
        'To calculate the alignment cvu needs to use freesurfer\'s bbregister. '
        'If freesurfer environment is not set include the setup script here.\n'
        'All other fields are required.')
    track_file=File
    b0_volume=File
    SUBJECTS_DIR=Directory
    SUBJECT=Str
    fs_setup=File('/usr/local/freesurfer/nmr-stable53-env')
    traits_view=View(
        current_dataset_item,
        Group(
            Item(name='Please_note',style='readonly',height=150,width=325),
            Item(name='track_file',object='object.ctl',label='Tractography (.trk)',
                editor=CustomFileEditor()),
            Item(name='b0_volume',object='object.ctl',label='B0 volume (NIFTI)',
                editor=CustomFileEditor()),
            Item(name='subjects_dir',object='object.ctl',label='SUBJECTS_DIR',
                editor=CustomDirectoryEditor()),
            Item(name='subject',object='object.ctl',label='SUBJECT'),
            Item(name='fs_setup',object='object.ctl',editor=CustomFileEditor()),
        ), kind='panel',buttons=OKCancelButtons,
            title='Just FYI subject 39108 has an abnormal HRF')

############################################################################
class LoadGeneralMatrixWindow(UnstableDatasetSpecificSubwindow):
    _stupid_listener=Bool
    Please_note=Str('Same rules for adjmat ordering files apply')
    whichkind=Enum('modules','scalars')
    traits_view=View(
        current_dataset_item,
        Item(name='Please_note',style='readonly',height=50,width=250),
        Item(name='whichkind',object='object.ctl',label='Load what?'),
        Item(name='mat',object='object.ctl',label='Filename',
            editor=CustomFileEditor()),
        Item(name='mat_order',object='object.ctl',label='Ordering file',
            editor=CustomFileEditor()),
        Item(name='field_name',object='object.ctl',
            label='Field (.mat files only)'),
        Item(name='ignore_deletes',object='object.ctl',label='Ignore deletes'),
        Item(name='measure_name',object='object.ctl',
            label='Name these scalars',
            enabled_when='object.ctl.whichkind==\'scalars\''),
        kind='panel',buttons=OKCancelButtons,
        title='Behold the awesome power of zombies')

    @on_trait_change('ctl:whichkind')
    def _stupid_listen(self):
        self._stupid_listener=self.ctl.whichkind=='scalars'

############################################################################
class ConfigureScalarsWindow(DatasetSpecificSubwindow):
    #idea:
    #node_scalars needs to be DICTIONARY.
    #add field to dictionary upon load scalars.  can replace.
    #three ListStr editors, one for each display method, across the field names
    #the selections can be the same for multiple scalars
    node_col_label=Str('Node color')
    surf_col_label=Str('Surface color')
    node_size_label=Str('Node size')
    circ_label=Str('Circle plot')
    cmat_label=Str('Connection Matrix')

    def _scalar_set(selected_trait):
        return Item(name='scalar_sets',object='object.ctl',
            editor=ListStrEditor(selected='object.ctl.%s'%selected_trait))
    traits_view=View(
        current_dataset_item,
        HGroup(
            Group(
                Item(name='node_col_label',style='readonly'),
                _scalar_set('node_color'),
                show_labels=False
            ),
            Group(
                Item(name='surf_col_label',style='readonly'),
                _scalar_set('surf_color'),
                show_labels=False
            ),
            Group(
                Item(name='node_size_label',style='readonly'),
                _scalar_set('node_size'),
                show_labels=False
            ),
            Group(
                Item(name='circ_label',style='readonly'),
                _scalar_set('circle'),
                show_labels=False
            ),
            Group(
                Item(name='cmat_label',style='readonly'),
                _scalar_set('connmat'),
                show_labels=False
            ),
        ),
        height=450,width=800,buttons=OKCancelButtons,
        title='Your data is probably just spurious artifacts anyway',
    )
    
############################################################################
class NodeChooserWindow(UnstableDatasetSpecificSubwindow):
    traits_view=View(
        current_dataset_item,
        Item(name='node_list',object='object.ctl',
            editor=ListStrEditor(selected_index='object.ctl.cur_node'),
                show_label=False),
        kind='panel',height=350,width=350,buttons=OKCancelButtons,
        resizable=True,title='Do you know the muffin man?')

    @on_trait_change('current_dataset')
    def _rebuild_list(self):
        if self.window_active:
            self.reconstruct()

############################################################################
class ModuleChooserWindow(UnstableDatasetSpecificSubwindow):
    AllModulesButton=Action(name='View all modules',action='do_view_all')

    traits_view=View(
        current_dataset_item,
        Item(name='module_list',object='object.ctl',
            editor=ListStrEditor(editable=True,
                selected_index='object.ctl.cur_mod'),
            show_label=False),
        kind='panel',height=350,width=350,resizable=True,
        buttons=[AllModulesButton,OKButton,CancelButton],
        title='Roll d12 for dexterity check')

    #handler methods

    #having handler methods call the dataset directly is ok as long as
    #they just make simple calls to the dataset and dont do processing here
    def do_view_all(self,info):
        self.ctl.ds_ref.display_multi_module()

############################################################################
class ModuleCustomizerWindow(UnstableDatasetSpecificSubwindow):
    ClearButton=Action(name='Clear Selections',action='do_clear')
    traits_view=View(
        current_dataset_item,
        Item(name='intermediate_node_list',object='object.ctl',
            editor=CheckListEditor(name='object.ctl.initial_node_list',cols=2),
            show_label=False,style='custom'),
        kind='panel',height=400,width=500,
        buttons=[ClearButton,OKButton,CancelButton],
        resizable=True,scrollable=True,title='Mustard/Revolver/Conservatory')

    #handler methods
    def do_clear(self,info):
        info.object.ctl.intermediate_node_list=[]

    @on_trait_change('current_dataset')
    def _rebuild_list(self):
        if self.window_active:
            self.reconstruct()

############################################################################
class SaveSnapshotWindow(UnstableDatasetSpecificSubwindow):
    traits_view=View(Group(
        current_dataset_item,
        Item(name='savefile',object='object.ctl'),
        Item(name='whichplot',object='object.ctl',label='view'),
        Item(name='dpi',object='object.ctl',label='dots per inch'),
    ), kind='panel',buttons=OKCancelButtons,
        title="Help I'm a bug",height=250,width=250)

############################################################################
class MakeMovieWindow(UnstableDatasetSpecificSubwindow):
    please_note=Str("Making movies relies on the ability to record an X11 "
        "desktop. It won't run on non-X11 systems.")
    traits_view=View(Group(
        current_dataset_item,
        Item(name='please_note',style='readonly',height=25,width=250),
        Item(name='savefile',object='object.ctl'),
        Item(name='framerate',object='object.ctl',label='framerate'),
        Item(name='bitrate',object='object.ctl',label='bitrate (kb/s)'),
        Item(name='anim_style',object='object.ctl',
            label='automatically rotate'),
        Item(name='samplerate',object='object.ctl',label='animation speed (Hz)'),
        Item(name='debug',object='object.ctl',label='debug ffmpeg'),
    ), kind='panel',buttons=OKCancelButtons,title="Make me a sandwich")

############################################################################
class ReallyOverwriteFileWindow(InteractiveSubwindow):
    Please_note=Str('That file exists. Really overwrite?')
    save_continuation=Function # Continuation passing style
        #this should technically be stored in a parameters but it is
        #completely contained in the GUI interaction
    traits_view=View(Spring(),
        Item(name='Please_note',style='readonly',height=25,width=250,
            show_label=False),
        Spring(),
        kind='panel',buttons=OKCancelButtons,
        title='Your doom awaits you')

############################################################################
class ColorLegendWindow(UnstableDatasetSpecificSubwindow):
    import color_legend
    traits_view=View(
        current_dataset_item,
        Item(name='entries',object='object.ctl.legend',
            editor=TableEditor(columns=
                [ObjectColumn(label='ROI',editor=TextEditor(),name='metaregion',
                    style='readonly',editable=False),
                color_legend.ColorColumn(label='color',editor=TextEditor(),
                    name='blank',editable=False)],
                selection_bg_color=None,),
            show_label=False),
        kind='panel',height=500,width=325,resizable=True,
        title='Fresh artichokes just -$3/lb',)

    @on_trait_change('current_dataset')
    def _rebuild_list(self):
        if self.window_active:
            self.reconstruct()

############################################################################
class ErrorDialogWindow(Handler):
    error=Str
    stacktrace=Either(Instance(traceback.types.TracebackType),None)
    StackTraceButton=Action(name='print stack to console',action='do_stack_trace')
    traits_view=View(Item(name='error',style='readonly',height=75,width=300),
        buttons=[StackTraceButton,OKButton],kind='nonmodal',
        title='Evil mutant zebras did this',)

    def do_stack_trace(self,info):
        if self.stacktrace is not None:
            
            try:
                traceback.print_tb(self.stacktrace)
            except:
                traceback.print_stack()
                print "The stack trace passed along with this error was not valid!"
                print "The entire accessible stack was printed instead"
                
        else:
            traceback.print_stack()
            print "There is no stack trace available for this error!"
            print "The entire accessible stack was printed instead"

class WarningDialogWindow(HasTraits):
    warning=Str
    traits_view=View(Item(name='warning',style='readonly',height=75,width=300),
        buttons=[OKButton],kind='nonmodal',
        title='Evil mutant zebras did this',)

class AboutWindow(HasTraits):
    message=Str('cvu version 0.4\n'
        'cvu is copyright (C) Roan LaPlante 2013\n\n'
        'cvu strictly observes the tenets of fundamentalist Theravada Mahasi\n'
        'style Buddhism.  Any use of cvu in violation of the tenets of\n'
        'fundamentalist Theravada Mahasi style Buddhism or in violation of\n'
        'the theosophical or teleological principles as described\n'
        'in the Vishuddhimagga Sutta is strictly prohibited and punishable by\n'
        'extensive Mahayana style practice.  By being or not being mindful of\n'
        'the immediate present moment sensations involved in the use of cvu,\n'
        'you confer your acceptance of these terms and conditions.\n\n'

        'cvu is distributed without warranty unless otherwise prohibited by\n'
        'law.  cvu is licensed under the GNU GPL v3.  a license is contained\n'
        'with the distribution of this program.  you may modify and convey\n'
        'this program to others in accordance with the terms of the GNU\n'
        'GPLv3 or optionally any subsequent version of the GNU GPL.\n\n'

        'Please note that modest noncompliance with the tenets of\n'
        'fundamentalist Mahasi style Buddhism is typically overlooked as long\n'
        'as the licensing requirements of the GPL are upheld.'
    )
    traits_view=View(Item(name='message',style='readonly',show_label=False),
        buttons=[OKButton],kind='nonmodal',height=400,width=450,
        title='Greetings, corporeal being',)
