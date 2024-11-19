# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'  # 直接繼承 res.users，不需要新建 _name
    
    vendor_type = fields.Selection([
        ('normal', '一般廠商'),
        ('parallel', '平行廠商'),
    ], string='廠商類型', default='normal')
    
    is_parallel_vendor = fields.Boolean(string='是否為平行廠商', default=False)
    
    @api.onchange('groups_id')
    def _compute_is_portal(self):
        portal_group = self.env.ref('base.group_portal')
        for user in self:
            user.is_portal = portal_group in user.groups_id
            
    is_portal = fields.Boolean(
        string='Is Portal User',
        compute='_compute_is_portal',
        store=True
    )
    
    def action_set_parallel_vendor(self):
        """設定平行廠商"""
        self.ensure_one()
        return {
            'name': '設定平行廠商',
            'type': 'ir.actions.act_window',
            'res_model': 'parallel.vendor.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_user_id': self.id}
        }

# class ParallelVendorWizard(models.TransientModel):
#     _name = 'parallel.vendor.wizard'
#     _description = '平行廠商設定精靈'
    
#     user_id = fields.Many2one('res.users', string='使用者')
#     confirm = fields.Boolean(string='確認設為平行廠商')
    
#     def action_confirm(self):
#         if self.confirm:
#             self.user_id.write({
#                 'vendor_type': 'parallel',
#                 'is_parallel_vendor': True
#             })
#         return {'type': 'ir.actions.act_window_close'}