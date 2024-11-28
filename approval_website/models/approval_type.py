from odoo import models, fields, api

class ApprovalType(models.Model):
    _name = 'approval.type'
    _description = '審批主題'
    _order = 'sequence'

    name = fields.Char('主題名稱', required=True)
    sequence = fields.Integer('序號', default=10)
    active = fields.Boolean('啟用', default=True)

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    approval_type_id = fields.Many2one(
        'approval.type',
        string='審批主題',
        required=True
    )

    @api.onchange('approval_type_id')
    def _onchange_approval_type_id(self):
        if self.approval_type_id:
            self.name = self.approval_type_id.name

    @api.model
    def create(self, vals):
        if vals.get('approval_type_id'):
            approval_type = self.env['approval.type'].browse(vals['approval_type_id'])
            vals['name'] = approval_type.name
        return super().create(vals)

    def write(self, vals):
        if vals.get('approval_type_id'):
            approval_type = self.env['approval.type'].browse(vals['approval_type_id'])
            vals['name'] = approval_type.name
        return super().write(vals)