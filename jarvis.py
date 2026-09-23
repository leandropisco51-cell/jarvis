"""
J.A.R.V.I.S. - Interface Principal
Assistente de Inteligência Artificial Local com LLaMA 3.2 e Terminal HUD.
"""

import sys
import os

# Configuração de encoding UTF-8 para terminais Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8-sig")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.llm_client import LLMClient
from core.config import DEFAULT_MODEL
from core.actions import get_system_time, get_system_stats, open_browser

console = Console()

BANNER = r"""
   _   ___  ___  _   _ _____ _____ 
  | | / _ \ | _ \ | | | |_   _/  ___|
  | |/ /_\ \| v / | | | | | | \ `--. 
  | ||  _  ||   \ | | | | | |  `--. \
/\__/| | | || |\ \ \_/ /_| |_/\__/ /
\____/\_| |_/\_| \_|\___/ \___/\____/ 
 Just A Rather Very Intelligent System
"""


def show_banner(model_name: str, status_online: bool):
    """Exibe o HUD inicial do JARVIS."""
    status_text = (
        "[bold green][ON] SISTEMAS OPERACIONAIS[/bold green]"
        if status_online
        else "[bold red][OFF] SERVICO OFFLINE (Inicie o Ollama)[/bold red]"
    )

    info_text = (
        f"[bold cyan]{BANNER}[/bold cyan]\n"
        f"  [white]Status:[/white] {status_text}\n"
        f"  [white]Modelo Ativo:[/white] [yellow]{model_name}[/yellow]\n"
        f"  [white]Data/Hora:[/white] [dim]{get_system_time()}[/dim]\n"
        f"  [dim]Digite [bold cyan]/ajuda[/bold cyan] para ver comandos ou converse normalmente.[/dim]"
    )

    console.print(
        Panel(
            info_text,
            title="[bold cyan]HUD TATICO[/bold cyan]",
            border_style="cyan",
            expand=False,
        )
    )


def show_help():
    """Exibe a lista de comandos disponíveis."""
    table = Table(title="Comandos do Sistema Jarvis", border_style="cyan")
    table.add_column("Comando", style="bold yellow")
    table.add_column("Descrição", style="white")

    table.add_row("/ajuda", "Exibe esta lista de comandos")
    table.add_row("/status", "Exibe telemetria de hardware e status da LLM")
    table.add_row("/modelo [nome]", "Lista modelos locais ou alterna o modelo ativo")
    table.add_row("/web", "Inicia a interface Web Holográfica no navegador")
    table.add_row("/hora", "Informa o dia e horário atual")
    table.add_row("/abrir <url/busca>", "Abre uma pesquisa ou site no navegador")
    table.add_row("/limpar", "Limpa o histórico de memória da conversa atual")
    table.add_row("/sair", "Encerra os protocolos do Jarvis")

    console.print(table)


def show_status(client: LLMClient):
    """Exibe estatísticas de telemetria do sistema e do Ollama."""
    stats = get_system_stats()
    mem = stats.get("memory", {})

    table = Table(title="Telemetria de Sistema - Jarvis", border_style="blue")
    table.add_column("Métrica", style="bold cyan")
    table.add_column("Valor", style="white")

    table.add_row("Sistema Operacional", stats.get("os", "Desconhecido"))
    table.add_row("Arquitetura / CPU", f"{stats.get('machine')} ({stats.get('cpu_count')} núcleos)")

    if mem:
        mem_str = f"{mem.get('used_gb')} GB / {mem.get('total_gb')} GB ({mem.get('percent_used')}% em uso)"
        table.add_row("Memória RAM", mem_str)

    ollama_ok = client.check_health()
    table.add_row(
        "Servidor Ollama",
        "[bold green]Conectado (127.0.0.1:11434)[/bold green]" if ollama_ok else "[bold red]Desconectado[/bold red]",
    )
    table.add_row("Modelo LLM Ativo", f"[yellow]{client.model}[/yellow]")

    console.print(table)


