# -*- coding: utf-8 -*-
{
    'name': "custom_B_and_B",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Extension module vente pour l'impression du chiffre d'affaire par rayon sur une periode 
    """,

    'author': "Lenyx Dev",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'pos_product_section', 'sale', 'point_of_sale'],

    # always loaded
    'data': [
        'security/preva_custom_report_security.xml',
        'security/ir.model.access.csv',
        'wizard/turn_over_view.xml',
        'wizard/pos_session_wizard_view.xml',
        'views/ir_views.xml',
        'views/report_pos_order_search_view.xml',
        'views/res_config_settings_views.xml',
        'views/pos_session_back_dating_views.xml',
        'report/turn_over_report.xml',
        'report/turn_over_report_pos.xml',
        'report/turn_over_report_sale.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "installable" : True,
    "application" : False,

}
