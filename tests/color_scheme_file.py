self.controller.ds_orig.opts.default_map.cmap='file'
self.controller.ds_orig.opts.default_map.fname='cmaps/sample_heat.lut'
self.controller.ds_orig.opts.activation_map.cmap='file'
self.controller.ds_orig.opts.activation_map.fname='cmaps/sample_heat.lut'
self.controller.ds_orig.opts.connmat_map.cmap='file'
self.controller.ds_orig.opts.connmat_map.fname='cmaps/sample_heat.lut'

load_parc('laus125', 'orders/laus125_cmp.txt', dataset=self.controller.ds_orig)
load_adj('data/sample_gqi.npy', self.controller.ds_orig)
