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


from chaco.api import PlotAxis,LinearMapper
import numpy as np
from traits.api import RGBColor,List,Any,Enum,HasTraits,Instance,Int

def rcol():
    return tuple(np.random.random(3)).__add__((1,))

class ColorfulAxis(PlotAxis):
    colors=List(Any)
    direction=Enum('x','y',None)

    def __init__(self,component,color_list,direction,**traits):
        super(ColorfulAxis,self).__init__(component=component,**traits)
    
        self.colors=color_list
        self.ensure_labels_bounded=True
        self.axis_line_visible=False
        self.tick_interval=1
        self.tick_weight=2

        self.direction=direction
        if self.direction=='x':
            self.orientation='bottom'
        elif self.direction=='y':
            self.orientation='left'
    
    def _draw_ticks(self,gc):
        if not self.tick_visible:
            return
        gc.set_line_width(self.tick_weight)
        gc.set_antialias(False)
        #tick_in_vector = self._inside_vector*self.tick_in
        tick_out_vector = self._inside_vector*self.tick_out*2
        #print self._tick_positions
        
        if self.direction=='x':
            self.mapper=self.component.x_mapper
        elif self.direction=='y':
            self.mapper=self.component.y_mapper

        min_scr=self.mapper.range.low
        max_scr=self.mapper.range.high

        #deal with the edge cases
        if min_scr-int(min_scr)==0:
            #the tick at r is preserved and i'll put at r+.5
            min_r=int(min_scr)
        elif min_scr-int(min_scr)<=.5:
            #i need a tick at r+.5 but i don't have one, take the one from r-1
            min_r=int(np.floor(min_scr))
        elif min_scr-int(min_scr)>.5:
            #don't need a tick at r+.5, don't have a tick at r, start at r+1
            min_r=int(np.ceil(min_scr))
        else:
            raise IndexError('Internal error in ColorfulAxis min')

        if max_scr-int(max_scr)<.5:
            #i have a superfluous tick at r, get rid of it
            max_r=int(np.floor(max_scr))
        elif max_scr-int(max_scr)>=.5:
            #the tick at r will be displayed at r+.5, stop at r+1
            max_r=int(np.ceil(max_scr))
        else:
            raise IndexError('Internal error in ColorfulAxis max')

        moddiv=int(np.ceil(max((max_r-min_r)//75,1)))
        inds=xrange(min_r,max_r,moddiv)
        nr_ticks=len(inds)

        # add .5 to each tick to place them in the center of the grid
        ticks_axis=self.mapper.map_screen(np.array(inds)+.5)
        ticks_static=np.tile(48,(nr_ticks,))

        if self.direction=='x':
            ticks=np.vstack((ticks_axis,ticks_static)).T
        elif self.direction=='y':
            ticks=np.vstack((ticks_static,ticks_axis)).T

        for tick_pos,i in zip(ticks,inds):
            if i<0 or i>=len(self.colors):
                #gc.set_stroke_color((0,0,0))
                continue
            else:
                gc.set_stroke_color(self.colors[i])
            gc.begin_path()
            gc.move_to(*(tick_pos))
            gc.line_to(*(tick_pos - tick_out_vector))
            gc.stroke_path()
        return

    def _draw_labels(self,gc):
        pass
