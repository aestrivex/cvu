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



import os
from traits.api import (Directory, Str)
from traitsui.api import (Item, HGroup, VGroup, View, HistoryEditor,
    DirectoryEditor)
from traitsui.file_dialog import OpenFileDialog

#reimplementation of OpenFileDialog for directory selection

class OpenDirectoryDialog(OpenFileDialog):
    file_name = Directory

    id = Str('OpenDirectoryDialog')

    def _get_is_valid_file(self):
        if self.is_save_file:
            return (os.path.isdir(self.file_name) or (os.path.exists(
                self.file_name)))

        return os.path.isdir(self.file_name) or os.path.isfile(self.file_name)

    def open_file_view(self):
        item=Item( 'file_name',
                    id      = 'file_tree',
                    style   = 'custom',
                    show_label = False,
                    width   = 0.5,
                    editor = DirectoryEditor( filter = self.filter,
                                            allow_dir = True,
                                            reload_name = 'reload',
                                            dclick_name = 'dclick',))
        width=height=0.20

        if len(self.extensions) > 0:
            raise Exception('extensions are not supported')


        return View (
            VGroup(
                VGroup( item ),
                HGroup(
                    Item( 'create',
                          id           = 'create',
                          show_label   = False,
                          style        = 'custom',
                          defined_when = 'is_save_file',
                          enabled_when = 'can_create_dir',
                          tooltip      = 'Create a new directory'
                    ),
                    Item( 'file_name',
                          id      = 'history',
                          editor  = HistoryEditor( entries  = self.entries,
                                                   auto_set = True ),
                          springy = True
                    ),
                    Item( 'ok',
                          id           = 'ok',
                          show_label   = False,
                          enabled_when = 'is_valid_file'
                    ),
                    Item( 'cancel',
                          show_label = False
                    )
                )
            ),
            title        = self.title,
            id           = self.id,
            kind         = 'livemodal',
            width        = width,
            height       = height,
            close_result = False,
            resizable    = True
        )

def open_directory(**traits):
    fd=OpenDirectoryDialog(**traits)
    if fd.edit_traits( view='open_file_view' ).result:
        return fd.file_name
    else:
        return ''

