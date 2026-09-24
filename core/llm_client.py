"""
Cliente de comunicação com o Ollama para o J.A.R.V.I.S.
Gerencia chamadas de API, streaming de tokens e histórico da conversa.
"""

import json
from typing import Generator, List, Dict, Any, Optional
import requests

from core.config import (
    OLLAMA_HOST,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    JARVIS_SYSTEM_PROMPT,
)


class LLMClient:
    """Cliente responsável pela comunicação com o serviço local Ollama."""

    def __init__(self, host: str = OLLAMA_HOST, model: str = DEFAULT_MODEL):
        self.host = host.rstrip("/")
        self.model = model
        self.system_prompt = JARVIS_SYSTEM_PROMPT
        self.history: List[Dict[str, str]] = []
        self._init_history()

    def _init_history(self) -> None:
        """Reinicia o histórico incluindo o prompt de sistema do Jarvis."""
        from core.config import JARVIS_SYSTEM_PROMPT
        self.system_prompt = JARVIS_SYSTEM_PROMPT
        self.history = [{"role": "system", "content": self.system_prompt}]

    def check_health(self) -> bool:
        """Verifica se o servidor Ollama está respondendo."""
        try:
            res = requests.get(f"{self.host}/api/version", timeout=3)
            return res.status_code == 200
        except requests.RequestException:
            return False

    def list_models(self) -> List[str]:
        """Retorna os nomes dos modelos locais disponíveis no Ollama."""
        try:
            res = requests.get(f"{self.host}/api/tags", timeout=5)
            if res.status_code == 200:
                data = res.json()
                return [m["name"] for m in data.get("models", [])]
            return []
        except requests.RequestException:
            return []

    def set_model(self, model_name: str) -> None:
        """Altera o modelo LLM ativo."""
        self.model = model_name

    def clear_history(self) -> None:
        """Limpa as mensagens do usuário e recarrega o prompt de sistema."""
        self._init_history()

    def chat_stream(
        self, prompt: str, temperature: float = DEFAULT_TEMPERATURE
    ) -> Generator[str, None, str]:
        """
        Envia uma mensagem para o Ollama em modo streaming.
        Gera tokens em tempo real conforme são recebidos da LLM.
        Retorna a resposta completa consolidada.
        """
        self.history.append({"role": "user", "content": prompt})

        # Mantém histórico focado (sistema + até 6 mensagens mais recentes)
        if len(self.history) > 7:
            self.history = [self.history[0]] + self.history[-6:]

        payload = {
            "model": self.model,
            "messages": self.history,
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }

        full_reply = []
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json=payload,
                stream=True,
                timeout=120,
            )
            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    delta = data.get("message", {}).get("content", "")
                    if delta:
                        full_reply.append(delta)
                        yield delta
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue

            complete_text = "".join(full_reply)
            self.history.append({"role": "assistant", "content": complete_text})
            return complete_text

        except requests.RequestException as e:
            # Em caso de falha, remove a última mensagem do usuário para não corromper o histórico
            if self.history and self.history[-1]["role"] == "user":
                self.history.pop()
            error_msg = f"Erro na comunicação com a LLM local: {str(e)}"
            yield error_msg
            return error_msg
