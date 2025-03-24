{
    'name': 'Quản lý điều trị',
    'version': '1.0',
    'category': 'Healthcare',
    'summary': 'Manage pharmacy inventory and stock operations',
    'description': 'A module to manage pharmacy inventory, stock in/out, and ensure sufficient medicine supply for patients.',
    'depends': ['base', "patient_management"],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',  # Chỉ load file này
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',

}