from odoo import models, fields, api

class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    company_id = fields.Many2one('res.company', string='案場', required=True, default=lambda self: self.env.company)
    
    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)', 
         '同一個案場內的審批類型名稱不能重複!')
    ]

    @api.model
    def _create_general_work_approval_type(self):
        """創建一般作業申請表單審批類型"""
        category = self.env['approval.category'].sudo().search([
            ('name', '=', '一般作業申請表單')
        ], limit=1)
        
        if not category:
            category = self.env['approval.category'].sudo().create({
                'name': '一般作業申請表單',
                'description': '用於處理一般作業申請的審批流程',
                'approval_type': 'required',  # 必需審批
                'approval_minimum': 3,  # 需要3個審批人
                'has_date_range': True,  # 包含日期範圍
                'sequence': 10,
                'active': True,
                'manager_approval': True,
                'automated_sequence': True,  # 自動編號
                'sequence_code': 'GW',  # General Work
                'sequence_prefix': 'GW/%(range_year)s/',
            })
            
            # 創建審批用戶組
            self.env['res.groups'].sudo().create({
                'name': '一般作業申請審批群組',
                'category_id': self.env.ref('base.module_category_operations').id,
                'comment': '可以審批一般作業申請的用戶群組'
            })

        return category
    
    @api.model
    def _create_safety_check_approval_type(self):
        """創建安全設施拆除作業申請表單審批類型"""
        category = self.env['approval.category'].sudo().search([
            ('name', '=', '安全設施拆除作業申請表單')
        ], limit=1)
        
        if not category:
            category = self.env['approval.category'].sudo().create({
                'name': '安全設施拆除作業申請表單',
                'description': '用於處理安全設施拆除作業的審批流程',
                'approval_type': 'required',
                'approval_minimum': 3,
                'has_date_range': True,
                'sequence': 20,
                'active': True,
                'manager_approval': True,
                'automated_sequence': True,
                'sequence_code': 'SF',  # Safety Facility
                'sequence_prefix': 'SF/%(range_year)s/',
            })

        return category
    
    @api.model
    def _create_equipment_material_approval_type(self):
        """創建機具物料進場申請表單審批類型"""
        category = self.env['approval.category'].sudo().search([
            ('name', '=', '機具物料進場申請表單')
        ], limit=1)
        
        if not category:
            category = self.env['approval.category'].sudo().create({
                'name': '機具物料進場申請表單',
                'description': '用於處理機具物料進場申請的審批流程',
                'approval_type': 'required',
                'approval_minimum': 3,
                'has_date_range': True,
                'sequence': 30,
                'active': True,
                'manager_approval': True,
                'automated_sequence': True,
                'sequence_code': 'EM',  # Equipment Material
                'sequence_prefix': 'EM/%(range_year)s/',
            })

        return category

    def _get_user_approvers(self):
        """獲取審批流程中的用戶"""
        return [
            ('承商工安', 1),
            ('主承商工程師', 2),
            ('UIS EHS', 3)
        ]