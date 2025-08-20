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
        ICP = self.env['ir.config_parameter'].sudo()
        api_key = ICP.get_param('gpt_core.openapi_api_key')
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
                model_rec = (
                    self.env['chatgpt.model'].sudo().browse(int(model_param))
                )
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

        def _stringify(content):
            if isinstance(content, list):
                texts = []
                for part in content:
                    if isinstance(part, dict) or hasattr(part, 'get'):
                        texts.append(
                            getattr(part, 'text', '') or part.get('text', '')
                        )
                    else:
                        texts.append(
                            getattr(part, 'text', '') or str(part)
                        )
                return ''.join(texts)
            return content or ''

        prompt = '\n'.join(_stringify(m.get('content', '')) for m in messages)

        def _request(m_name, tokens):
            params = {
                'model': m_name,
                'input': prompt,
                'max_output_tokens': tokens,
            }
            if not m_name.startswith('gpt-5') and temperature is not None:
                params['temperature'] = temperature
            try:
                resp = client.responses.create(**params)
            except Exception as e:  # adapt unsupported params silently
                msg = str(e).lower()
                adapted = False
                if 'max_tokens' in msg:
                    params['max_output_tokens'] = params.pop(
                        'max_tokens', tokens
                    )
                    adapted = True
                if 'temperature' in msg and 'temperature' in params:
                    params.pop('temperature', None)
                    adapted = True
                if adapted:
                    _logger.info('Adjusted unsupported parameter: %s', e)
                    resp = client.responses.create(**params)
                else:
                    raise
            return resp

        def _extract_text(resp):
            text = getattr(resp, 'output_text', '') or ''
            if not text.strip():
                texts = []
                for output in getattr(resp, 'output', []) or []:
                    content = getattr(output, 'content', None)
                    if content is None and hasattr(output, 'get'):
                        content = output.get('content', [])
                    for part in content or []:
                        texts.append(
                            getattr(part, 'text', '') or part.get('text', '')
                        )
                text = ''.join(texts)
            return text

        used_retry = False
        used_fallback = False

        response = _request(model_name, max_tokens)
        _logger.info(
            'Raw response: %s',
            response.model_dump()
            if hasattr(response, 'model_dump')
            else response.__dict__,
        )
        text = _extract_text(response)

        if not text.strip():
            used_retry = True
            retry_tokens = max(max_tokens, 128)
            response = _request(model_name, retry_tokens)
            _logger.info(
                'Raw response (retry): %s',
                response.model_dump()
                if hasattr(response, 'model_dump')
                else response.__dict__,
            )
            text = _extract_text(response)
            if not text.strip() and model_name == 'gpt-5-nano':
                used_fallback = True
                fallback_model = 'gpt-5-mini'
                _logger.info(
                    'Falling back from %s to %s due to empty response',
                    model_name,
                    fallback_model,
                )
                response = _request(fallback_model, retry_tokens)
                model_name = fallback_model
                _logger.info(
                    'Raw response (fallback): %s',
                    response.model_dump()
                    if hasattr(response, 'model_dump')
                    else response.__dict__,
                )
                text = _extract_text(response)

        if not text.strip():
            raise ValueError('Empty response from model')

        usage_obj = getattr(response, 'usage', None)
        usage = {
            'prompt_tokens': getattr(usage_obj, 'input_tokens', 0),
            'completion_tokens': getattr(usage_obj, 'output_tokens', 0),
            'total_tokens': getattr(usage_obj, 'total_tokens', 0),
        }
        if not usage['total_tokens']:
            usage['total_tokens'] = (
                usage['prompt_tokens'] + usage['completion_tokens']
            )
        self._log_usage(
            model_name,
            usage,
            messages,
            text,
            used_retry=used_retry,
            used_fallback=used_fallback,
        )
        return text

    @api.model
    def _log_usage(
        self,
        model_name,
        usage,
        messages,
        response,
        used_retry=False,
        used_fallback=False,
    ):
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get(
            'total_tokens', prompt_tokens + completion_tokens
        )
        pricing = PRICING.get(model_name, {})
        cost = (
            prompt_tokens * pricing.get('prompt', 0)
            + completion_tokens * pricing.get('completion', 0)
        )

        def _stringify(content):
            if isinstance(content, list):
                texts = []
                for part in content:
                    if isinstance(part, dict) or hasattr(part, 'get'):
                        texts.append(
                            getattr(part, 'text', '') or part.get('text', '')
                        )
                    else:
                        texts.append(
                            getattr(part, 'text', '') or str(part)
                        )
                return ''.join(texts)
            return content or ''

        self.env['gpt.completion.log'].sudo().create(
            {
                'model_name': model_name,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'cost': cost,
                'prompt': '\n'.join(
                    _stringify(m.get('content', '')) for m in messages
                ),
                'response': response,
                'used_retry': used_retry,
                'used_fallback': used_fallback,
            }
        )
