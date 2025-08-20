# -*- coding: utf-8 -*-
import logging
from openai import OpenAI
from odoo import api, models


_logger = logging.getLogger(__name__)


PRICING = {
    'gpt-4o': {'prompt': 0.000005, 'completion': 0.000015},
    'gpt-4o-mini': {'prompt': 0.00000015, 'completion': 0.00000060},
    'gpt-5-mini': {'prompt': 0.00000050, 'completion': 0.00000150},
    'gpt-5-nano': {'prompt': 0.00000010, 'completion': 0.00000040},
}


class GPTService(models.AbstractModel):
    _name = 'gpt.service'
    _description = 'OpenAI GPT Service'

    @api.model
    def _get_client(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param('gpt_core.openapi_api_key')
        if not api_key:
            raise ValueError('Missing OpenAI API key')
        return OpenAI(api_key=api_key)

    @api.model
    def _default_params(self):
        ICP = self.env['ir.config_parameter'].sudo()
        model_param = ICP.get_param('gpt_core.chatgpt_model')
        model_name = 'gpt-5-nano'
        if model_param:
            if model_param.isdigit():
                model_rec = self.env['chatgpt.model'].sudo().browse(int(model_param))
                model_name = model_rec.name or model_name
            else:
                model_name = model_param
        temperature = float(ICP.get_param('gpt_core.temperature') or 0.0)
        max_tokens = int(ICP.get_param('gpt_core.max_tokens') or 512)
        return model_name, temperature, max_tokens

    @api.model
    def chat_completion(self, messages, **kwargs):
        client = self._get_client()
        model_name, temperature, max_tokens = self._default_params()
        temperature = kwargs.get('temperature', temperature)
        max_tokens = kwargs.get('max_tokens', max_tokens)
        model_name = kwargs.get('model', model_name)

        def _normalize(msgs):
            normalized = []
            for m in msgs:
                content = m.get('content', '')
                parts = content if isinstance(content, list) else [{
                    'type': 'input_text',
                    'text': content,
                }]
                normalized.append({'role': m.get('role'), 'content': parts})
            return normalized

        params = {
            'model': model_name,
            'messages': _normalize(messages),
            'max_output_tokens': max_tokens,
        }
        if not model_name.startswith('gpt-5') and temperature is not None:
            params['temperature'] = temperature

        try:
            response = client.responses.create(**params)
        except Exception as e:  # adapt unsupported params silently
            msg = str(e).lower()
            adapted = False
            if 'max_tokens' in msg:
                params['max_output_tokens'] = params.pop('max_tokens', max_tokens)
                adapted = True
            if 'temperature' in msg and 'temperature' in params:
                params.pop('temperature', None)
                adapted = True
            if adapted:
                _logger.info('Adjusted unsupported parameter: %s', e)
                response = client.responses.create(**params)
            else:
                raise

        texts = []
        for output in getattr(response, 'output', []) or []:
            content = getattr(output, 'content', None)
            if content is None and hasattr(output, 'get'):
                content = output.get('content', [])
            for part in content or []:
                texts.append(getattr(part, 'text', '') or part.get('text', ''))
        text = ''.join(texts)
        if not text.strip():
            raise ValueError('Empty response from model')

        usage_raw = getattr(response, 'usage', {}) or {}
        usage = {
            'prompt_tokens': usage_raw.get('input_tokens', 0),
            'completion_tokens': usage_raw.get('output_tokens', 0),
            'total_tokens': usage_raw.get('total_tokens', usage_raw.get('input_tokens', 0) + usage_raw.get('output_tokens', 0)),
        }
        self._log_usage(model_name, usage, messages, text)
        return text

    @api.model
    def _log_usage(self, model_name, usage, messages, response):
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)
        pricing = PRICING.get(model_name, {})
        cost = (
            prompt_tokens * pricing.get('prompt', 0) +
            completion_tokens * pricing.get('completion', 0)
        )
        self.env['gpt.completion.log'].sudo().create({
            'model_name': model_name,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': total_tokens,
            'cost': cost,
            'prompt': '\n'.join(m.get('content', '') for m in messages),
            'response': response,
        })
