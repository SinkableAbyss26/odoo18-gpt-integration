# -*- coding: utf-8 -*-
from odoo import fields, models


class GPTCompletionLog(models.Model):
    """Store usage and cost details for GPT API calls."""
    _name = 'gpt.completion.log'
    _description = 'GPT Completion Log'
    _order = 'id desc'

    model_name = fields.Char(string='Model')
    prompt_tokens = fields.Integer()
    completion_tokens = fields.Integer()
    total_tokens = fields.Integer()
    cost = fields.Float(help='Approximate cost in USD')
    currency = fields.Char(default='USD')
    prompt = fields.Text()
    response = fields.Text()
    used_retry = fields.Boolean()
    used_fallback = fields.Boolean()
