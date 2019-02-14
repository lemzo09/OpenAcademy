# -*- coding: utf-8 -*-
{
    'name': "Open Academy 1",

    'summary': """Manage Trainings""",
    
    'description': """
        Open Academy 1  module for managing trainings : 
            - training courses
            - training sessions
            - attendees registration
    """,

    'author': "Karizma Conseil",
    'website': "https://www.karizma-conseil.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Test',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','board'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/openacademy1.xml',
        'views/partner.xml',
        'views/session_board.xml',
        'reports.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml'
    ],
}