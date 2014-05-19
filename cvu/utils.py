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

from traits.api import (HasTraits,Any,Property,List,Str)
from traitsui.api import (View,Item)

class CVUError(Exception):
    pass 

class DisplayMetadata(HasTraits):
    subject_name=Str
    parc_name=Str
    adj_filename=Str

    traits_view = View(
        Item('subject_name',style='readonly'),
        Item('parc_name',style='readonly'),
        Item('adj_filename',style='readonly',width=250,height=5),)

class DatasetMetadataElement(HasTraits):
    _controller=Any				#Controller for the entire program
    all_datasets=Property(depends_on='_controller:datasets')
    def _get_all_datasets(self):
        return self._controller.ds_instances.values()

    _current_dataset_list=List	#List(Dataset)
    current_dataset=Property(depends_on='_current_dataset_list')
    def _get_current_dataset(self):
        try: return self._current_dataset_list[0]	
        except IndexError: return None

    def __init__(self,controller,dataset=None,**kwargs):
        super(DatasetMetadataElement,self).__init__(**kwargs)
        self._controller=controller
        if dataset==None:
            self._current_dataset_list=[controller.ds_orig]
        else:
            self._current_dataset_list=[dataset]

# file chooser functions are deprecated 
def file_chooser(**kwargs):
    # use kwarg initialdir='/some_path'
    from Tkinter import Tk
    Tk().withdraw()
    from tkFileDialog import askopenfilename
    return askopenfilename(**kwargs)

def fancy_file_chooser(main_window):
    from traits.api import HasPrivateTraits,File,Str,on_trait_change
    from traitsui.api import View,Item,FileEditor,OKCancelButtons

    class FileChooserWindow(HasPrivateTraits):
        f=File
        _fn=Str
        traits_view=View(
            Item(name='_fn',show_label=False),
            Item(name='f',editor=FileEditor(),style='custom',
                height=500,width=500,show_label=False),
            buttons=OKCancelButtons,kind='nonmodal',
            title="This should be extremely inconvenient")

        @on_trait_change('_fn')
        def f_chg(self):
            self.f=self._fn
    
    main_window.file_chooser_window=FileChooserWindow()
    main_window.file_chooser_window.edit_traits()
