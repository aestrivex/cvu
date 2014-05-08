try:
	os.makedirs('../tests/')
except:
	pass

try:
	os.remove('../tests/output/first_3D.png')
except:
	pass

try:
	os.remove('../tests/output/sparc_3D.png')
except:
	pass

try:
	os.remove('../tests/output/sparc_mat.png')
except:
	pass

try:
	os.remove('../tests/output/sparc_circ.png')
except:
	pass

#the incorrect scaling is done on whichever method goes first

from mayavi import mlab
#print self.controller.ds_orig.dv_3d.scene.mayavi_scene

#mlab.savefig('../tests/output/direct3d.png',figure=self.controller.ds_orig.dv_3d.scene.mayavi_scene,size=(694,694))


self.save_snapshot_window.ctl.dpi=100

self.save_snapshot_window.ctl.whichplot='connection matrix'
self.save_snapshot_window.ctl.savefile='../tests/output/sparc_mat.png'
self.save_snapshot_window.finished=True
self.save_snapshot_window.notify=True

#self.controller.ds_orig.dv_3d.hack_mlabsavefig('../tests/output/test3d.png',
#	size=(694,694))

print self.controller.ds_orig.dv_3d.scene.scene_editor.light_manager

self.save_snapshot_window.ctl.whichplot='3D brain'
self.save_snapshot_window.ctl.savefile='../tests/output/first_3D.png'
self.save_snapshot_window.finished=True
self.save_snapshot_window.notify=True

self.save_snapshot_window.ctl.whichplot='3D brain'
self.save_snapshot_window.ctl.savefile='../tests/output/sparc_3D.png'
self.save_snapshot_window.finished=True
self.save_snapshot_window.notify=True

self.save_snapshot_window.ctl.whichplot='circle plot'
self.save_snapshot_window.ctl.savefile='../tests/output/sparc_circ.png'
self.save_snapshot_window.finished=True
self.save_snapshot_window.notify=True

sys.exit(0)
