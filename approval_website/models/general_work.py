from odoo import models, fields, api

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    # 添加新欄位
    main_contractor = fields.Many2one('new.res.partner.company', string='主承攬商')
    sub_contractor = fields.Many2one('new.res.partner.company', string='次承攬商')
    work_location = fields.Char(string='施工區位置')
    worker_count = fields.Integer(string='施工人數')
    supervisor_name = fields.Char(string='監工人員')
    supervisor_phone = fields.Char(string='監工電話')
    safety_staff_name = fields.Char(string='工安人員')
    safety_staff_phone = fields.Char(string='工安電話')