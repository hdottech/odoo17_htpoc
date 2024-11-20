from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import time,datetime
import pytz

class EquipmentMaterialEntry(models.Model):
    _inherit = 'approval.request'
    
    # 基本申請資訊
    email = fields.Char(string='電子郵件', required=True, tracking=True)
    entry_date = fields.Date(string='進場日期', tracking=True)
    entry_method = fields.Char(string='進場方式', tracking=True)
    contact_person = fields.Char(string='攜貨人/聯絡人姓名', required=True, tracking=True)
    contact_phone = fields.Char(string='攜貨人/聯絡人電話', required=True, tracking=True)
    item_details = fields.Text(string='物品/數量/單一物品重量', required=True, tracking=True)
    
    # 關聯欄位
    main_contractor_id = fields.Many2one('new.res.partner.company', string='主承攬商', tracking=True)
    sub_contractor_id = fields.Many2one('new.res.partner.company', string='次承攬商', tracking=True)
    
    # 進場方式相關資訊
    truck_details = fields.Char(string='貨車車號', tracking=True)
    forklift_operator_qualified = fields.Selection([
        ('yes', '有'),
        ('no', '無')
    ], string='堆高機工區合格標籤', tracking=True)
    crane_model = fields.Char(string='吊掛型號', tracking=True)
    crane_tonnage = fields.Float(string='吊掛噸數', tracking=True)
    other_model_1 = fields.Char(string='其他型號-1', tracking=True)
    other_model_2 = fields.Char(string='其他型號-2', tracking=True)

    @api.model
    def _get_default_datetime_range(self, date):
        """設定默認的時間範圍 (早上8點到下午6點) 並轉換為 UTC"""
        if not date:
            return False, False
        
        local_tz = pytz.timezone('Asia/Taipei')

        # 開始時間
        start_naive = datetime.combine(date, time(hour=8, minute=0))
        start_localized = local_tz.localize(start_naive)  # 加入時區資訊
        start_utc = start_localized.astimezone(pytz.UTC).replace(tzinfo=None)  # 轉換為 UTC 並移除時區

        # 結束時間
        end_naive = datetime.combine(date, time(hour=18, minute=0))
        end_localized = local_tz.localize(end_naive)  # 加入時區資訊
        end_utc = end_localized.astimezone(pytz.UTC).replace(tzinfo=None)  # 轉換為 UTC 並移除時區

        return start_utc, end_utc

    @api.model
    def create(self, vals):
        """創建記錄時的處理邏輯"""
        # 設置正確的審批類別
        if not vals.get('category_id'):
            category = self.env['approval.category'].sudo().search([
                ('name', '=', '機具物料進場申請表單')
            ], limit=1)
            if category:
                vals['category_id'] = category.id

        # 處理進場日期和時間範圍
        if vals.get('entry_date'):
            entry_date = fields.Date.from_string(vals['entry_date'])
            start_time, end_time = self._get_default_datetime_range(entry_date)
            vals.update({
                'date_start': start_time,
                'date_end': end_time,
                'planned_date_begin': start_time,
                'planned_date_end': end_time,
            })

        return super(EquipmentMaterialEntry, self).create(vals)

    @api.onchange('entry_date')
    def _onchange_entry_date(self):
        """當進場日期改變時，更新相關時間欄位"""
        if self.entry_date:
            self.date_start, self.date_end = self._get_default_datetime_range(self.entry_date)
            self.planned_date_begin = self.date_start
            self.planned_date_end = self.date_end