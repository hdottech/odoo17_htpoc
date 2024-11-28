from odoo import models, fields, api

class RefuseReasonWizard(models.TransientModel):
    _name = 'approval.request.refuse.wizard'
    _description = '退回原因'

    refuse_reason = fields.Text(string='退回原因', required=True)
    request_id = fields.Many2one('approval.request', string='審批請求')

    def action_refuse(self):
        self.ensure_one()
        if self.request_id:
            # 更新審批請求狀態和原因
            self.request_id.write({
                'request_status': 'refused',
                'refuse_reason': self.refuse_reason
            })

            # 更新審批人狀態
            approver = self.request_id.approver_ids.filtered(
                lambda a: a.user_id.id == self.env.user.id
            )
            if approver:
                approver.write({'status': 'refused'})

            # 創建退回歷史記錄
            self.env['approval.request.refuse.history'].create({
                'request_id': self.request_id.id,
                'refuse_reason': self.refuse_reason,
                'refuse_date': fields.Datetime.now(),
                'refuse_user_id': self.env.user.id,
            })

            # 添加系統訊息
            self.request_id.message_post(
                body=f'申請已被退回。退回原因：{self.refuse_reason}',
                message_type='notification',
                subtype_id=self.env.ref('mail.mt_note').id
            )

        return {'type': 'ir.actions.act_window_close'}