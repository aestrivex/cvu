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

self.save_snapshot_window.ctl.whichplot='3D brain'
self.save_snapshot_window.ctl.savefile='../tests/output/sparc_3D.png'
self.save_snapshot_window.ctl.dpi=100
self.save_snapshot_window.finished=True
self.save_snapshot_window.notify=True

from mayavi import mlab
mlab.savefig('../tests/output/direct3d.png',figure=self.controller.ds_orig.dv_3d.scene.mayavi_scene,size=(694,694))

self.save_snapshot_window.ctl.whichplot='connection matrix'
self.save_snapshot_window.ctl.savefile='../tests/output/sparc_mat.png'
self.save_snapshot_window.finished=True
self.save_snapshot_window.notify=True

self.save_snapshot_window.ctl.whichplot='circle plot'
self.save_snapshot_window.ctl.savefile='../tests/output/sparc_circ.png'
self.save_snapshot_window.finished=True
self.save_snapshot_window.notify=True
