from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ApprovalApprover(models.Model):
    _inherit = 'approval.approver'
    _order = 'sequence, id'
    
    approval_sequence = fields.Integer(
        string='審批順序',
        default=10,
        help='決定審批順序的數字，數字越小越先審批'
    )
    user_id = fields.Many2one(
        'res.users', 
        string='User', 
        required=True,
        domain="[]"  # 移除domain限制
    )
    can_delete = fields.Boolean(
        string='Can Delete',
        compute='_compute_can_delete',
        store=True
    )

    @api.depends('status')
    def _compute_can_delete(self):
        """計算是否可以刪除"""
        for approver in self:
            approver.can_delete = approver.status not in ['approved', 'refused']

    def unlink(self):
        """刪除前檢查"""
        for approver in self:
            if approver.status in ['approved', 'refused']:
                raise ValidationError(_('不能刪除已審批的審批者：%s') % approver.user_id.name)
        return super().unlink()


class ApprovalCategoryApprover(models.Model):
    _inherit = 'approval.category.approver'
    _order = 'sequence, id'
    
    approval_sequence = fields.Integer(
        string='審批順序',
        default=10,
    )