from odoo import models, fields,api
from odoo.exceptions import UserError

class HtpocMissingRecords(models.Model):
    _name = 'htpoc.missingrecords'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Missing Records'

    brief = fields.Char(string='缺失簡述', required=True)

    contact = fields.Many2one("res.partner", string="聯絡人", copy=False)
    company = fields.Many2one("res.partner", string='公司名稱',  readonly=True)
    principal = fields.Many2one("res.partner", string="負責人")
    phone = fields.Char(string="連絡電話")
    email = fields.Char(string="電子信箱")

    floor = fields.Char(string='樓層')
    pillar = fields.Char(string='柱位')
    feeback = fields.Char(string='回報')
    cycle = fields.Char(string='週期')
    state = fields.Selection([
        ('initiate', '發起缺失紀錄'),
        ('in_process', '缺失處理中'),
        ('completed', '已完成'),
        ('cancel', "已取消")
    ], string='狀態', default='initiate')
    system_name = fields.Many2one("htpoc.missingrecords.type", string="系統")
    main_contractor = fields.Many2one('new.res.partner.company', string="主承攬商") #主承攬商
    deputy_contractor = fields.Many2one('new.res.partner.company',string="副承攬商") #副承攬商
    security_person = fields.Many2one('res.partner', string="工安人員", domain=[('category_id', '=', '工安人員')]) #工安人員
    security_person_tel = fields.Char(related='security_person.phone',string="工安人員電話") #工安人員電話
    create_date = fields.Datetime(string="第一次紀錄的時間", readonly=True)  # 第一次紀錄的時間
    write_date = fields.Datetime(string="最後更新表單的時間", readonly=True)  # 最後更新表單的時間
    record_date = fields.Datetime("記錄日期時間", default=fields.Datetime.now)  # 記錄日期時間
    message_ids = fields.One2many('mail.message', 'res_id', string='發送訊息', domain=lambda self: [('model', '=', self._name)], auto_join=True)
    activity_ids = fields.One2many('mail.activity', 'res_id', string='活動', domain=lambda self: [('res_model', '=', self._name)], auto_join=True)
    classification = fields.Many2one("htpoc.classification", string="缺失分類")
    classification_color = fields.Char(related='classification.color',string="分類顏色")

    classification_level = fields.Many2one("classification_level", string="缺失等級代號")
    classification_common = fields.Text(related='classification_level.level', string="缺失等級說明") #缺失等級說明

    penalties = fields.Text(help='Please enter manually', string="罰則") #罰則
    improve = fields.Text(help='Record of immediate improvement measures on site', string="現場立即改善措施") #現場立即改善措施
    improveDT = fields.Text(help='Immediate on-site improvement measures recording Datetime', string="改善措施及時間")  #現場立即改善措施
    sign = fields.Binary(string='缺失人員簽名') #簽名
    sign2 = fields.Binary(string='驗收人員簽名') #簽名
    empty = fields.Char(string="")
    content = fields.Text(help='詳細缺失內容記錄', string="詳細缺失內容") #詳細缺失內容
    improvement_record_ids = fields.One2many('beforeafterimage', 'missing_record_id', string="改善紀錄")
    # product_id = fields.Many2one('product.product', string='Product', required=True)
    

    ######## state 狀態變更定義  #########
    @api.onchange('record_date', 'sign', 'sign2')
    def _onchange_fields(self):
        for record in self:
            if record.create_date and not record.sign and not record.sign2:
                record.state = 'initiate'
            if record.sign and not record.sign2:
                record.state = 'in_process'
            if record.sign2:
                record.state = 'completed'

    def write(self, vals):
        if 'record_date' in vals:
            vals['create_date'] = vals.get('record_date', fields.Datetime.now())
            vals['state'] = 'initiate'
        
        if 'sign' in vals and vals['sign']:
            vals['state'] = 'in_process'
        
        if 'sign2' in vals and vals['sign2']:
            vals['state'] = 'completed'

        return super(HtpocMissingRecords, self).write(vals)
    

    # 郵件寄送方法
    @api.model
    def create(self, vals):
        if 'record_date' in vals:
            vals['create_date'] = vals.get('record_date', fields.Datetime.now())
            vals['state'] = 'initiate'
        
        record = super(HtpocMissingRecords, self).create(vals)
        record._log_state_change()
        return record

    
    # 添加創建者為關注者
    def create(self, vals):
        record = super(HtpocMissingRecords, self).create(vals)
        if self.env.user.partner_id:
            record.message_subscribe(partner_ids=[self.env.user.partner_id.id])
        return record
    
    # 在狀態變化時通知關注者
    def write(self, vals):
        res = super(HtpocMissingRecords, self).write(vals)
        if 'state' in vals:
            message = f"狀態變更為: {dict(self._fields['state'].selection).get(vals['state'])}"
            self.message_post(body=message, subtype_xmlid='mail.mt_note')
        return res
    

    # 自動將當前用戶添加為關注者
    def create(self, values):
        record = super().create(values)
        user_partner_id = self.env.user.partner_id
        if user_partner_id:
            record.message_subscribe([user_partner_id.id])
        return record
    def create(self, vals):
        record = super(HtpocMissingRecords, self).create(vals)
        if self.env.user.partner_id:
            record.message_subscribe(partner_ids=[self.env.user.partner_id.id])
        return record
    

    #狀態變更通知
    def write(self, vals):
        old_state = self.state
        res = super(HtpocMissingRecords, self).write(vals)

        # Only log if state changes
        if 'state' in vals and vals['state'] != old_state:
            self._log_state_change()

        return res

    def _log_state_change(self):
        for record in self:
            message = f"狀態變更為: {dict(self._fields['state'].selection).get(record.state)}"
            record.message_post(body=message, subtype_xmlid='mail.mt_note')

    # 自動帶出聯絡人聯絡方法
    @api.onchange('contact')
    def _onchange_contact(self):
        if self.contact:
            self.phone = self.contact.phone
            self.email = self.contact.email
            self.security_person = self.contact.industrial_safety_personnel
            if self.security_person:
                self.security_person_tel = self.security_person.mobile
    @api.depends('security_person')
    def _compute_security_person_tel(self):
        for record in self:
            if record.security_person:
                record.security_person_tel = record.security_person.mobile 

    #聯絡人變更時自動帶出相關資訊
    @api.onchange('contact')
    def _onchange_contact(self):
        if self.contact:
            # 填充對應欄位
            self.company = self.contact.parent_id  # 根據 parent_id 填充公司
            self.principal = self.contact.parent_id
            self.phone = self.contact.phone
            self.email = self.contact.email
        else:
            self.company = False
            self.principal = False
            self.phone = ''
            self.email = ''

    