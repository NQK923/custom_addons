# -*- coding: utf-8 -*-
{
     'name': "Medical Test Management",

    'summary': "Quản lý xét nghiệm và chẩn đoán y tế",

    'description': """
Module quản lý xét nghiệm và chẩn đoán y tế với giao diện website
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    'category': 'Healthcare',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'website', 'web', 'staff_management', 'patient_management'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/website_templates.xml',
        'views/website_templates_create.xml',
        'views/website_templates_image.xml',
        'views/website_menus.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'medical_management/static/src/css/medical_styles.css',
            'medical_management/static/src/js/medical_scripts.js',
        ],
    },
    'installable': True,
    'application': True,
}