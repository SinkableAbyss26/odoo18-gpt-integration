# -*- coding: utf-8 -*-
# Copyright (c) 2019-Present InTechual Solutions. (<https://intechualsolutions.com/>)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def _get_default_chatgpt_model(self):
        model_id = False
        try:
            model_id = self.env.ref('gpt_core.chatgpt_model_gpt_5_nano').id
        except Exception:
            model_id = False
        return model_id

    openapi_api_key = fields.Char(
        string="API Key",
        help="Provide the OpenAI API key",
        config_parameter="gpt_core.openapi_api_key",
    )
    chatgpt_model_id = fields.Many2one(
        'chatgpt.model',
        'ChatGPT Model',
        ondelete='cascade',
        default=_get_default_chatgpt_model,
        config_parameter="gpt_core.chatgpt_model",
    )
    temperature = fields.Float(
        string="Temperature",
        help="Sampling temperature to use.",
        config_parameter="gpt_core.temperature",
        default=0.0,
    )
    max_tokens = fields.Integer(
        string="Max Tokens",
        help="Maximum number of output tokens to generate (maps to max_output_tokens)",
        config_parameter="gpt_core.max_tokens",
        default=512,
    )
