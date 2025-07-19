"""
LLM integration service for Ollama
Reference: https://github.com/ollama/ollama/blob/main/docs/api.md
"""

import httpx
import json
from typing import Optional, AsyncGenerator, Dict, Any
from fastapi import HTTPException

from app.shared.config import settings


class OllamaService:
    """
    Service for interacting with Ollama LLM server.
    
    Single Responsibility: LLM communication and response generation
    """
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.ollama_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.default_model = settings.default_model
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def check_health(self) -> bool:
        """
        Check if Ollama server is running.
        
        Single Responsibility: Health check
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """
        Get list of available models.
        
        Single Responsibility: Model listing
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            print(f"Error listing models: {e}")
            return []
    
    async def generate_response(
        self, 
        prompt: str, 
        model: str = None,
        context: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ) -> str:
        """
        Generate response from LLM.
        
        Single Responsibility: Response generation
        """
        model = model or self.default_model
        
        # Prepare prompt with context if provided
        if context:
            full_prompt = f"""Context information:
{context}

Based on the context above, please answer the following question:
{prompt}

Answer:"""
        else:
            full_prompt = prompt
        
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": stream,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
                "max_tokens": kwargs.get("max_tokens", 500),
                "stop": kwargs.get("stop", [])
            }
        }
        
        try:
            if stream:
                return self._stream_generate(payload)
            else:
                response = await self.client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
                
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500, 
                detail=f"LLM service error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Unexpected error: {str(e)}"
            )
    
    async def _stream_generate(self, payload: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Stream response from LLM.
        
        Single Responsibility: Streaming response handling
        """
        try:
            async with self.client.stream(
                "POST", 
                f"{self.base_url}/api/generate", 
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data and data["response"]:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Streaming error: {str(e)}"
            )


# Global LLM service instance
llm_service = OllamaService()
