# from typing import Any, Dict

# import requests

# # from backend.ai.provider_interface import AIProvider
# from backend.ai.openai_provider import OpenAIClient


# class OpenAIProvider(OpenAIClient):
#     def __init__(self, api_key: str, model: str = 'gpt-3.5-turbo'):
#         self.api_key = api_key
#         self.model = model

#     def generate_response(self, prompt: str, message: str) -> Dict[str, Any]:
#         response = requests.post(
#             'https://api.openai.com/v1/chat/completions',
#             json={
#                 'model': self.model,
#                 'messages': [
#                     {'role': 'system', 'content': prompt},
#                     {'role': 'user', 'content': message},
#                 ],
#                 'temperature': 0.1,
#                 'max_tokens': 1000,
#             },
#             headers={
#                 'Authorization': f'Bearer {self.api_key}',
#                 'Content-Type': 'application/json',
#             },
#             timeout=60,
#         )
#         response.raise_for_status()
#         return response.json()

from typing import Any, Dict
import requests

from backend.ai.openai_client import OpenAIClient


class OpenAIProvider(OpenAIClient):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model

    def generate_response(self, prompt: str, message: str) -> Dict[str, Any]:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": message},
                ],
                "temperature": 0.1,
                "max_tokens": 1000,
            },
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
