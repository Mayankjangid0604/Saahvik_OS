from typing import Protocol
from enterprise_os.providers.ai.request import AIRequest
from enterprise_os.providers.ai.response import AIResponse

class AIProvider(Protocol):
    @property
    def name(self) -> str:
        ...

    def chat(self, request: AIRequest) -> AIResponse:
        ...
        
    def generate(self, request: AIRequest) -> AIResponse:
        ...
        
    def analyse(self, request: AIRequest) -> AIResponse:
        ...
        
    def summarise(self, request: AIRequest) -> AIResponse:
        ...
        
    def embed(self, request: AIRequest) -> AIResponse:
        ...
        
    def health(self) -> str:
        ...
