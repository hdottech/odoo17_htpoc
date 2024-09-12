{
    'name': '漢唐集成缺失記錄',
    'version': '1.0',
    'category': 'APP',
    'license': 'LGPL-3',
    'summary': 'HTPOC 漢唐集成缺失記錄',
    'description': 'Module for managing missing records',
    'depends': ['base','web','mail','New_res_partner','sms'],
    'data': [
        'security/ir.model.access.csv',
        'views/htpoc_classification_views.xml',
        'views/htpoc_missingrecords.xml',
        'views/htpoc_missingrecords_type.xml',
        'views/classification_level.xml',
        'views/beforeafterimage.xml',
        'views/users.xml',
        #'data/res_users_data.xml',
        'data/email_template.xml',
            

        # 'views/users.xml',
        'views/htpoc_menu.xml',

    ],
    'icon': '/HTPOC/static/description/icon.png',
    'installable': True,
    'application': True,
}
