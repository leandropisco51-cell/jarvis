"""
Módulo de Auto-Engenharia de Software do J.A.R.V.I.S. (Coder Agent)
Analisa instruções de voz/texto do usuário, inspeciona arquivos, gera modificações de código e as aplica com segurança.
"""

import json
import re
from typing import Generator, Dict, Any, Tuple, Optional
from core.llm_client import LLMClient
from core.agent_tools import (
    list_project_files,
    read_project_file,
    write_project_file,
    apply_file_patch,
    create_safety_checkpoint,
    rollback_last_change,
)

# Palavra-chave de autorização do protocolo de auto-programação
PROTOCOL_KEYWORD = "autoprog"

ROLLBACK_KEYWORDS = [
    "desfaça", "desfazer", "desfazer a última", "desfaça a última alteração",
    "volte ao estado anterior", "reverta", "rollback", "reverter código"
]


class CoderAgent:
    """Agente de código auto-programável integrado ao Jarvis com ativação por protocolo seguro."""

    @staticmethod
    def is_coding_request(message: str) -> bool:
        """
        Verifica se a mensagem contém a palavra-chave de autorização 'autoprog'.
        A auto-programação SÓ é acionada quando o usuário menciona explicitamente o protocolo.
        """
        msg_lower = message.lower().strip()
        return PROTOCOL_KEYWORD in msg_lower

    @staticmethod
    def is_rollback_request(message: str) -> bool:
        """Verifica se dentro do protocolo autoprog foi solicitado rollback."""
        msg_lower = message.lower().strip()
        return any(kw in msg_lower for kw in ROLLBACK_KEYWORDS)

    @staticmethod
    def clean_instruction(message: str) -> str:
        """Remove a palavra-chave 'autoprog' e termos comuns de ativação para isolar o comando."""
        cleaned = re.sub(r"\b(protocolo|ativar|iniciar|modo)?\s*autoprog\b[:\s,-]*", "", message, flags=re.IGNORECASE)
        return cleaned.strip() or message

    @classmethod
    def process_instruction(
        cls, instruction: str, client: LLMClient
    ) -> Generator[Dict[str, Any], None, str]:
        """
        Processa a instrução de código, gerando eventos de progresso e aplicando as alterações.
        Yields dicts no formato: {"type": "status" | "token" | "done", "data": ...}
        """
        # 1. Tratar pedido de rollback
        if cls.is_rollback_request(instruction):
            yield {"type": "status", "data": "Revertendo última alteração via Git..."}
            success, msg = rollback_last_change()
            reply = f"Protocolo de rollback executado, Senhor. {msg}"
            yield {"type": "token", "data": reply}
            yield {"type": "done", "data": reply}
            return reply

        actual_instruction = cls.clean_instruction(instruction)
        yield {"type": "status", "data": "Protocolo AUTOPROG ativado: inspecionando arquivos..."}

        # 2. Obter mapa de arquivos do projeto
        files = list_project_files()

        # Determina arquivos potencialmente relevantes para a instrução
        relevant_files = []
        inst_lower = actual_instruction.lower()
        for f in files:
            name = f.lower()
            if "css" in inst_lower and name.endswith(".css"):
                relevant_files.append(f)
            elif ("html" in inst_lower or "tela" in inst_lower or "hud" in inst_lower) and name.endswith(".html"):
                relevant_files.append(f)
            elif ("js" in inst_lower or "script" in inst_lower or "voz" in inst_lower) and name.endswith(".js"):
                relevant_files.append(f)
            elif ("servidor" in inst_lower or "api" in inst_lower) and "app.py" in name:
                relevant_files.append(f)
            elif ("comando" in inst_lower or "ação" in inst_lower or "acao" in inst_lower) and "actions.py" in name:
                relevant_files.append(f)
            elif "config" in inst_lower and "config.py" in name:
                relevant_files.append(f)

        if not relevant_files:
            relevant_files = ["core/actions.py", "core/config.py", "web/static/css/hud.css", "web/static/js/app.js"]

        # Lê conteúdo de amostra dos arquivos mais relevantes para dar contexto exato
        context_snippets = []
        for rf in relevant_files[:2]:
            try:
                content = read_project_file(rf)
                # Limita a 200 linhas para não estourar a janela de contexto local
                lines = content.splitlines()[:200]
                snippet = "\n".join(lines)
                context_snippets.append(f"--- Arquivo: {rf} ---\n{snippet}\n")
            except Exception:
                pass

        files_context = "\n".join(context_snippets)

        prompt_system = (
            "Você é o módulo de Auto-Engenharia de Software do J.A.R.V.I.S.\n"
            "O Senhor ativou o protocolo AUTOPROG e solicitou uma alteração ou adição em sua própria programação.\n"
            f"Arquivos do projeto: {files}\n\n"
            f"Trechos de arquivos relevantes:\n{files_context}\n\n"
            "INSTRUÇÃO IMPORTANTE: Responda ESTRITAMENTE em formato JSON com o seguinte schema:\n"
            "{\n"
            '  "file": "caminho_relativo/do_arquivo",\n'
            '  "action": "patch" ou "write",\n'
            '  "target_text": "texto exato a ser substituído (se action for patch)",\n'
            '  "replacement_text": "novo texto a inserir no lugar (se action for patch)",\n'
            '  "content": "conteúdo completo do arquivo (se action for write)",\n'
            '  "explanation": "resumo polido em português de 1 a 2 frases para o Senhor explicando o que foi alterado"\n'
            "}\n"
            "Não adicione nenhuma explicação fora do bloco JSON."
        )

        user_prompt = f"Instrução do Senhor via protocolo AUTOPROG: {actual_instruction}"

        yield {"type": "status", "data": "Formulando plano de código com a LLM local..."}

        # Faz a chamada à LLM
        messages = [
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": user_prompt},
        ]

        full_raw = []
        try:
            # Usa o modelo mais capaz disponível se possível, ou o ativo
            models = client.list_models()
            chosen_model = "llama3.2:latest" if "llama3.2:latest" in models else client.model

            payload = {
                "model": chosen_model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.2}, # Baixa temperatura para precisão sintática
            }

            import requests
            res = requests.post(f"{client.host}/api/chat", json=payload, timeout=90)
            res.raise_for_status()
            data = res.json()
            raw_reply = data.get("message", {}).get("content", "").strip()

            # Extrair JSON da resposta
            json_match = re.search(r"\{.*\}", raw_reply, re.DOTALL)
            if not json_match:
                # Se não gerou JSON direto, tenta interpretar ou relata o resultado
                reply = f"Senhor, processei a solicitação mas preciso de mais detalhes: {raw_reply[:200]}"
                yield {"type": "token", "data": reply}
                yield {"type": "done", "data": reply}
                return reply

            plan = json.loads(json_match.group(0))
            target_file = plan.get("file", "").strip()
            action = plan.get("action", "patch")
            explanation = plan.get("explanation", "Alteração de código concluída com sucesso.")

            if not target_file:
                reply = "Senhor, não foi possível identificar o arquivo de destino para esta modificação."
                yield {"type": "token", "data": reply}
                yield {"type": "done", "data": reply}
                return reply

            yield {"type": "status", "data": f"Criando checkpoint e aplicando em '{target_file}'..."}

            # Cria checkpoint de segurança
            create_safety_checkpoint(f"Auto-modificação: {instruction[:40]}")

            # Executa a ação
            if action == "write":
                new_content = plan.get("content", "")
                success, result_msg = write_project_file(target_file, new_content)
            else:
                target_text = plan.get("target_text", "")
                replacement_text = plan.get("replacement_text", "")
                success, result_msg = apply_file_patch(target_file, target_text, replacement_text)

            if success:
                final_speech = f"Senhor, auto-programação concluída com sucesso no arquivo {target_file}. {explanation}"
            else:
                final_speech = f"Senhor, a auto-modificação foi interrompida: {result_msg}"

            yield {"type": "token", "data": final_speech}
            yield {"type": "done", "data": final_speech}
            return final_speech

        except Exception as e:
            err_msg = f"Senhor, ocorreu uma exceção durante o protocolo de programação: {str(e)}"
            yield {"type": "token", "data": err_msg}
            yield {"type": "done", "data": err_msg}
            return err_msg
