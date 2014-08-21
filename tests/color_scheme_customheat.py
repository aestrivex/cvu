self.controller.ds_orig.opts.default_map.cmap='custom_heat'
self.controller.ds_orig.opts.activation_map.cmap='custom_heat'
self.controller.ds_orig.opts.connmat_map.cmap='custom_heat'

load_parc('laus125', 'orders/laus125_cmp.txt', dataset=self.controller.ds_orig)
load_adj('data/sample_gqi.npy', self.controller.ds_orig)