def main():
    """Loop principal de execução do Jarvis."""
    if "--web" in sys.argv:
        console.print("\n[bold cyan]Jarvis:[/bold cyan] Inicializando interface Web Holográfica em http://127.0.0.1:8000 ...")
        open_browser("http://127.0.0.1:8000")
        from app import start_server
        start_server()
        return

    client = LLMClient(model=DEFAULT_MODEL)
    is_online = client.check_health()

    show_banner(client.model, is_online)

    if not is_online:
        console.print(
            "\n[bold yellow]Aviso:[/bold yellow] O servidor Ollama não está ativo no momento.\n"
            "Execute [bold green]ollama serve[/bold green] em segundo plano para ativar a IA local.\n"
        )

    while True:
        try:
            console.print("\n[bold green]Você > [/bold green]", end="")
            user_input = input().lstrip("\ufeff").strip()

            if not user_input:
                continue

            # Comandos de controle
            if user_input.lower() in ("/sair", "sair", "exit", "quit"):
                console.print("\n[bold cyan]Jarvis:[/bold cyan] Protocolos encerrados. Até logo, Senhor.\n")
                break

            elif user_input.lower() == "/ajuda":
                show_help()
                continue

            elif user_input.lower() == "/web":
                console.print("\n[bold cyan]Jarvis:[/bold cyan] Abrindo interface Web Holográfica em http://127.0.0.1:8000 ...")
                open_browser("http://127.0.0.1:8000")
                from app import start_server
                start_server()
                break

            elif user_input.lower() == "/status":
                show_status(client)
                continue

            elif user_input.lower() == "/hora":
                console.print(f"\n[bold cyan]Jarvis:[/bold cyan] São exatamente {get_system_time()}, Senhor.\n")
                continue

            elif user_input.lower() == "/limpar":
                client.clear_history()
                console.print("\n[bold cyan]Jarvis:[/bold cyan] Memória contextual reiniciada com sucesso, Senhor.\n")
                continue

            elif user_input.lower().startswith("/modelo"):
                parts = user_input.split(maxsplit=1)
                available = client.list_models()
                if len(parts) == 1:
                    console.print(f"\n[bold cyan]Jarvis:[/bold cyan] Modelo atual: [yellow]{client.model}[/yellow]")
                    console.print(f"Modelos locais disponíveis no Ollama: {available}\n")
                    console.print("Para alternar, use: [bold yellow]/modelo <nome>[/bold yellow]")
                else:
                    new_model = parts[1].strip()
                    client.set_model(new_model)
                    console.print(f"\n[bold cyan]Jarvis:[/bold cyan] Modelo alterado para [yellow]{new_model}[/yellow].\n")
                continue

            elif user_input.lower().startswith("/abrir "):
                target = user_input[7:].strip()
                console.print(f"\n[bold cyan]Jarvis:[/bold cyan] Abrindo '{target}' no navegador...")
                open_browser(target)
                continue

            # Envio para a LLM Local
            if not client.check_health():
                console.print(
                    "\n[bold red]Jarvis:[/bold red] Senhor, não consigo me comunicar com o serviço Ollama. "
                    "Por favor verifique se o servidor está rodando (execute 'ollama serve').\n"
                )
                continue

            console.print(f"\n[bold cyan]Jarvis ({client.model}):[/bold cyan] ", end="")
            
            # Streaming da resposta token por token
            for chunk in client.chat_stream(user_input):
                console.print(chunk, end="", style="bold white")
            console.print("\n")

        except KeyboardInterrupt:
            console.print("\n\n[bold yellow]Jarvis:[/bold yellow] Operação interrompida pelo usuário.")
            continue
        except EOFError:
            console.print("\n[bold cyan]Jarvis:[/bold cyan] Encerrando. Até logo, Senhor.\n")
            break
        except Exception as e:
            console.print(f"\n[bold red]Erro inesperado:[/bold red] {e}\n")


if __name__ == "__main__":
    main()
