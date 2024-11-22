# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ApprovalRights(models.Model):
    _inherit = 'approval.request'  # 繼承審批請求模型
    
    # 添加判斷用戶是否為主管的方法
    def _is_manager(self):
        manager_group = self.env.ref('base.group_manager')  # 請根據實際的主管群組ID調整
        return True if manager_group in self.env.user.groups_id else False
    
    # 覆寫原有的按鈕可見性方法
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ApprovalRights, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if self.env.user.has_group('your_module.group_approval_manager'):
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//button[@name='action_approve']"):
                node.set('modifiers', '{"invisible": true}')
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

