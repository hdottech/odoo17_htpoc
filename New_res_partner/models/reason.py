from odoo import models, fields, api

class NoEntryReason(models.Model):
    _name = 'no.entry.reason'
    _description = '不可入場原因記錄'

    partner_id = fields.Many2one('res.partner', string='聯絡人', required=True, ondelete='cascade')
    reason = fields.Text(string="不可入場原因紀錄")
    date = fields.Date(string="記錄日期")

class ResPartner(models.Model):
    _inherit = 'res.partner'

    no_entry_reason_ids = fields.One2many('no.entry.reason', 'partner_id', string='不可入場原因記錄')