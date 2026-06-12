import os
import requests
from typing import Any, Dict


class GroqProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.url = "https://api.groq.com/openai/v1/chat/completions"

        if not self.api_key:
            raise ValueError("GROQ_API_KEY is missing")

    def generate_response(self, prompt: str, message: str) -> Dict[str, Any]:

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            "temperature": 0.2
        }

        try:
            response = requests.post(
                self.url,
                headers=headers,
                json=payload,
                timeout=30
            )

            # IMPORTANT DEBUG
            print("\n========== GROQ STATUS ==========")
            print(response.status_code)
            print(response.text)
            print("================================\n")

            return response.json()

        except Exception as e:
            print("\n❌ GROQ REQUEST FAILED ❌")
            print(str(e))

            return {
                "error": str(e),
                "choices": []
            }