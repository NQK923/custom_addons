{
    'name': 'Quản lý điều trị',
    'version': '1.0',
    'category': 'Healthcare',
    'summary': 'Manage pharmacy inventory and stock operations',
    'description': 'A module to manage pharmacy inventory, stock in/out, and ensure sufficient medicine supply for patients.',
    'depends': ['base', "patient_management", "website", 'staff_management', 'prescription_management'],
    # Added website dependency
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/treatment_plans_template.xml',
        'views/patient_care_template.xml',
        'views/treatment_plan_forms.xml',
        'views/treatment_process_forms.xml',
        'views/patient_care_forms.xml',
        'views/website_menu.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/Treatment_and_care_management/static/src/css/treatment_styles.scss',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
