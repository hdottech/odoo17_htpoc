from odoo import models, fields, api
from odoo.exceptions import UserError

class HtpocMissingRecords(models.Model):
    _name = 'htpoc.missingrecords'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # 使模型能夠追蹤訊息和活動
    _description = 'Missing Records'


    # 欄位定義
    brief = fields.Char(string='缺失簡述', required=True)  # 缺失簡述
    contact = fields.Many2one("res.partner", string="聯絡人", copy=False)  # 聯絡人
    company = fields.Many2one("res.partner", string='公司名稱', readonly=True)  # 公司名稱（唯讀）
    principal = fields.Many2one("res.partner", string="負責人")  # 負責人
    phone = fields.Char(string="連絡電話")  # 連絡電話
    email = fields.Char(string="電子信箱")  # 電子信箱

    floor = fields.Char(string='樓層')  # 樓層
    pillar = fields.Char(string='柱位')  # 柱位
    feeback = fields.Char(string='回報')  # 回報
    cycle = fields.Char(string='週期')  # 週期

    # 狀態定義
    state = fields.Selection([
        ('initiate', '發起缺失紀錄'),
        ('in_process', '缺失處理中'),
        ('completed', '已完成'),
        ('cancel', "已取消")
    ], string='狀態', default='initiate')  # 狀態初始值為'發起缺失紀錄'

    # 其他欄位
    system_name = fields.Many2one("htpoc.missingrecords.type", string="系統")  # 系統名稱
    main_contractor = fields.Many2one('new.res.partner.company', string="主承攬商")  # 主承攬商
    deputy_contractor = fields.Many2one('new.res.partner.company', string="副承攬商")  # 副承攬商
    security_person = fields.Many2one('res.partner', string="工安人員", domain=[('category_id', '=', '工安人員')])  # 工安人員
    security_person_tel = fields.Char(related='security_person.mobile', string="工安人員電話")  # 工安人員電話（關聯）
    
    # 日期欄位
    create_date = fields.Datetime(string="第一次紀錄的時間", readonly=True)  # 創建日期
    write_date = fields.Datetime(string="最後更新表單的時間", readonly=True)  # 最後更新日期
    record_date = fields.Datetime("記錄日期時間", default=fields.Datetime.now)  # 記錄日期時間
    
    # 郵件訊息欄位
    message_ids = fields.One2many('mail.message', 'res_id', string='發送訊息', domain=lambda self: [('model', '=', self._name)], auto_join=True)
    activity_ids = fields.One2many('mail.activity', 'res_id', string='活動', domain=lambda self: [('res_model', '=', self._name)], auto_join=True)
    
    # 缺失分類
    classification = fields.Many2one("htpoc.classification", string="缺失分類")  # 缺失分類
    classification_color = fields.Char(related='classification.color', string="分類顏色")  # 顏色

    classification_level = fields.Many2one("classification_level", string="缺失等級代號")  # 等級代號
    classification_common = fields.Text(related='classification_level.level', string="缺失等級說明")  # 說明

    # 其他
    penalties = fields.Text(help='Please enter manually', string="罰則")  # 罰則
    improve = fields.Text(help='Record of immediate improvement measures on site', string="現場立即改善措施")  # 現場立即改善措施
    improveDT = fields.Text(help='Immediate on-site improvement measures recording Datetime', string="改善措施及時間")  # 改善措施及時間
    sign = fields.Binary(string='缺失人員簽名')  # 缺失人員簽名
    sign2 = fields.Binary(string='驗收人員簽名')  # 驗收人員簽名
    content = fields.Text(help='詳細缺失內容記錄', string="詳細缺失內容")  # 詳細缺失內容
    improvement_record_ids = fields.One2many('beforeafterimage', 'missing_record_id', string="改善紀錄")  # 改善紀錄

    ######## 狀態變更定義 ########
    @api.onchange('record_date', 'sign', 'sign2')
    def _onchange_fields(self):
        """
        根據記錄日期和簽名狀態來改變表單的狀態
        """
        for record in self:
            if record.create_date and not record.sign and not record.sign2:
                record.state = 'initiate'
            elif record.sign and not record.sign2:
                record.state = 'in_process'
            elif record.sign2:
                record.state = 'completed'

    def write(self, vals):
        """
        根據更新的值變更狀態：
        - 如果有記錄日期，狀態變為發起。
        - 如果有簽名，狀態變為處理中。
        - 如果有驗收人員簽名，狀態變為已完成。
        """
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
        """
        創建記錄時：
        - 設定創建日期為當前記錄日期
        - 狀態設為 '發起缺失紀錄'
        """
        if 'record_date' in vals:
            vals['create_date'] = vals.get('record_date', fields.Datetime.now())
            vals['state'] = 'initiate'

        record = super(HtpocMissingRecords, self).create(vals)
        record._log_state_change()  # 記錄狀態變更訊息
        return record

    # 自動將創建者添加為關注者
    def create(self, vals):
        """
        創建記錄後自動將當前用戶設為關注者
        """
        record = super(HtpocMissingRecords, self).create(vals)
        if self.env.user.partner_id:
            record.message_subscribe(partner_ids=[self.env.user.partner_id.id])
        return record

    # 狀態變化時通知關注者
    def write(self, vals):
        """
        狀態變更時發送郵件通知關注者
        """
        res = super(HtpocMissingRecords, self).write(vals)
        if 'state' in vals:
            message = f"狀態變更為: {dict(self._fields['state'].selection).get(vals['state'])}"
            self.message_post(body=message, subtype_xmlid='mail.mt_note')
        return res

    def _log_state_change(self):
        """
        用來記錄狀態變更的訊息
        """
        for record in self:
            message = f"狀態變更為: {dict(self._fields['state'].selection).get(record.state)}"
            record.message_post(body=message, subtype_xmlid='mail.mt_note')

    # 自動帶出聯絡人相關資訊
    @api.onchange('contact')
    def _onchange_contact(self):
        """
        當聯絡人變更時，根據聯絡人自動填充公司、負責人、電話和電子信箱等欄位
        """
        if self.contact:
            self.company = self.contact.parent_id  # 根據 parent_id 填充公司
            self.principal = self.contact.parent_id  # 填充負責人
            self.phone = self.contact.mobile  # 填充電話
            self.email = self.contact.email  # 填充電子信箱
        else:
            self.company = False
            self.principal = False
            self.phone = ''
            self.email = ''
    @api.model
    def create(self, vals):
        """在創建記錄時處理公司欄位"""
        if 'contact' in vals and vals['contact']:
            contact = self.env['res.partner'].browse(vals['contact'])
            vals['company'] = contact.parent_id.id if contact.parent_id else False
        return super(HtpocMissingRecords, self).create(vals)

    def write(self, vals):
        """在更新記錄時處理公司欄位"""
        if 'contact' in vals and vals['contact']:
            contact = self.env['res.partner'].browse(vals['contact'])
            vals['company'] = contact.parent_id.id if contact.parent_id else False
        return super(HtpocMissingRecords, self).write(vals)

    @api.depends('security_person')
    def _compute_security_person_tel(self):
        """
        自動帶出工安人員的電話號碼
        """
        for record in self:
            if record.security_person:
                record.security_person_tel = record.security_person.mobile  # 取得工安人員手機號碼
