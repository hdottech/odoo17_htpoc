from odoo import models, fields, api

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    @api.depends('request_status')
    def _compute_can_edit_approvers(self):
        for request in self:
            request.can_edit_approvers = True  # 允許編輯審批人

    # 增加一個計算字段來控制是否可以編輯審批人
    can_edit_approvers = fields.Boolean(
        compute='_compute_can_edit_approvers',
        store=True
    )