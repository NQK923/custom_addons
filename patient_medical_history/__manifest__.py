{
    'name': 'Patient Medical History',
    'version': '1.0',
    'summary': 'Xem lịch sử khám bệnh của bệnh nhân',
    'depends': ['base', 'website'],
    'data': [
        'views/patient_medical_history_views.xml',
        'views/website_templates.xml',
    ],
    'installable': True,
    'application': True,
}