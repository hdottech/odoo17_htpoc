from odoo import models, fields

class HtpocMissingRecordsType(models.Model):
    _name = "htpoc.missingrecords.type"
    _description = "Htpoc Missingrecords Type 系統"
    _order = "sequence, name"

    name = fields.Char(string="系統名稱", required=True)
    sequence = fields.Integer("Sequence", default=10)
    description = fields.Text(string="說明")

    # system_ids=fields.One2many("htpoc.missingrecords","system_name", string="系統")
