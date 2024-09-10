from odoo import api, fields, models

class NewResPartnerCompany(models.Model):
    _name = 'new.res.partner.company'
    _description = 'New Partner Company'

    name=fields.Char(string="廠商名稱")
