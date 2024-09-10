from odoo import api, fields, models

class NewResPartnerFunction(models.Model):
    _name = 'new.res.partner.function'
    _description = 'New Partner Function'

    name=fields.Char(string="職位名稱")
