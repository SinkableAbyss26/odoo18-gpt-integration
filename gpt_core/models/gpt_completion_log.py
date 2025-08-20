# -*- coding: utf-8 -*-
from odoo import fields, models


class GPTCompletionLog(models.Model):
    """Store usage and cost details for GPT API calls."""
    _name = 'gpt.completion.log'
    _description = 'GPT Completion Log'
    _order = 'id desc'

    model = fields.Char(string='Model')
    status = fields.Char()
    incomplete_details_reason = fields.Char()
    input_tokens = fields.Integer()
    output_tokens = fields.Integer()
    reasoning_tokens = fields.Integer()
    total_tokens = fields.Integer()
    max_output_tokens = fields.Integer()
    temperature = fields.Float()
    cost = fields.Float(help='Approximate cost in USD')
    currency = fields.Char(default='USD')
    prompt = fields.Text()
    response = fields.Text()
    used_retry = fields.Boolean()
