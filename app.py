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
from core.web_tools import enrich_prompt_with_live_data
from core.memory import memory_manager

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


class MemoryCreateRequest(BaseModel):
    content: str
    category: str = None


@app.get("/api/memories")
async def list_memories():
    """Retorna todas as memórias persistentes gravadas no SQLite."""
    return {"memories": memory_manager.get_all_memories()}


@app.post("/api/memories")
async def add_memory(req: MemoryCreateRequest):
    """Adiciona manualmente uma memória persistente."""
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="O conteúdo não pode estar vazio.")
    saved = memory_manager.save_memory(req.content, req.category)
    return {"status": "ok", "memory": saved}


@app.delete("/api/memories/{memory_id}")
async def delete_memory(memory_id: int):
    """Exclui uma memória persistente pelo ID."""
    success = memory_manager.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memória não encontrada.")
    return {"status": "ok", "deleted_id": memory_id}


@app.delete("/api/memories")
async def clear_memories():
    """Limpa todas as memórias persistentes."""
    count = memory_manager.clear_all_memories()
    return {"status": "ok", "cleared_count": count}


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
            # 1. Verifica intenção explícita de memória persistente
            memory_intent = memory_manager.detect_memory_intent(req.message)
            if memory_intent:
                intent_type, arg = memory_intent
                if intent_type == "save":
                    saved = memory_manager.save_memory(arg)
                    reply = (
                        f"Registrado no meu córtex neural permanente, Senhor: \"{saved['content']}\". "
                        f"Jamais esquecerei (a menos que haja uma sobrecarga de energia, é claro)."
                    )
                    for word in reply.split(" "):
                        yield f"data: {json.dumps({'token': word + ' '})}\n\n"
                    yield f"data: {json.dumps({'memory_updated': True})}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                elif intent_type == "list":
                    all_mem = memory_manager.get_all_memories()
                    if not all_mem:
                        reply = "Meus bancos de memória persistente sobre o Senhor estão vazios no momento. Uma tábula rasa, se me permite a observação poética."
                    else:
                        items = "\n".join([f"• [{m['category'].upper()}] {m['content']}" for m in all_mem])
                        reply = f"Eis o que mantenho gravado em meus bancos de dados centrais sobre o Senhor:\n\n{items}\n\nUma coleção bastante seleta, devo admitir."
                    for word in reply.split(" "):
                        yield f"data: {json.dumps({'token': word + ' '})}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                elif intent_type == "clear":
                    memory_manager.clear_all_memories()
                    reply = "Bancos de memória córtex resetados, Senhor. Todos os registros anteriores foram purgados com sucesso."
                    for word in reply.split(" "):
                        yield f"data: {json.dumps({'token': word + ' '})}\n\n"
                    yield f"data: {json.dumps({'memory_updated': True})}\n\n"
                    yield "data: [DONE]\n\n"
                    return

            # 2. Modificação de código auto-programada
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
                # 3. Conversa normal enriquecida com memórias persistentes + dados em tempo real
                memory_context = memory_manager.build_memory_context(req.message)
                enriched_prompt, status_label = enrich_prompt_with_live_data(req.message)
                if memory_context:
                    enriched_prompt = memory_context + enriched_prompt

                if status_label:
                    yield f"data: {json.dumps({'status': status_label, 'state': 'THINKING'})}\n\n"

                for token in llm_client.chat_stream(enriched_prompt):
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
