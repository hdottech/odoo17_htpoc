{
    'name': "New_res_partner",
    'version': '17.0.1.0',
    'depends': ['base','sms','contacts'],
    'category': 'App',
    'application': False,
    'installable':True,
    'license': 'LGPL-3',
    'data': [
        'views/new_res_partner_view.xml',
        'views/new_res_partner_company_view.xml',
        'views/new_res_partner_work_type_view.xml',
        'views/new_res_partner_function_view.xml',
        'security/ir.model.access.csv',
        'data/email_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'New_res_partner/static/src/css/custom_styles.css',
        ],
    },
    'installable': True,
    'application': True,
}
