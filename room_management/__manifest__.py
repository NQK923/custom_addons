{
    'name': "Quản lý Phòng khám và Giường bệnh",
    'summary': "Quản lý phòng khám và giường bệnh trên giao diện web",
    'description': "Module cho phép quản lý phòng khám và giường bệnh trên giao diện web.",
    'author': "Your Name",
    'version': '1.0',
    'depends': ['base', 'website', 'patient_management'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        # 'views/views.xml',
        'views/room_templates.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}
