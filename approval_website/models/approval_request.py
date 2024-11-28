from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from ..utils.date_utils import DateUtils
from lxml import etree

class ApprovalRequest(models.Model):
    _inherit ='approval.request'

    # Fields
    sequence_number = fields.Char('序號', readonly=True, copy=False)
    planned_date_begin = fields.Datetime(string='計劃開始日期')
    planned_date_end = fields.Datetime(string='計劃結束日期')
    display_date_begin = fields.Char(string='開始日期', compute='_compute_display_dates')
    display_date_end = fields.Char(string='結束日期', compute='_compute_display_dates')
    main_contractor_id = fields.Many2one('new.res.partner.company', string='主承商', required=True, tracking=True)
    sub_contractor_id = fields.Many2one('new.res.partner.company', string='次承商', required=True, tracking=True)
    document_ids = fields.Many2many('documents.document', string='相關文件')
    refuse_reason = fields.Text(string='退回原因')
    refuse_history_ids = fields.One2many('approval.request.refuse.history', 'request_id', string='退回紀錄')
    can_edit_approvers = fields.Boolean(compute='_compute_can_edit_approvers', store=True)
    can_approve = fields.Boolean(string='Can Approve', compute='_compute_can_approve')
    can_access = fields.Boolean(compute='_compute_can_access')



    # Computes
    @api.depends('approver_ids.required', 'approver_ids.status')
    def _compute_can_approve(self):
        """計算當前用戶是否可以審批"""
        for request in self:
            current_user_approver = request.approver_ids.filtered(
                lambda a: a.user_id == self.env.user
            )
            can_approve = False
            if current_user_approver:
                approver = current_user_approver[0]
                can_approve = (
                    approver.required and 
                    approver.status == 'pending' and 
                    request.request_status not in ['approved', 'refused', 'cancel'])
            request.can_approve = can_approve

    def _compute_can_edit_approvers(self):
        """計算是否可以編輯審批者"""
        for request in self:
            request.can_edit_approvers = True

    def _compute_can_access(self):
        """計算是否有權限訪問"""
        for record in self:
            record.can_access = (
                record.request_owner_id == self.env.user or
                self.env.user in record.approver_ids.mapped('user_id') or
                self.env.user.has_group('approvals.group_approval_manager')
            )

    @api.depends('approver_ids.user_id', 'approver_ids.status')
    def _compute_user_status(self):
        """計算用戶審批狀態"""
        for approval in self:
            approver = approval.approver_ids.filtered(lambda a: a.user_id == self.env.user)
            approval.user_status = approver[0].status if approver else False


    #  CRUD    
    @api.model
    def create(self, vals):
        """創建記錄時生成序號"""
        if not vals.get('sequence_number'):
            today = date.today()
            prefix = today.strftime('%Y%m%d-')
            domain = [
                ('sequence_number', 'like', prefix),
                ('create_date', '>=', today.strftime('%Y-%m-%d 00:00:00')),
                ('create_date', '<=', today.strftime('%Y-%m-%d 23:59:59'))
            ]
            last_seq = self.search(domain, order='sequence_number desc', limit=1)
            sequence = str(int(last_seq.sequence_number.split('-')[-1]) + 1).zfill(3) if last_seq else '001'
            vals['sequence_number'] = prefix + sequence

        # 同步日期
        if vals.get('planned_date_begin'):
            vals['date_start'] = vals['planned_date_begin']
        if vals.get('planned_date_end'):
            vals['date_end'] = vals['planned_date_end']

        return super().create(vals)

    def write(self, vals):
        """寫入時的驗證和處理"""
        # 審批者驗證
        if 'approver_ids' in vals:
            self._validate_approver_changes(vals['approver_ids'])

        # 日期同步
        if vals.get('planned_date_begin'):
            vals['date_start'] = vals['planned_date_begin']
        if vals.get('planned_date_end'):
            vals['date_end'] = vals['planned_date_end']

        result = super().write(vals)

        # 更新審批者狀態
        if 'approver_ids' in vals:
            self._reset_approver_status()
            self._reset_non_required_approvers()

        return result
    
    # Business Methods
    def _validate_approver_changes(self, commands):
        """驗證審批者變更"""
        approvers_to_check = self.env['approval.approver']
        
        for command in commands:
            if command[0] in [2, 3]:  # 刪除或移除關聯
                approver = self.env['approval.approver'].browse(command[1])
                if approver.exists():
                    if approver.status in ['approved', 'refused']:
                        raise ValidationError(_('不能刪除已審批的審批者：%s') % approver.user_id.name)

    def _reset_approver_status(self):
        """重置審批者狀態"""
        for request in self:
            for approver in request.approver_ids:
                if approver.status not in ['approved', 'refused']:
                    approver.status = 'pending' if approver.required else 'new'

    def _reset_non_required_approvers(self):
        """重置非必填審批者狀態"""
        for request in self:
            non_required_approvers = request.approver_ids.filtered(lambda r: not r.required)
            if non_required_approvers:
                non_required_approvers.write({'status': 'new'})

    # Action
    def action_approve(self):
        """審批通過"""
        if not self.user_has_groups('approvals.group_approval_user'):
            raise ValidationError(_('只有審批用戶可以批准請求。'))
    
        current_user_approver = self.mapped('approver_ids').filtered(
            lambda approver: approver.user_id == self.env.user
        )
        
        if current_user_approver:
            current_user_approver.write({'status': 'approved'})

    def action_refuse(self):
        """拒絕審批"""
        self.ensure_one()
        if not self.user_has_groups('approvals.group_approval_user'):
            raise ValidationError(_('只有審批用戶可以拒絕請求。'))
        return {
            'name': _('退回原因'),
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request.refuse.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id}
        }
    
    # Onchange
    @api.onchange('planned_date_begin', 'planned_date_end')
    def _onchange_planned_dates(self):
        """計劃日期變更時同步更新"""
        for record in self:
            if record.planned_date_begin:
                record.date_start = record.planned_date_begin
            if record.planned_date_end:
                record.date_end = record.planned_date_end

    @api.onchange('date_start', 'date_end')
    def _onchange_period_dates(self):
        """期間日期變更時同步更新"""
        for record in self:
            if record.date_start and not record.planned_date_begin:
                record.planned_date_begin = record.date_start
            if record.date_end and not record.planned_date_end:
                record.planned_date_end = record.date_end

    @api.onchange('category_id')
    def _onchange_category_id(self):
        """類別變更時更新公司"""
        for record in self:
            if record.category_id and record.category_id.company_id:
                record.company_id = record.category_id.company_id

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """公司變更時更新領域"""
        domain = []
        if self.company_id:
            domain = [('company_id', '=', self.company_id.id)]
        return {'domain': {'category_id': domain}}

class ApprovalRequestRefuseHistory(models.Model):
    _name = 'approval.request.refuse.history'
    _description = '審批退回歷史'
    _order = 'refuse_date desc'

    request_id = fields.Many2one('approval.request', string='審批請求')
    refuse_reason = fields.Text(string='退回原因')
    refuse_date = fields.Datetime(string='退回時間')
    refuse_user_id = fields.Many2one('res.users', string='退回人')