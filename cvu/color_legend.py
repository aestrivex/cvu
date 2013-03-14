# (C) Roan LaPlante 2013 rlaplant@nmr.mgh.harvard.edu



from traits.api import HasTraits,Str,List,RGBColor,Any
from traitsui.api import View,Item,TableEditor,TextEditor,ObjectColumn

class ColorColumn(ObjectColumn):
	def get_cell_color(self,object):
		#quick-and-dirty conversion from rgbcolor to color
		#TODO less hacky?
		return tuple(map(lambda c:int(round(c*255)),object.col))

class LegendEntry(HasTraits):
	metaregion=Str
	col=Any #RGBColor doesn't support alpha.  It is easier to convert the
	#matplotlib alpha value to Color directly which does support alpha
	blank=Str('')
	def __init__(self,**traits):
		super(LegendEntry,self).__init__(**traits)

class ColorLegendWindow(HasTraits):
	legend=List(LegendEntry)
	traits_view=View(Item(name='legend',
		editor=TableEditor(columns=
			[ObjectColumn(label='ROI',editor=TextEditor(),
				name='metaregion',style='readonly',editable=False),
			ColorColumn(label='color',editor=TextEditor(),
				name='blank',editable=False)],
			selection_bg_color=None,),show_label=False),
		kind='nonmodal',height=500,width=325,resizable=True,
		title='Fresh artichokes just -$3/lb',)
