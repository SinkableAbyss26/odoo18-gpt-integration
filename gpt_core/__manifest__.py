# -*- coding: utf-8 -*-
{
    'name': 'GPT Core',
    'version': '18.0.1.0',
    'license': 'AGPL-3',
    'summary': 'Core utilities for GPT integration',
    'description': 'Configuration and service layer for OpenAI GPT models.',
    'author': 'Odoo GPT Integration',
    'maintainer': 'Odoo GPT Integration',
    'website': 'https://example.com',
    'depends': ['base', 'base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'data/chatgpt_model_data.xml',
        'views/res_config_settings_views.xml',
    ],
    'external_dependencies': {'python': ['openai>=1.30.0']},
    'installable': True,
    'application': False,
    'auto_install': False,
}
