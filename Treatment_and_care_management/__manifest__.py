{
    'name': 'Quản lý điều trị',
    'version': '1.0',
    'category': 'Healthcare',
    'summary': 'Manage pharmacy inventory and stock operations',
    'description': 'A module to manage pharmacy inventory, stock in/out, and ensure sufficient medicine supply for patients.',
    'depends': ['base', "patient_management", "website"],  # Added website dependency
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',  # Keep for backward compatibility
        "views/clinic_patient_views.xml",
        'views/website_templates/treatment_plans_template.xml',
        'views/website_templates/patient_care_template.xml',
        'views/website_templates/treatment_plan_forms.xml',
        'views/website_templates/treatment_process_forms.xml',
        'views/website_templates/patient_care_forms.xml',
        'views/website_menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}