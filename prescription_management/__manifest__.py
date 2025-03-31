{
    'name': 'Quản lý dược phẩm',
    'version': '1.0',
    'category': 'Healthcare',
    'summary': 'Manage pharmacy inventory and stock operations',
    'description': 'A module to manage pharmacy inventory, stock in/out, and ensure sufficient medicine supply for patients.',
    'depends': ['base', 'website'],  # Added website dependency
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/prescription_templates.xml',
        'views/prescription_edit_templates.xml',
        'views/pharmacy_product_templates.xml',
        'views/pharmacy_product_form_template.xml',
        'views/pharmacy_dashboard_template.xml',
        'views/clinic_service_templates.xml',
        'views/clinic_service_form_template.xml',
        'views/website_menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}