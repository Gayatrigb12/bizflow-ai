from typing import Any, Dict

class OpenAIClient:
    def generate_response(self, prompt: str, message: str) -> Dict[str, Any]:
        raise NotImplementedError