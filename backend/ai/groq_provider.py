import logging
import os
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)


class GroqProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key or os.getenv('GROQ_API_KEY', '')
        self.url = 'https://api.groq.com/openai/v1/chat/completions'

        if not self.api_key:
            raise ValueError('GROQ_API_KEY is missing')

    def generate_response(self, prompt: str, message: str) -> Dict[str, Any]:
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        payload = {
            'model': 'llama-3.3-70b-versatile',
            'messages': [
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': message},
            ],
            'temperature': 0.2,
        }

        try:
            response = requests.post(
                self.url,
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.exception('Groq API request failed')
            return {
                'error': str(exc),
                'choices': [],
            }
