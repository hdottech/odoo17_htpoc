from odoo import models, fields, api

class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    invalid_minimum = fields.Boolean(
        string='Invalid Minimum',
        store=True,
        readonly=False,
        default=False
    )

    invalid_minimum_warning = fields.Char(
        string='Invalid Minimum Warning',
        compute='_compute_invalid_minimum_warning',
        store=True
    )

    @api.depends('invalid_minimum', 'approval_minimum')
    def _compute_invalid_minimum_warning(self):
        for record in self:
            record.invalid_minimum_warning = False
            if record.invalid_minimum and record.approval_minimum > 0:
                record.invalid_minimum_warning = '警告：已允許超過最小審批人數'