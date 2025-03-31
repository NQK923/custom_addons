{
    'name': 'Quản lý dược phẩm',
    'version': '1.0',
    'category': 'Healthcare',
    'summary': 'Manage pharmacy inventory and stock operations',
    'description': 'A module to manage pharmacy inventory, stock in/out, and ensure sufficient medicine supply for patients.',
    'depends': ['base', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/prescription_templates.xml',
        'views/website_menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}