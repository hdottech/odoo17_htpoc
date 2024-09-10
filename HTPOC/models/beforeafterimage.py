
from odoo import fields, models

class beforeafterimage(models.Model):
    _name = "beforeafterimage"
    _description = "Before & After Image"


    name = fields.Text(string='改善前說明', required=True)
    photo_before = fields.Binary(string='改善前照片')
    name2 = fields.Text(string='改善後說明', required=True)
    photo_after = fields.Binary(string='改善後照片')
    missing_record_id = fields.Many2one('htpoc.missingrecords', string='Missing Record')
    # b_description = fields.Text(help="請寫下改善照片說明", string="改善前照片說明")
    # a_description = fields.Text(help="請寫下改善照片說明", string="改善後照片說明")



    
    def action_save_and_close(self):
        return {'type': 'ir.actions.act_window_close'}

    def action_save_and_new(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'beforeafterimage',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
        }

