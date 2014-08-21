load_parc('laus125', 'orders/laus125_cmp.txt', dataset=self.controller.ds_orig)
load_adj('data/sample_gqi.npy', self.controller.ds_orig)

self.controller.ds_orig.calculate_graph_stats(1) #threshold as argument
#this function does not block. the blocking is done in the GUI

self.controller.ds_orig.opts.scalar_map.cmap='custom_heat'
self.controller.ds_orig.opts.scalar_map.reverse=True

self.configure_scalars_window.ctl.node_size='eigenvector centrality'
self.configure_scalars_window.ctl.node_color='clustering coefficient'
self.configure_scalars_window.ctl.connmat='average strength'
self.configure_scalars_window.ctl.circle='binary kcore'
self.controller.ds_orig.display_scalars()
