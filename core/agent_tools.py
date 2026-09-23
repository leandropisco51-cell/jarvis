"""
Ferramentas de Engenharia de Software e Segurança do J.A.R.V.I.S.
Permite ao Jarvis inspecionar, editar e criar seus próprios arquivos com validação de sintaxe e rollback via Git.
"""

import ast
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Diretório raiz do projeto Jarvis
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Extensões e pastas permitidas
ALLOWED_EXTENSIONS = {".py", ".html", ".css", ".js", ".md", ".toml", ".txt", ".json"}
IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "build", "dist"}


def _resolve_safe_path(rel_path: str) -> Path:
    """Resolve o caminho garantindo que permaneça dentro da pasta do projeto."""
    clean_path = Path(rel_path.strip().replace("\\", "/"))
    abs_path = (PROJECT_ROOT / clean_path).resolve()
    if not str(abs_path).startswith(str(PROJECT_ROOT)):
        raise PermissionError(f"Acesso negado: o arquivo '{rel_path}' está fora do diretório do projeto.")
    return abs_path


def list_project_files() -> List[str]:
    """Lista todos os arquivos do projeto que o Jarvis pode inspecionar e modificar."""
    files = []
    for root, dirs, filenames in os.walk(PROJECT_ROOT):
        # Ignora diretórios proibidos
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for f in filenames:
            file_path = Path(root) / f
            if file_path.suffix.lower() in ALLOWED_EXTENSIONS:
                rel = file_path.relative_to(PROJECT_ROOT)
                files.append(str(rel).replace("\\", "/"))
    return sorted(files)


def read_project_file(rel_path: str) -> str:
    """Lê o conteúdo completo de um arquivo do projeto."""
    target = _resolve_safe_path(rel_path)
    if not target.exists():
        raise FileNotFoundError(f"Arquivo '{rel_path}' não encontrado.")
    return target.read_text(encoding="utf-8", errors="replace")


def validate_code(rel_path: str, content: str) -> Tuple[bool, Optional[str]]:
    """Valida a integridade sintática antes de salvar para evitar quebrar o sistema."""
    ext = Path(rel_path).suffix.lower()
    if ext == ".py":
        try:
            ast.parse(content, filename=rel_path)
        except SyntaxError as e:
            return False, f"Erro de sintaxe Python na linha {e.lineno}: {e.msg}"
    return True, None


def create_safety_checkpoint(description: str = "Auto-modificação do Jarvis") -> bool:
    """Cria um ponto de salvamento via git stash/commit para que possa ser revertido."""
    try:
        subprocess.run(
            ["git", "add", "."],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Cria commit temporário de checkpoint
        res = subprocess.run(
            ["git", "commit", "-m", f"checkpoint: {description}"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return res.returncode == 0
    except Exception:
        return False


def rollback_last_change() -> Tuple[bool, str]:
    """Desfaz a última alteração efetuada voltando ao commit anterior no Git."""
    try:
        # Reverte alterações não commitadas ou último commit de checkpoint
        subprocess.run(["git", "restore", "."], cwd=str(PROJECT_ROOT), timeout=10)
        res = subprocess.run(
            ["git", "reset", "--hard", "HEAD~1"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if res.returncode == 0:
            return True, "Última alteração desfeita com sucesso. Código restaurado ao estado anterior."
        return False, f"Falha ao reverter: {res.stderr}"
    except Exception as e:
        return False, f"Erro ao executar rollback: {str(e)}"


def write_project_file(rel_path: str, content: str) -> Tuple[bool, str]:
    """Cria ou sobrescreve um arquivo do projeto com validação prévia de sintaxe."""
    target = _resolve_safe_path(rel_path)

    # 1. Validação de sintaxe
    is_valid, err = validate_code(rel_path, content)
    if not is_valid:
        return False, f"Alteração abortada por segurança: {err}"

    # 2. Criar diretórios pais se não existirem
    target.parent.mkdir(parents=True, exist_ok=True)

    # 3. Salva o arquivo com encoding UTF-8
    target.write_text(content, encoding="utf-8")
    return True, f"Arquivo '{rel_path}' atualizado com sucesso."


def apply_file_patch(rel_path: str, target_text: str, replacement_text: str) -> Tuple[bool, str]:
    """Aplica substituição precisa de um trecho de código em um arquivo existente."""
    target = _resolve_safe_path(rel_path)
    if not target.exists():
        return False, f"Arquivo '{rel_path}' não encontrado para edição."

    current_content = target.read_text(encoding="utf-8")
    if target_text not in current_content:
        return False, f"O trecho alvo especificado não foi encontrado no arquivo '{rel_path}'."

    new_content = current_content.replace(target_text, replacement_text, 1)

    # Valida sintaxe
    is_valid, err = validate_code(rel_path, new_content)
    if not is_valid:
        return False, f"Alteração abortada por segurança: {err}"

    target.write_text(new_content, encoding="utf-8")
    return True, f"Trecho de código modificado com sucesso em '{rel_path}'."
