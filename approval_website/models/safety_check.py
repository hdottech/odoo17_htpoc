# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from ..utils.date_utils import DateUtils

class SafetyCheck(models.Model):
    _inherit = 'approval.request'

    # 安全設施拆除相關欄位
    email = fields.Char(string='申請人信箱')
    removal_items = fields.Text(string='拆除項目')
    location = fields.Char(string='樓別/樓層/住位')
    removal_reason = fields.Text(string='拆除原因')
    alternative_measures = fields.Text(string='替代防護措施')
    document_ids = fields.Many2many('documents.document', string='相關文件')
    task_id = fields.Many2one('project.task', string='相關任務')

    # 使用 DateUtils 來處理日期顯示
    implementation_date = fields.Datetime(string='施工日期')
    display_implementation_date = fields.Char(
        string='顯示施工日期',
        compute='_compute_display_implementation_date'
    )
    date_start = fields.Datetime(string='開始時間')
    date_end = fields.Datetime(string='結束時間')
    construction_date = fields.Date(string='施工日期', compute='_compute_construction_date', store=True)

    @api.depends('implementation_date')
    def _compute_display_implementation_date(self):
        for record in self:
            record.display_implementation_date = DateUtils.format_datetime(record.implementation_date)

    @api.depends('date_start')
    def _compute_construction_date(self):
        """根據開始時間計算施工日期"""
        for record in self:
            if record.date_start:
                record.construction_date = record.date_start.date()
            else:
                record.construction_date = False

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        """檢查日期有效性"""
        for record in self:
            if record.date_start and record.date_end:
                if record.date_start > record.date_end:
                    raise ValidationError(_('開始時間不能晚於結束時間'))

    # @api.model
    # def create(self, vals):
    #     # 建立審批請求
    #     res = super().create(vals)
        
    #     # 如果是安全設施拆除申請，建立對應任務
    #     if res.category_id.name == '安全設施施工拆除作業申請表單':
    #         # 準備任務資料
    #         description = {
    #             'name': f"{res.name}",
    #             'date_deadline': res.implementation_date,
    #             'description': f"""
    #                 <h3>安全設施拆除作業施工申請表單詳情：</h3>
    #                 <p><strong>施工日期：</strong>{res.display_implementation_date}</p>
    #                 <p><strong>拆除項目：</strong>{res.removal_items}</p>
    #                 <p><strong>申請人電子郵件：</strong>{res.email}</p>
    #                 <p><strong>主承攬商：</strong>{res.main_contractor_id.name}</p>
    #                 <p><strong>次承攬商：</strong>{res.sub_contractor_id.name}</p>
    #                 <p><strong>樓別/樓層/住位：</strong>{res.location}</p>
    #                 <p><strong>拆除原因：</strong>{res.removal_reason}</p>
    #                 <p><strong>替代防護措施：</strong>{res.alternative_measures}</p>
    #             """,
    #             'user_id': self.env.user.id,
    #         }
            
    #         # # 建立任務
    #         # task = self.env['project.task'].sudo().create(task_vals)
    #         # res.write({'task_id': task.id})

    #         # # 如果有文件，關聯到任務
    #         # if res.document_ids:
    #         #     res.document_ids.write({
    #         #         'res_model': 'project.task',
    #         #         'res_id': task.id
    #         #     })
    #         #     task.write({'document_ids': [(6, 0, res.document_ids.ids)]})
            
    #         res.write({'reason': description})

    #     return res