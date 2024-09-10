from odoo import models, fields

class HtpocClassification(models.Model):
    _name = "classification_level"
    _description = "Classification Level"
    _order = "sequence, name"

    name = fields.Text(string="缺失等級代號", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    description = fields.Text(string="缺失等級說明")
    level = fields.Text(string="缺失等級分類說明") 