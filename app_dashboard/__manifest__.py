{
    'name': 'My Custom Module',
    'version': '1.0',
    'summary': 'Module with a button to open another module',
    'author': 'Your Name',
    'category': 'Custom',
    'depends': ['base','Treatment_and_care_management'],  # module_to_link là module mà bạn muốn gọi tới
    'data': [
        'views/my_custom_view.xml',
        'views/menu_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
}
