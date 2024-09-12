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
        ('valid', '有效'),
        ('expired', '已逾期'),
    ], string="體檢狀態", compute='_compute_date_status')
    six_hour_class_status = fields.Selection([
        ('valid', '有效'),
        ('expired', '已逾期'),
    ], string="六小時上課狀態", compute='_compute_date_status')
    hazard_notification_class_status = fields.Selection([
        ('valid', '證件有效'),
        ('expired', '無效證件'),
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


    #檢查身分證字號是否是唯一的
    @api.constrains('id_number')
    def _check_id_number(self):
        for record in self:
            if record.id_number:
                existing = self.env['res.partner'].search([
                    ('id_number', '=', record.id_number),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(_("身分證字號 %s 已存在，人員資料不允許重複建立！") % record.id_number)
                
    def write(self, vals):
        if 'id_number' in vals:
            for record in self:
                if record.id_number != vals['id_number']:
                    existing = self.env['res.partner'].search([
                        ('id_number', '=', vals['id_number']),
                        ('id', '!=', record.id)
                    ])
                    if existing:
                        raise ValidationError(_("身分證字號 %s 已存在，人員資料不允許重複更新！") % vals['id_number'])
        return super(NewResPartner, self).write(vals)

    #計算工安行動電話
    @api.onchange('industrial_safety_personnel')
    def _onchange_industrial_safety_personnel(self):
        self._compute_industrial_safety_mobile()

    @api.depends('industrial_safety_personnel')
    def _compute_industrial_safety_mobile(self):
        if self.industrial_safety_personnel:
            self.industrial_safety_mobile = self.industrial_safety_personnel.mobile
        else:
            self.industrial_safety_mobile = False

    #在人名前面加上公司名稱
    @api.depends('name', 'parent_id.name')
    def _compute_display_name(self):
        for partner in self:
            if partner.parent_id and partner.parent_id.is_company:
                partner.display_name = f"{partner.parent_id.name}, {partner.name}"
            else:
                partner.display_name = partner.name

    # 計算年齡
    @api.depends('birthday')
    def _compute_age(self):
        for record in self:
            if record.birthday:
                today = fields.Date.today()
                born = fields.Date.from_string(record.birthday)
                # 計算年齡
                record.age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            else:
                record.age = 0  # 如果沒有生日，則設定年齡為0

    # 計算下一次體檢日期
    @api.depends('age', 'physical_examination_date')
    def _compute_next_examination_date(self):
        for record in self:
            if record.physical_examination_date and record.age:
                if record.age < 45:
                    years_to_add = 5
                elif 45 <= record.age < 65:
                    years_to_add = 3
                else:
                    years_to_add = 1
                
                record.next_physical_examination_date = record.physical_examination_date + relativedelta(years=years_to_add)
            else:
                record.next_physical_examination_date = False

    @api.depends('Six_hour_class_date', 'hazard_notification_class_date')
    def _compute_class_expiration(self):
        today = fields.Date.today()
        for record in self:
            # 計算六小時上課日期到期時間
            if record.Six_hour_class_date:
                expiry_date = record.Six_hour_class_date + relativedelta(years=3)
                record.six_hour_class_expiry_date = expiry_date
                record.six_hour_class_expired = today >= (expiry_date - relativedelta(months=1))
            else:
                record.six_hour_class_expired = False
                record.six_hour_class_expiry_date = False

            # 計算危害告知上課日期到期時間
            if record.hazard_notification_class_date:
                expiry_date = record.hazard_notification_class_date + relativedelta(years=3)
                record.hazard_notification_class_expiry_date = expiry_date
                record.hazard_notification_class_expired = today >= (expiry_date - relativedelta(months=1))
            else:
                record.hazard_notification_class_expired = False
                record.hazard_notification_class_expiry_date = False

    @api.depends('next_physical_examination_date', 'six_hour_class_expiry_date', 'hazard_notification_class_expiry_date')
    def _compute_admission(self):
        today = fields.Date.today()
        for record in self:
            if (record.next_physical_examination_date and record.next_physical_examination_date >= today) and \
               (record.six_hour_class_expiry_date and record.six_hour_class_expiry_date >= today) and \
               (record.hazard_notification_class_expiry_date and record.hazard_notification_class_expiry_date >= today):
                record.admission = 'yes'
            else:
                record.admission = 'no'

    # 檢查課程到期狀態
    @api.depends('next_physical_examination_date', 'six_hour_class_expiry_date', 'hazard_notification_class_expiry_date')
    def _compute_date_status(self):
        today = fields.Date.today()
        for record in self:
            record.next_physical_examination_status = 'valid' if record.next_physical_examination_date and record.next_physical_examination_date >= today else 'expired'
            record.six_hour_class_status = 'valid' if record.six_hour_class_expiry_date and record.six_hour_class_expiry_date >= today else 'expired'
            record.hazard_notification_class_status = 'valid' if record.hazard_notification_class_expiry_date and record.hazard_notification_class_expiry_date >= today else 'expired'

    # 自動發送信件
    def action_send_email(self):
        template = self.env.ref("New_res_partner.email_template")  # 取得郵件模板
        company_email = self.env.res.company.email

        for partner in self:
            email_values = {
                "email_to": partner.email,
                "email_cc": company_email,
                "auto_delete": True,
                "recipient_ids": [],
                "partner_ids": [],
                "scheduled_date": False,
                "email_from": company_email,
            }
            template.send_mail(partner.id, email_values=email_values, force_send=True)

    @api.model
    def _cron_check_expirations(self):
        today = fields.Date.today()
        one_month_later = today + relativedelta(months=1)

        partners_to_notify = self.search([
            '|', '|',
            ('next_physical_examination_date', '<=', one_month_later),
            ('six_hour_class_expiry_date', '<=', one_month_later),
            ('hazard_notification_class_expiry_date', '<=', one_month_later)
        ])

        for partner in partners_to_notify:
            expiring_items = []
            if partner.next_physical_examination_date and partner.next_physical_examination_date <= one_month_later:
                expiring_items.append('體檢')
            if partner.six_hour_class_expiry_date and partner.six_hour_class_expiry_date <= one_month_later:
                expiring_items.append('六小時上課')
            if partner.hazard_notification_class_expiry_date and partner.hazard_notification_class_expiry_date <= one_month_later:
                expiring_items.append('危害告知上課')

            if expiring_items:
                partner.action_send_email()

    # 在您的模型中添加這個方法
    def init(self):
        # 創建一個每週運行的 cron 作業
        self.env['ir.cron'].sudo().create({
            'name': 'Check Partner Expirations',
            'model_id': self.env['ir.model'].search([('model', '=', 'res.partner')]).id,
            'state': 'code',
            'code': 'model._cron_check_expirations()',
            'interval_number': 1,
            'interval_type': 'weeks',
            'numbercall': -1,
            'doall': False,
            'active': True,
        })
