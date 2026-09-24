"""
Módulo de Memória Persistente de Longo Prazo do J.A.R.V.I.S.
Utiliza banco SQLite local para armazenar fatos, preferências e diretrizes do usuário.
"""

import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "memory.db"


class MemoryManager:
    """Gerenciador do banco de memória persistente SQLite do J.A.R.V.I.S."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Cria e retorna uma conexão com o banco SQLite."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Inicializa as tabelas do banco de dados caso não existam."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL DEFAULT 'general',
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.commit()

    @staticmethod
    def categorize_content(content: str) -> str:
        """Classifica automaticamente a memória em uma categoria semântica."""
        content_lower = content.lower()
        if any(w in content_lower for w in ["nome", "chamo", "sou o", "trabalho como", "profissão", "idade"]):
            return "perfil"
        if any(w in content_lower for w in ["gosto", "prefiro", "preferência", "favorito", "favorita", "não gosto", "odeio"]):
            return "preferencia"
        if any(w in content_lower for w in ["projeto", "desenvolvendo", "código", "python", "sistema", "estudo", "empresa"]):
            return "projeto"
        if any(w in content_lower for w in ["lembrar", "anotação", "nota", "aviso", "importante"]):
            return "nota"
        return "geral"

    def save_memory(self, content: str, category: Optional[str] = None) -> Dict:
        """
        Salva um novo fato ou atualiza se já existir algo idêntico.
        Retorna o registro salvo.
        """
        cleaned_content = content.strip()
        if cleaned_content and cleaned_content[0].islower():
            cleaned_content = cleaned_content[0].upper() + cleaned_content[1:]
        cat = category or self.categorize_content(cleaned_content)

        with self._get_connection() as conn:
            # Evita duplicatas idênticas
            cursor = conn.execute(
                "SELECT id FROM memories WHERE LOWER(content) = LOWER(?)",
                (cleaned_content,),
            )
            existing = cursor.fetchone()
            if existing:
                conn.execute(
                    "UPDATE memories SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (existing["id"],),
                )
                conn.commit()
                return {"id": existing["id"], "category": cat, "content": cleaned_content, "action": "updated"}

            cursor = conn.execute(
                "INSERT INTO memories (category, content) VALUES (?, ?)",
                (cat, cleaned_content),
            )
            conn.commit()
            return {"id": cursor.lastrowid, "category": cat, "content": cleaned_content, "action": "created"}

    def get_all_memories(self) -> List[Dict]:
        """Retorna todas as memórias ordenadas pelas mais recentes."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, category, content, created_at FROM memories ORDER BY id DESC"
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "category": row["category"],
                    "content": row["content"],
                    "created_at": str(row["created_at"]),
                }
                for row in rows
            ]

    def delete_memory(self, memory_id: int) -> bool:
        """Exclui uma memória pelo ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_all_memories(self) -> int:
        """Limpa todo o banco de memórias. Retorna quantidade de linhas removidas."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM memories")
            conn.commit()
            return cursor.rowcount

    def search_relevant_memories(self, query: str, limit: int = 4) -> List[str]:
        """
        Busca memórias relevantes usando palavras-chave da consulta.
        Sempre inclui itens da categoria 'perfil' (como o nome do usuário).
        """
        stop_words = {
            "o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
            "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "que",
            "e", "ou", "se", "qual", "quais", "como", "quem", "jarvis", "voce",
            "você", "senhor", "me", "meu", "minha", "ele", "ela", "eles", "elas",
            "este", "esta", "isso", "isto", "favor", "por favor"
        }

        # Extrai palavras significativas
        tokens = [
            w for w in re.findall(r"\w+", query.lower())
            if len(w) > 2 and w not in stop_words
        ]

        with self._get_connection() as conn:
            memories: List[str] = []

            # 1. Sempre recupera fatos de perfil (ex: nome, identidade do usuário)
            cursor = conn.execute(
                "SELECT content FROM memories WHERE category = 'perfil' ORDER BY id DESC LIMIT 3"
            )
            for row in cursor.fetchall():
                if row["content"] not in memories:
                    memories.append(row["content"])

            # 2. Busca por correspondência das palavras-chave
            if tokens:
                placeholders = " OR ".join(["LOWER(content) LIKE ?" for _ in tokens])
                params = [f"%{token}%" for token in tokens]
                cursor = conn.execute(
                    f"SELECT content FROM memories WHERE {placeholders} ORDER BY id DESC LIMIT ?",
                    (*params, limit),
                )
                for row in cursor.fetchall():
                    if row["content"] not in memories:
                        memories.append(row["content"])

            return memories[:limit]

    def build_memory_context(self, user_query: str) -> str:
        """
        Constrói o bloco de injeção de contexto de memórias para a LLM.
        """
        relevant = self.search_relevant_memories(user_query)
        if not relevant:
            return ""

        facts_text = "\n".join([f"• {fact}" for fact in relevant])
        return (
            f"[MEMÓRIAS PERSISTENTES CÓRTEX DO SENHOR]:\n"
            f"{facts_text}\n"
            f"(Utilize essas informações sobre o Senhor caso pertinentes, de forma natural, perspicaz e concisa.)\n\n"
        )

    def detect_memory_intent(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Detecta intenções explícitas de memória na fala do usuário.
        Retorna (tipo_intencao, argumento) ou None.
        Tipos possíveis:
          - 'save': salvar novo fato
          - 'list': listar fatos conhecidos
          - 'clear': apagar todas as memórias
          - 'delete_match': apagar fato específico
        """
        text_clean = text.strip()
        lower = text_clean.lower()

        # 1. Intenção de listar memórias
        if any(
            phrase in lower
            for phrase in [
                "o que você lembra sobre mim",
                "o que você lembra de mim",
                "o que você sabe sobre mim",
                "quais são minhas memórias",
                "quais sao minhas memorias",
                "o que tem na sua memória",
                "o que tem na sua memoria",
                "liste suas memórias",
                "liste suas memorias",
                "quais informações você tem sobre mim",
            ]
        ):
            return ("list", "")

        # 2. Intenção de limpar tudo
        if any(
            phrase in lower
            for phrase in [
                "esqueça tudo",
                "esqueca tudo",
                "apague todas as memórias",
                "apague todas as memorias",
                "limpe sua memória",
                "limpe sua memoria",
                "limpe o banco de memórias",
                "limpe o banco de memorias",
            ]
        ):
            return ("clear", "")

        # 3. Intenção de salvar via padrões explícitos
        save_patterns = [
            r"(?:jarvis[, ]+)?(?:por favor[, ]+)?(?:lembre-se|lembre|memorize|grave|guarde|anote)(?:\s+(?:que|de que|de))?\s+(.+)",
            r"(?:meu nome é|eu me chamo|pode me chamar de)\s+([A-Za-zÀ-ÿ\s]+)",
            r"(?:minha preferência é|eu prefiro|meu favorito é|minha favorita é)\s+(.+)",
            r"(?:nunca se esqueça de que|nunca se esqueça que)\s+(.+)",
        ]

        for pattern in save_patterns:
            match = re.search(pattern, text_clean, re.IGNORECASE)
            if match:
                fact = match.group(1).strip().rstrip(".!?;")
                # Se contiver apresentação de nome próprio, formata com elegância
                name_match = re.search(r"(?:meu nome é|eu me chamo|pode me chamar de)\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)", fact, re.IGNORECASE)
                if name_match:
                    name = name_match.group(1).strip()
                    remainder = re.sub(r"^(?:meu nome é|eu me chamo|pode me chamar de)\s+[A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*\s*(?:e|,)?\s*", "", fact, flags=re.IGNORECASE).strip()
                    if remainder:
                        fact = f"O nome do Senhor é {name}, e {remainder}"
                    else:
                        fact = f"O nome do Senhor é {name}"
                return ("save", fact)

        return None


# Instância global do gerenciador de memória
memory_manager = MemoryManager()
