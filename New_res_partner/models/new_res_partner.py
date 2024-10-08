from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import logging
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
class NewResPartner(models.Model):
    _inherit = 'res.partner'
    

    #新增字段
    # new_function=fields.Char(string="工作職位")
    new_function=fields.Many2one('new.res.partner.function', string="工作職位")
    address = fields.Char(string="緊急聯絡人地址")
    gender = fields.Selection([
        ('male', '男'),
        ('female', '女'),
        ], string='性別')
    id_number=fields.Char(string="身分證字號",required=True, copy= False )
    #_sql_constraints = [
    #    ('unique_id_number', 'UNIQUE(id_number)', '身分證字號必須是唯一的！請確認此人是否已經存在於名單內！'),
    #]
    blood_type=fields.Selection([    
        ('A', 'A型'),
        ('B', 'B型'),
        ('O', 'O型'),
        ('AB', 'AB型'),
        ], string='血型')
    birthday=fields.Date(string="生日")
    age = fields.Integer(string="年齡", compute='_compute_age', store=True)
    emergency_contact=fields.Char(string="緊急聯絡人")
    emergency_relationship=fields.Char(string="緊急聯絡人關係")
    emergency_number=fields.Char(string="緊急聯絡人電話")
    admission=fields.Selection([
        ('no', '不可入場'),
        ('yes', '可入場')
        ], string='可否入場', compute='_compute_admission', store=True, default='no')
    main_contractor=fields.Many2one('new.res.partner.company', string="主承攬商")
    sub_contractor=fields.Many2one('new.res.partner.company', string="次承攬商")
    under_contractor=fields.Many2one('new.res.partner.company', string="下包商")
    work_type=fields.Many2one('new.res.partner.work.type', string="工種")
    industrial_safety_personnel=fields.Many2one('res.partner', string="工安人員", domain=[('category_id', '=', '工安人員')])
    industrial_safety_mobile=fields.Char(string="工安行動電話", readonly=True, compute='_compute_industrial_safety_mobile')
    
    physical_examination_date=fields.Date(string="體檢日期")
    next_physical_examination_date = fields.Date(string="下一次體檢日期", compute='_compute_next_examination_date', store=True)
    Six_hour_class_date = fields.Date(string="六小時上課日期")
    six_hour_class_expired = fields.Boolean(string="六小時上課到期", compute='_compute_class_expiration', store=True)
    six_hour_class_expiry_date = fields.Date(string="六小時上課到期日", compute='_compute_class_expiration', store=True)
    hazard_notification_class_date = fields.Date(string="危害告知上課日期")
    hazard_notification_class_expired = fields.Boolean(string="危害告知上課到期", compute='_compute_class_expiration', store=True)
    hazard_notification_class_expiry_date = fields.Date(string="危害告知上課到期日", compute='_compute_class_expiration', store=True)
    next_physical_examination_status = fields.Selection([
        ('valid', '證件有效'),
        ('warning', '即將到期'),
        ('expired', '已逾期'),
    ], string="體檢狀態", compute='_compute_date_status')
    six_hour_class_status = fields.Selection([
        ('valid', '證件有效'),
        ('warning', '即將到期'),
        ('expired', '已逾期'),
    ], string="六小時上課狀態", compute='_compute_date_status')
    hazard_notification_class_status = fields.Selection([
        ('valid', '證件有效'),
        ('warning', '即將到期'),
        ('expired', '已逾期'),
    ], string="危害告知上課狀態", compute='_compute_date_status')

    id_photo_front=fields.Binary(string="1.1. 身分證正面")
    id_photo_back=fields.Binary(string="1.2. 身分證背面")
    mug_shot=fields.Binary(string="2. 大頭照")
    life_mug_shot_01=fields.Binary(string="2.1. 生活大頭照01[辨識使用]")
    life_mug_shot_02=fields.Binary(string="2.2. 生活大頭照02[辨識使用]")
    life_mug_shot_03=fields.Binary(string="2.3. 生活大頭照03[辨識使用]")
    life_mug_shot_04=fields.Binary(string="2.4. 生活大頭照04[辨識使用]")
    construction_six_hour=fields.Binary(string="3. 營造六小時")
    physical_examination_form=fields.Binary(string="4. 體檢表")
    labor_insurance=fields.Binary(string="5. 勞保")
    hazzard_notification=fields.Binary(string="6. 危害告知")
    personal_date_consent_form=fields.Binary(string="7. 個人資料同意書")
    security_cutoff_letter=fields.Binary(string="8. 資安通訊保密切結書")
    foreigner_entry_certificate=fields.Binary(string="10. 外籍人士入台證明影本")
    health_commitment=fields.Binary(string="9. 健康承諾書")

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

    def write(self, vals):
        # 更新時檢查身分證字號
        if 'id_number' in vals:
            self._check_id_number()
        return super(NewResPartner, self).write(vals)

    @api.depends('industrial_safety_personnel')
    def _compute_industrial_safety_mobile(self):
        # 計算工安行動電話
        for record in self:
            record.industrial_safety_mobile = record.industrial_safety_personnel.mobile if record.industrial_safety_personnel else False

    @api.depends('name', 'parent_id.name')
    def _compute_display_name(self):
        # 計算顯示名稱，加上公司名稱
        for partner in self:
            partner.display_name = f"{partner.parent_id.name}, {partner.name}" if partner.parent_id and partner.parent_id.is_company else partner.name

    @api.depends('birthday')
    def _compute_age(self):
        # 計算年齡
        today = fields.Date.today()
        for record in self:
            if record.birthday:
                born = fields.Date.from_string(record.birthday)
                record.age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            else:
                record.age = 0

    @api.depends('age', 'physical_examination_date')
    def _compute_next_examination_date(self):
        # 計算下一次體檢日期
        for record in self:
            if record.physical_examination_date and record.age:
                years_to_add = 5 if record.age < 45 else 3 if 45 <= record.age < 65 else 1
                record.next_physical_examination_date = record.physical_examination_date + relativedelta(years=years_to_add)
            else:
                record.next_physical_examination_date = False

    @api.depends('Six_hour_class_date', 'hazard_notification_class_date')
    def _compute_class_expiration(self):
        # 計算課程到期日期和狀態
        today = fields.Date.today()
        for record in self:
            for class_date, expiry_date, expired in [
                ('Six_hour_class_date', 'six_hour_class_expiry_date', 'six_hour_class_expired'),
                ('hazard_notification_class_date', 'hazard_notification_class_expiry_date', 'hazard_notification_class_expired')
            ]:
                if record[class_date]:
                    expiry = record[class_date] + relativedelta(years=3)
                    record[expiry_date] = expiry
                    record[expired] = today >= (expiry - relativedelta(months=1))
                else:
                    record[expiry_date] = record[expired] = False

    @api.depends('next_physical_examination_date', 'six_hour_class_expiry_date', 'hazard_notification_class_expiry_date')
    def _compute_date_status(self):
        # 計算各項狀態
        today = fields.Date.today()
        one_month_later = today + relativedelta(months=1)
        for record in self:
            for date_field, status_field in [
                ('next_physical_examination_date', 'next_physical_examination_status'),
                ('six_hour_class_expiry_date', 'six_hour_class_status'),
                ('hazard_notification_class_expiry_date', 'hazard_notification_class_status')
            ]:
                if record[date_field]:
                    record[status_field] = 'expired' if record[date_field] < today else 'warning' if record[date_field] <= one_month_later else 'valid'
                else:
                    record[status_field] = 'expired'

    @api.depends('next_physical_examination_date', 'six_hour_class_expiry_date', 'hazard_notification_class_expiry_date')
    def _compute_admission(self):
        # 計算是否可入場
        today = fields.Date.today()
        for record in self:
            record.admission = 'yes' if all(record[f] and record[f] >= today for f in [
                'next_physical_examination_date', 'six_hour_class_expiry_date', 'hazard_notification_class_expiry_date'
            ]) else 'no'

    def action_send_email(self):
        # 發送提醒郵件
        template = self.env.ref("New_res_partner.email_template_expiration_notification", raise_if_not_found=False)
        company_email = self.env.company.email

        for partner in self.filtered(lambda p: not p.is_company):  # 只處理個人聯絡人
            expiring_items = [item for item, status in [
                ('體檢', partner.next_physical_examination_status),
                ('六小時上課', partner.six_hour_class_status),
                ('危害告知上課', partner.hazard_notification_class_status)
            ] if status in ['warning', 'expired']]

            if expiring_items and partner.email:
                template.with_context(expiring_items=", ".join(expiring_items)).send_mail(
                    partner.id,
                    email_values={
                        "email_to": partner.email,
                        "email_cc": False,
                        "auto_delete": True,
                        "email_from": company_email,
                    },
                    force_send=True,
                    raise_exception=True
                )
        self.env.cr.commit()
        self.env.invalidate_all()

    @api.model
    def _cron_check_expirations(self):
        # 定時檢查並發送郵件
        self.search([
            '|', '|',
            ('next_physical_examination_status', 'in', ['warning', 'expired']),
            ('six_hour_class_status', 'in', ['warning', 'expired']),
            ('hazard_notification_class_status', 'in', ['warning', 'expired'])
        ]).action_send_email()

    @api.model
    def init(self):
        # 初始化 cron 作業
        cron_data = {
            'name': '檢查夥伴到期日並發送郵件',
            'model_id': self.env['ir.model'].search([('model', '=', 'res.partner')]).id,
            'state': 'code',
            'code': 'model._cron_check_expirations()',
            'interval_number': 1,
            'interval_type': 'weeks',
            'numbercall': -1,
            'doall': False,
            'active': True,
        }
        if not self.env['ir.cron'].sudo().search([('name', '=', cron_data['name'])]):
            self.env['ir.cron'].sudo().create(cron_data)

    
