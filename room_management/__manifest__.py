{
    'name': 'Quản lý phòng khám',
    'version': '1.0',
    'category': 'Healthcare',
    'summary': 'Quản lý phòng khám',
    'description': """
        Module quản lý phòng khám và theo dõi bệnh nhân trong phòng
    """,
    'depends': ['base', 'patient_management', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/room_templates.xml',
        'views/website_menu.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            ('https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css', {'external': True}),
            ('https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.min.js', {'external': True}),
            '/room_management/static/src/css/room_management.css',
            '/room_management/static/src/js/room_management.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}