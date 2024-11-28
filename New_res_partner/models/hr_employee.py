from urllib.parse import urlencode
from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError
from markupsafe import Markup

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    id_number=fields.Char(string="身分證字號",required=True, copy= False, readonly=False)
    
    @api.constrains('id_number')
    def _check_id_number(self):
        # 檢查身分證字號是否唯一
        for record in self:
            if record.id_number:
                existing = self.env['res.partner'].search([
                    ('id_number', '=', record.id_number),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(_("身分證字號 %s 已存在，人員資料不允許重複建立！") % record.id_number)

    @api.model
    def create(self, vals):
        # 創建時自動同步到關聯的聯絡人
        if vals.get('id_number'):
            self._check_id_number()
        result = super(HrEmployee, self).create(vals)
        if result.work_contact_id and result.id_number:
            result.work_contact_id.write({'id_number': result.id_number})
        return result

    def write(self, vals):
        result = super(HrEmployee, self).write(vals)

        if 'id_number' in vals:
            self._check_id_number()

        if 'id_number' in vals and self.work_contact_id:
            self.work_contact_id.write({
                'id_number': vals['id_number']
            })
        return result

    

    