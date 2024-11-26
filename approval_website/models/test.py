# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from ..utils.date_utils import DateUtils
import logging

_logger = logging.getLogger(__name__)


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
    can_edit_approvers = fields.Boolean(compute='_compute_can_edit_approvers', store=True)
    can_approve = fields.Boolean(string='Can Approve', compute='_compute_can_approve')

    def _get_daily_sequence(self, target_date):
        """取得當日序號"""
        # 搜尋同一天的記錄來計算序號
        domain = [
            ('create_date', '>=', f"{target_date} 00:00:00"),
            ('create_date', '<=', f"{target_date} 23:59:59")
        ]
        records = self.search(domain)
        return len(records) + 1
    
    def _reset_approver_status(self):
        """重置審批者狀態"""
        for request in self:
            for approver in request.approver_ids:
                if approver.status not in ['approved', 'refused']:
                    approver.status = 'pending' if approver.required else 'new'
    
    def create(self, vals):
        """生成序號及創建記錄"""
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

        # 創建記錄
        record = super().create(vals)

        # 如果沒有審批者且有類別，添加預設審批者
        if not record.approver_ids and record.category_id:
            approver_commands = []
            existing_user_ids = set()
            category_approvers = record.category_id.approver_ids.sorted(
                key=lambda r: r.sequence
            )
            
            for category_approver in category_approvers:
                user_id = category_approver.user_id.id
                if user_id not in existing_user_ids:
                    initial_status = 'pending' if category_approver.required else 'new'
                    approver_commands.append((0, 0, {
                        'user_id': user_id,
                        'status': initial_status,
                        'required': category_approver.required,
                        'sequence': category_approver.sequence
                    }))
                    existing_user_ids.add(user_id)
            
            if approver_commands:
                record.write({
                    'approver_ids': approver_commands
                })

        return record
    
    @api.depends('approver_ids.required', 'approver_ids.status')
    def _compute_can_approve(self):
        """計算是否可以顯示審批按鈕"""
        for request in self:
            current_user_approver = request.approver_ids.filtered(
                lambda a: a.user_id == self.env.user
            )
            can_approve = False
            if current_user_approver:
                approver = current_user_approver[0]
                can_approve = (approver.required and 
                             approver.status == 'pending' and 
                             request.request_status not in ['approved', 'refused', 'cancel'])
            request.can_approve = can_approve

    def _reset_approver_status(self):
        """重置審批者狀態"""
        for request in self:
            for approver in request.approver_ids:
                if approver.status not in ['approved', 'refused']:
                    approver.status = 'pending' if approver.required else 'new'
    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        for request in self:
            request._reset_non_required_approvers()
            status_lst = request.mapped('approver_ids.status')
            required_approvers = request.approver_ids.filtered('required')
            non_required_approvers = request.approver_ids - required_approvers
            required_statuses = required_approvers.mapped('status')
            
            if not status_lst:
                request.request_status = 'new'
            elif 'refused' in status_lst:
                request.request_status = 'refused'
            elif 'cancel' in status_lst:
                request.request_status = 'cancel'
            elif all(status == 'approved' for status in required_statuses if required_statuses):
                request.request_status = 'approved'
            else:
                request.request_status = 'pending'

        self.filtered_domain([('request_status', 'in', ['approved', 'refused', 'cancel'])])._cancel_activities()
        
    
    # 審批順序相關邏輯
    @api.depends('category_id')
    def _compute_approver_ids(self):
        for request in self:
            if not request.approver_ids and request.category_id:
                approver_commands = []
                category_approvers = request.category_id.approver_ids.sorted(
                    key=lambda r: r.sequence
                )
                
                for category_approver in category_approvers:
                    # 根據 required 決定初始狀態
                    initial_status = 'pending' if category_approver.required else 'new'
                    approver_commands.append((0, 0, {
                        'user_id': category_approver.user_id.id,
                        'status': initial_status,  # 使用根據 required 決定的狀態
                        'required': category_approver.required,
                        'sequence': category_approver.sequence
                    }))
                
                if approver_commands:
                    request.write({
                        'approver_ids': approver_commands
                    })
    def _compute_can_edit_approvers(self):
        for request in self:
            request.can_edit_approvers = True
        
    
    # onchange
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
    @api.onchange('category_id')
    def _onchange_category_id(self):
        for record in self:
            if record.category_id and record.category_id.company_id:
                record.company_id = record.category_id.company_id


    @api.depends('approver_ids.user_id', 'approver_ids.status')
    def _compute_user_status(self):
        for approval in self:
            approver = approval.approver_ids.filtered(lambda a: a.user_id == self.env.user)
            approval.user_status = approver[0].status if approver else False

    def action_approve(self):
        if not self.user_has_groups('approvals.group_approval_user'):
            raise ValidationError(_('只有審批用戶可以批准請求。'))
            
        current_user_approver = self.mapped('approver_ids').filtered(
            lambda approver: approver.user_id == self.env.user
        )
        
        if current_user_approver and current_user_approver[0].required:
            current_user_approver.write({'status': 'approved'})

    
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

    # def action_confirm(self):
    #     """ 確認請求前確保有足夠的審批人 """
    #     for record in self:
    #         if not record.approver_ids:
    #             # 如果沒有審批者，觸發計算方法從類別獲取預設審批者
    #             record._compute_approver_ids()
                
    #         # 重新讀取記錄以確保審批者已更新
    #         record = record.with_context(clean_context=True).browse(record.id)
            
    #     return super(ApprovalRequest, self).action_confirm()
    @api.model
    def create(self, vals):
        record = super(ApprovalRequest, self).create(vals)
        record._reset_non_required_approvers()
        return record


    def _reset_non_required_approvers(self):
        """
        確保沒有打勾的審批者狀態為新增
        """
        for request in self:
            # 找出所有沒打勾的審批者
            non_required_approvers = request.approver_ids.filtered(lambda r: not r.required)
            # 將它們的狀態設為 new
            if non_required_approvers:
                non_required_approvers.write({'status': 'new'})
    

    def write(self, vals):
        """
        整合的 write 方法
        """
        if 'approver_ids' in vals:
            commands = vals['approver_ids']
            approvers_to_check = self.env['approval.approver']  # 創建一個空的 recordset
            
            for command in commands:
                if command[0] == 2:  # 刪除記錄
                    approver_id = command[1]
                    approver = self.env['approval.approver'].browse(approver_id)
                    if approver.exists():
                        approvers_to_check |= approver
                elif command[0] == 3:  # 移除關聯
                    approver_id = command[1]
                    approver = self.env['approval.approver'].browse(approver_id)
                    if approver.exists():
                        approvers_to_check |= approver
                elif command[0] == 5:  # 移除所有關聯
                    approvers_to_check |= self.approver_ids
                elif command[0] == 6:  # 替換所有關聯
                    old_approvers = self.approver_ids - self.env['approval.approver'].browse(command[2])
                    approvers_to_check |= old_approvers

            # 檢查所有需要被刪除的審批者
            if approvers_to_check:
                for approver in approvers_to_check:
                    if approver.status in ['approved', 'refused']:
                        raise ValidationError(_('不能刪除已審批的審批者：%s') % approver.user_id.name)

        # 日期同步
        if vals.get('planned_date_begin'):
            vals['date_start'] = vals['planned_date_begin']
        if vals.get('planned_date_end'):
            vals['date_end'] = vals['planned_date_end']

        # 調用父類的 write 方法
        result = super().write(vals)

        # 後續處理
        if 'approver_ids' in vals:
            self._reset_approver_status()
            self._reset_non_required_approvers()

        return result

    def action_confirm(self):
        """ 確認請求前確保有足夠的審批人 """
        for record in self:
            if not record.approver_ids:
                record._compute_approver_ids()
            record = record.with_context(clean_context=True).browse(record.id)
        return super().action_confirm()

class ApprovalRequestRefuseHistory(models.Model):
    _name = 'approval.request.refuse.history'
    _description = '審批退回歷史'
    _order = 'refuse_date desc'

    request_id = fields.Many2one('approval.request', string='審批請求')
    refuse_reason = fields.Text(string='退回原因')
    refuse_date = fields.Datetime(string='退回時間')
    refuse_user_id = fields.Many2one('res.users', string='退回人')
