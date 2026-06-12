from abc import ABC, abstractmethod
from typing import Dict, Any


class AIProvider(ABC):
    @abstractmethod
    def generate_response(self, prompt: str, message: str) -> Dict[str, Any]:
        raise NotImplementedError
