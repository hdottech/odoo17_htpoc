from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SpecialWorkPermit(models.Model):
    _inherit = 'approval.request'
    # _description = '特殊作業許可單'

    # 基本欄位
    email = fields.Char(string='電子郵件', tracking=True)
    document_ids = fields.Many2many('documents.document', string='相關文件')
    main_contractor_id = fields.Many2one('new.res.partner.company', string='主承商', tracking=True)
    sub_contractor_id = fields.Many2one('new.res.partner.company', string='次承商', tracking=True)
    approval_type_id = fields.Many2one('approval.type', string='案場', tracking=True)
    
    # 申請資訊
    apply_date = fields.Date(string='申請日期', tracking=True)
    work_area = fields.Char(string='施工區域', tracking=True)
    entry_work_time = fields.Selection([
        ('常日 08:00~18:00', '常日 08:00~18:00'),
        ('夜間 18:00~07:00', '夜間 18:00~07:00')
    ], string='作業時段', tracking=True)
    
    # 化學品相關
    has_chemicals = fields.Selection([
        ('是', '是'),
        ('否', '否')
    ], string='是否攜帶化學品', tracking=True)
    sds_file = fields.Binary(string='SDS文件')
    sds_filename = fields.Char(string='SDS文件名稱')

    # 特殊作業許可欄位
    # 基本作業類型
    high_work = fields.Boolean('高架作業', tracking=True)
    confined_space = fields.Boolean('局限作業', tracking=True)
    hypoxia = fields.Boolean('缺氧作業', tracking=True)
    hot_work = fields.Boolean('熱作業', tracking=True)
    open_flame = fields.Boolean('明火作業', tracking=True)
    electric_work = fields.Boolean('電力作業', tracking=True)
    hanging_work = fields.Boolean('吊掛作業', tracking=True)
    eExcavation_work = fields.Boolean('開挖作業', tracking=True)
    organic_solvent = fields.Boolean('有機溶劑', tracking=True)
    
    # 高架作業種類
    aerial_platform = fields.Boolean('高空工作車', tracking=True)
    ceiling_work = fields.Boolean('天花板', tracking=True)
    scaffolding = fields.Boolean('施工架', tracking=True)
    ladder = fields.Boolean('梯具(合梯、爬梯、平台梯等)', tracking=True)
    other_high_work = fields.Boolean('其他高架作業說明', tracking=True)
    other_high_work_desc = fields.Text('其他高架作業說明',tracking=True)

    # 明火作業種類
    cutting_machine = fields.Boolean('切割機', tracking=True)
    acetylene = fields.Boolean('乙炔', tracking=True)
    grinder = fields.Boolean('砂輪機', tracking=True)
    welding = fields.Boolean('電焊機', tracking=True)
    spray = fields.Boolean('噴燈', tracking=True)
    # other_flame_work = fields.Boolean('其他(需填寫說明)', tracking=True)
    other_flame_work = fields.Text('其他明火作業說明', tracking=True)

    # 熱作業種類
    heat_gun = fields.Boolean('熱風槍', tracking=True)
    gas_stove = fields.Boolean('氬焊', tracking=True)
    oven = fields.Boolean('熔接', tracking=True)
    iron_plate = fields.Boolean('鐵板燒', tracking=True)
    drying_box = fields.Boolean('烘管箱', tracking=True)
    other_heat_work = fields.Text('其他熱作業說明', tracking=True)

    # 施工人員資訊
    safety_supervisor = fields.Char('廠商工安', tracking=True)
    safety_supervisor_phone = fields.Char('廠商工安電話', tracking=True)
    work_supervisor = fields.Char('廠商監工', tracking=True)
    work_supervisor_phone = fields.Char('廠商監工電話', tracking=True)

