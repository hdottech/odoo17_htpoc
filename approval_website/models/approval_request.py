# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from ..utils.date_utils import DateUtils
from lxml import etree

class ApprovalRequest(models.Model):
    _inherit ='approval.request'

    # 新增序號欄位
    sequence_number = fields.Char('序號', readonly=True, copy=False)
    planned_date_begin = fields.Datetime(string='計劃開始日期')
    planned_date_end = fields.Datetime(string='計劃結束日期')  
    display_date_begin = fields.Char(
        string='開始日期',
        compute='_compute_display_dates'
    )
    display_date_end = fields.Char(   
        string='結束日期',
        compute='_compute_display_dates'
    )
    main_contractor_id = fields.Many2one('new.res.partner.company', string='主承商', required=True, tracking=True)
    sub_contractor_id = fields.Many2one('new.res.partner.company', string='次承商', required=True, tracking=True)
    document_ids = fields.Many2many('documents.document', string='相關文件')
    refuse_reason = fields.Text(string='退回原因')
    refuse_history_ids = fields.One2many('approval.request.refuse.history', 'request_id', string='退回紀錄')
    def _get_daily_sequence(self, target_date):
        """取得當日序號"""
        # 搜尋同一天的記錄來計算序號
        domain = [
            ('create_date', '>=', f"{target_date} 00:00:00"),
            ('create_date', '<=', f"{target_date} 23:59:59")
        ]
        records = self.search(domain)
        return len(records) + 1
    
    def create(self, vals):
    # 生成序號(年月日-流水號)
        
        if not vals.get('sequence_number'):
            today = date.today()
            prefix = today.strftime('%Y%m%d-')

            domain = [
                ('sequence_number', 'like', prefix),
                ('create_date', '>=', today.strftime('%Y-%m-%d 00:00:00')),
                ('create_date', '<=', today.strftime('%Y-%m-%d 23:59:59'))
            ]
        
            last_seq = self.search(domain, order='sequence_number desc', limit=1)
        
            if last_seq:
                last_number = int(last_seq.sequence_number.split('-')[-1])
                sequence = str(last_number + 1).zfill(3)
            else:
                sequence = '001'
           
                
            vals['sequence_number'] = prefix + sequence

        # 同步日期資料
        if vals.get('planned_date_begin'):
            vals['date_start'] = vals['planned_date_begin']
        if vals.get('planned_date_end'):
            vals['date_end'] = vals['planned_date_end']

        return super().create(vals)
    
    # 在寫入時同步日期
    def write(self, vals):
        if vals.get('planned_date_begin'):
            vals['date_start'] = vals['planned_date_begin']
        if vals.get('planned_date_end'):
            vals['date_end'] = vals['planned_date_end']
        return super().write(vals)
    
 
    # 計算並更新期間欄位的值
    @api.onchange('planned_date_begin', 'planned_date_end')
    def _onchange_planned_dates(self):
        for record in self:
            if record.planned_date_begin:
                record.date_start = record.planned_date_begin
            if record.planned_date_end:
                record.date_end = record.planned_date_end

    # 反向同步：當期間欄位改變時，更新計劃日期
    @api.onchange('date_start', 'date_end')
    def _onchange_period_dates(self):
        for record in self:
            if record.date_start and not record.planned_date_begin:
                record.planned_date_begin = record.date_start
            if record.date_end and not record.planned_date_end:
                record.planned_date_end = record.date_end 


    @api.depends('approver_ids.user_id', 'approver_ids.status')
    def _compute_user_status(self):
        for approval in self:
            approver = approval.approver_ids.filtered(lambda a: a.user_id == self.env.user)
            approval.user_status = approver[0].status if approver else False

    @api.depends('approver_ids.user_id', 'approver_ids.status')
    def _compute_request_status(self):
        for approval in self:
            status_lst = approval.mapped('approver_ids.status')
            minimal_approver = approval.approval_minimum if len(approval.approver_ids) >= approval.approval_minimum else len(approval.approver_ids)
            if status_lst:
                if status_lst.count('approved') >= minimal_approver:
                    approval.request_status = 'approved'
                elif status_lst.count('refused'):
                    approval.request_status = 'refused'
                elif status_lst.count('cancel'):
                    approval.request_status = 'cancel'
                else:
                    approval.request_status = 'pending'
            else:
                approval.request_status = 'new'

    @api.onchange('category_id')
    def _onchange_category_id(self):
        for record in self:
            if record.category_id and record.category_id.company_id:
                record.company_id = record.category_id.company_id

    @api.onchange('company_id')
    def _onchange_company_id(self):
        domain = []
        if self.company_id:
            domain = [('company_id', '=', self.company_id.id)]
        return {'domain': {'category_id': domain}}

    def action_approve(self):
        """ 批准請求 """
        if not self.user_has_groups('approvals.group_approval_user'):
            raise ValidationError(_('只有審批用戶可以批准請求。'))
        approver = self.mapped('approver_ids').filtered(lambda approver: approver.user_id == self.env.user)
        approver.write({'status': 'approved'})

    def action_refuse(self):
        """ 開啟退回原因視窗 """
        self.ensure_one()
        if not self.user_has_groups('approvals.group_approval_user'):
            raise ValidationError(_('只有審批用戶可以拒絕請求。'))
            
        return {
            'name': _('退回原因'),
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request.refuse.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_request_id': self.id,
            }
        }
    

    def _compute_can_access(self):
        for record in self:
            record.can_access = (
                record.request_owner_id == self.env.user or
                self.env.user in record.approver_ids.mapped('user_id') or
                self.env.user.has_group('approvals.group_approval_manager')
            )

    can_access = fields.Boolean(compute='_compute_can_access')
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ApprovalRequest, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if self.env.user.has_group('your_module.group_approval_manager'):
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//button[@name='action_approve']"):
                node.set('modifiers', '{"invisible": true}')
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

class ApprovalRequestRefuseHistory(models.Model):
    _name = 'approval.request.refuse.history'
    _description = '審批退回歷史'
    _order = 'refuse_date desc'

    request_id = fields.Many2one('approval.request', string='審批請求')
    refuse_reason = fields.Text(string='退回原因')
    refuse_date = fields.Datetime(string='退回時間')
    refuse_user_id = fields.Many2one('res.users', string='退回人')
