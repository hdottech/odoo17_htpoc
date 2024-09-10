from odoo import models, fields

class HtpocClassification(models.Model):
    _name = "htpoc.classification"
    _description = "Htpoc Classification"
    _order = "sequence, name"

    name = fields.Char(string="缺失等級分類", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    description = fields.Text(string="缺失等級分類")
    color = fields.Char(string="缺失分類顏色")  # Char field for storing emoji color