# -*- coding: utf-8 -*-
{
    'name': "approval_website",  
    
    'summary': "網站表單串接審批功能",
    
    'description': """
        嘗試使用網站表單串接審批功能，
    """,
    
    'author': "My Company",
    'website': "https://www.eliam102.com",
    
    'category': 'Uncategorized',
    'version': '0.1',
    
    'depends': [
        'base',
        'mail',
        'website',
        'website_sale', 
        'project',
        'web',
        'portal',
        'approvals',
    ],
    
    'data': [
        'security/ir.model.access.csv',
        'security/securityrules.xml',
        'data/sequence.xml',
        'views/refuse_reason_views.xml',
        'templates/website_menu.xml',
        'templates/form_selection_template.xml',
        'templates/approval_website_template.xml', 
        'templates/approval_type_list_template.xml',
        'templates/approval_request_detail_template.xml',
        'templates/safety_form_template.xml',
        'templates/vendor_form_template123.xml',
        'templates/equipment_material.xml',
        'templates/special_work_permit_form.xml',
        'templates/vendor_form_success.xml',
        'templates/error.xml',
        'views/approval_request.xml',
        'views/approval_type.xml',
        # 'views/res_users_views.xml',

        # 'views/res_users_views.xml',

    ],

    'application': True,
    'installable': True,
}