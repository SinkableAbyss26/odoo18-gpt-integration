# -*- coding: utf-8 -*-
# Copyright (c) 2019-Present InTechual Solutions. (<https://intechualsolutions.com/>)

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def _get_default_chatgpt_model(self):
        model_id = False
        try:
            model_id = self.env.ref('gpt_core.chatgpt_model_gpt_5_mini').id
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
        help="Sampling temperature (GPT-4*)",
        config_parameter="gpt_core.temperature",
        default=0.75,
    )
    reasoning_effort = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        string="Reasoning Effort",
        help="Allocate tokens to reasoning (GPT-5*)",
        default='medium',
        config_parameter="gpt_core.reasoning_effort",
    )
    max_tokens = fields.Integer(
        string="Max Tokens",
        help="Maximum output tokens (Responses: max_output_tokens / Chat: max_tokens)",
        config_parameter="gpt_core.max_tokens",
        default=1600,
    )
    is_gpt5 = fields.Boolean(
        compute="_compute_is_gpt5", store=False
    )

    @api.onchange('chatgpt_model_id')
    def _onchange_chatgpt_model_id(self):
        name = self.chatgpt_model_id.name if self.chatgpt_model_id else ''
        self.is_gpt5 = name.startswith('gpt-5')

    @api.depends('chatgpt_model_id')
    def _compute_is_gpt5(self):
        for rec in self:
            name = rec.chatgpt_model_id.name if rec.chatgpt_model_id else ''
            rec.is_gpt5 = name.startswith('gpt-5')
