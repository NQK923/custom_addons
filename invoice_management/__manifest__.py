{
    'name': 'Quản lý hóa đơn',
    'version': '1.0',
    'summary': 'Module quản lý hóa đơn phòng khám',
    'sequence': 10,
    'description': """Module quản lý hóa đơn phòng khám""",
    'category': 'Healthcare',
    'author': 'Your Name',
    'website': '',
    'depends': ['base','prescription_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}