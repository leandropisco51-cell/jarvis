"""
Servidor Web FastAPI do J.A.R.V.I.S.
Provê a interface Web holográfica, endpoints de telemetria e streaming SSE para a LLM local.
"""

import json
import os
from pathlib import Path
from typing import Generator
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.llm_client import LLMClient
from core.config import DEFAULT_MODEL
from core.actions import get_system_stats, get_system_time
from core.coder_agent import CoderAgent

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"

app = FastAPI(title="J.A.R.V.I.S. Tactical HUD", version="1.0.0")

# Montar arquivos estáticos (CSS, JS, imagens)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Instância global do cliente LLM
llm_client = LLMClient(model=DEFAULT_MODEL)


class ChatRequest(BaseModel):
    message: str


class ModelChangeRequest(BaseModel):
    model: str


@app.get("/")
async def get_index():
    """Retorna a página principal do HUD holográfico."""
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Template index.html não encontrado")
    return FileResponse(str(index_file))


@app.get("/api/status")
async def get_status():
    """Retorna a telemetria do sistema e integridade do Ollama."""
    stats = get_system_stats()
    stats["ollama_online"] = llm_client.check_health()
    stats["current_model"] = llm_client.model
    return stats


@app.get("/api/models")
async def list_models():
    """Lista todos os modelos locais disponíveis no servidor Ollama."""
    models = llm_client.list_models()
    return {
        "models": models if models else [llm_client.model],
        "current_model": llm_client.model,
    }


@app.post("/api/model")
async def switch_model(req: ModelChangeRequest):
    """Altera o modelo LLM ativo."""
    llm_client.set_model(req.model)
    return {"status": "ok", "current_model": llm_client.model}


@app.post("/api/chat")
async def chat_stream_endpoint(req: ChatRequest):
    """
    Endpoint de streaming SSE (Server-Sent Events) para resposta em tempo real.
    Gera eventos formatados como: data: {"token": "..."}\n\n
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="A mensagem não pode estar vazia.")

    if not llm_client.check_health():
        raise HTTPException(
            status_code=503,
            detail="Servidor Ollama desconectado. Verifique se 'ollama serve' está ativo."
        )

    def event_generator() -> Generator[str, None, None]:
        try:
            if CoderAgent.is_coding_request(req.message):
                for event in CoderAgent.process_instruction(req.message, llm_client):
                    if event["type"] == "status":
                        yield f"data: {json.dumps({'status': event['data'], 'state': 'CODING'})}\n\n"
                    elif event["type"] == "token":
                        yield f"data: {json.dumps({'token': event['data']})}\n\n"
                    elif event["type"] == "done":
                        yield "data: [DONE]\n\n"
                        break
            else:
                for token in llm_client.chat_stream(req.message):
                    data = json.dumps({"token": token})
                    yield f"data: {data}\n\n"
                yield "data: [DONE]\n\n"
        except Exception as e:
            err_data = json.dumps({"token": f"\n[Erro na execução]: {str(e)}"})
            yield f"data: {err_data}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


def start_server(host: str = "127.0.0.1", port: int = 8000):
    """Inicia o servidor Uvicorn com recarregamento dinâmico."""
    uvicorn.run("app:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    start_server()
