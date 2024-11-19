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

    # 計算欄位 - 判斷是否有選擇任何特殊作業
    # has_special_work = fields.Boolean(
    #     string='有特殊作業',
    #     compute='_compute_has_special_work',
    #     store=True
    # )

    # @api.depends('high_work', 'confined_space', 'hypoxia', 'hot_work', 
    #              'open_flame', 'electric_work', 'hanging_work', 
    #              'eExcavation_work', 'organic_solvent')
    # def _compute_has_special_work(self):
    #     """計算是否有選擇任何特殊作業"""
    #     for record in self:
    #         record.has_special_work = any([
    #             record.high_work, record.confined_space, record.hypoxia,
    #             record.hot_work, record.open_flame, record.electric_work,
    #             record.hanging_work, record.eExcavation_work, record.organic_solvent
    #         ])

    # @api.constrains('other_high_work', 'other_high_work_desc')
    # def _check_other_high_work(self):
    #     """檢查高架作業其他選項說明"""
    #     for record in self:
    #         if record.other_high_work and not record.other_high_work_desc:
    #             raise ValidationError(_('請填寫其他高架作業說明'))

    # @api.constrains('other_flame_work', 'other_flame_work_desc')
    # def _check_other_flame_work(self):
    #     """檢查明火作業其他選項說明"""
    #     for record in self:
    #         if record.other_flame_work and not record.other_flame_work_desc:
    #             raise ValidationError(_('請填寫其他明火作業說明'))

    # @api.constrains('other_heat_work', 'other_heat_work_desc')
    # def _check_other_heat_work(self):
    #     """檢查熱作業其他選項說明"""
    #     for record in self:
    #         if record.other_heat_work and not record.other_heat_work_desc:
    #             raise ValidationError(_('請填寫其他熱作業說明'))

    # @api.constrains('has_chemicals', 'sds_file')
    # def _check_sds_file(self):
    #     """檢查化學品SDS文件"""
    #     for record in self:
    #         if record.has_chemicals == '是' and not record.sds_file:
    #             raise ValidationError(_('攜帶化學品時必須上傳SDS文件'))

    # @api.constrains('high_work')
    # def _check_high_work_types(self):
    #     """檢查高架作業類型"""
    #     for record in self:
    #         if record.high_work:
    #             has_type = any([
    #                 record.aerial_platform,
    #                 record.ceiling_work,
    #                 record.scaffolding,
    #                 record.other_high_work
    #             ])
    #             if not has_type:
    #                 raise ValidationError(_('請至少選擇一種高架作業類型'))

    # @api.constrains('open_flame')
    # def _check_flame_work_types(self):
    #     """檢查明火作業類型"""
    #     for record in self:
    #         if record.open_flame:
    #             has_type = any([
    #                 record.cutting_machine,
    #                 record.acetylene,
    #                 record.grinder,
    #                 record.welding,
    #                 record.spray,
    #                 record.other_flame_work
    #             ])
    #             if not has_type:
    #                 raise ValidationError(_('請至少選擇一種明火作業類型'))

    # @api.constrains('hot_work')
    # def _check_heat_work_types(self):
    #     """檢查熱作業類型"""
    #     for record in self:
    #         if record.hot_work:
    #             has_type = any([
    #                 record.heat_gun,
    #                 record.gas_stove,
    #                 record.oven,
    #                 record.iron_plate,
    #                 record.other_heat_work
    #             ])
    #             if not has_type:
    #                 raise ValidationError(_('請至少選擇一種熱作業類型'))

    # @api.onchange('has_chemicals')
    # def _onchange_has_chemicals(self):
    #     """當改變是否攜帶化學品時清空SDS文件"""
    #     if self.has_chemicals == '否':
    #         self.sds_file = False
    #         self.sds_filename = False

    # @api.onchange('high_work')
    # def _onchange_high_work(self):
    #     """當取消高架作業時清空相關欄位"""
    #     if not self.high_work:
    #         self.aerial_platform = False
    #         self.ceiling_work = False
    #         self.scaffolding = False
    #         self.other_high_work = False
    #         self.other_high_work_desc = False

    # @api.onchange('open_flame')
    # def _onchange_open_flame(self):
    #     """當取消明火作業時清空相關欄位"""
    #     if not self.open_flame:
    #         self.cutting_machine = False
    #         self.acetylene = False
    #         self.grinder = False
    #         self.welding = False
    #         self.spray = False
    #         self.other_flame_work = False
    #         self.other_flame_work_desc = False

    # @api.onchange('hot_work')
    # def _onchange_hot_work(self):
    #     """當取消熱作業時清空相關欄位"""
    #     if not self.hot_work:
    #         self.heat_gun = False
    #         self.gas_stove = False
    #         self.oven = False
    #         self.iron_plate = False
    #         self.other_heat_work = False
    #         self.other_heat_work_desc = False