from odoo import api, fields, models

class NewResPartnerWorkType(models.Model):
    _name = 'new.res.partner.work.type'
    _description = 'New Partner Work Type'

    name=fields.Char(string="工種名稱")