from odoo import api, fields, models, _

class TaskReturnWizard(models.TransientModel):
    _name = 'task.return.wizard'
    _description = '任務退回精靈'

    task_id = fields.Many2one('project.task', string='任務', required=True)
    current_stage_id = fields.Many2one('project.task.type', string='當前階段')
    reject_reason = fields.Text(string='退回原因', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_model') == 'project.task':
            task = self.env['project.task'].browse(self.env.context.get('active_id'))
            res.update({
                'task_id': task.id,
                'current_stage_id': task.stage_id.id,
            })
        return res

    def action_return(self):
        self.ensure_one()
        if not self.task_id:
            return False
            
        # 獲取或創建已退件狀態
        return_stage = self.env['project.task.type'].search(
            [('name', '=', '已退件')], limit=1)
        if not return_stage:
            return_stage = self.env['project.task.type'].create({
                'name': '已退件',
                'sequence': 99,
                'fold': False,
            })

        # 將任務移動到已退件狀態
        self.task_id.write({
            'stage_id': return_stage.id,
            'reject_reason': self.reject_reason,
            'last_stage_id': self.current_stage_id.id
        })

        # 創建備註記錄退回原因
        self.task_id.message_post(
            body=_(
                # '任務已從 <b>%s</b> 退回<br/>'
                '任務已從 %s 退回，'
                '退回原因：%s'
            ) % (
                self.current_stage_id.name,
                self.reject_reason
            )
        )

        return {'type': 'ir.actions.act_window_close'}