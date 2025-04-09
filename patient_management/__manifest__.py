# -*- coding: utf-8 -*-
{
    'name': "Quản lý bệnh nhân",
    'summary': "Quản lý thông tin bệnh nhân",
    'description': """
    Long description of module's purpose
    """,
    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Healthcare',
    'version': '0.1',
    'license': 'LGPL-3',
    'depends': ['base', 'website'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/clinic_patient_views.xml',
        'views/patient_list_template.xml',
        'views/patient_form_template.xml',
        'views/patient_edit_templates.xml',
        'views/website_menu.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'patient_management/static/src/scss/patient_management.scss',
        ],
    },
    'installable': True,
    'application': True,
}
