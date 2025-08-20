# -*- coding: utf-8 -*-
# Copyright (c) 2019-Present InTechual Solutions. (<https://intechualsolutions.com/>)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def _get_default_chatgpt_model(self):
        model_id = False
        try:
            self.env.ref('is_chatgpt_integration.chatgpt_model_gpt_3_5_turbo').id
        except:
            model_id = False
        return model_id

    openapi_api_key = fields.Char(string="API Key", help="Provide the API key here", config_parameter="is_chatgpt_integration.openapi_api_key")
    chatgpt_model_id = fields.Many2one('chatgpt.model', 'ChatGPT Model', ondelete='cascade', default=_get_default_chatgpt_model,  config_parameter="is_chatgpt_integration.chatgp_model")
