"""
Módulo de Ações e Comandos de Sistema do J.A.R.V.I.S.
Permite executar tarefas locais como consulta de status do sistema, data/hora e abertura de sites.
"""

from datetime import datetime
import platform
import webbrowser
import os
import ctypes
from typing import Dict, Any


def get_system_time() -> str:
    """Retorna data e hora atuais formatadas em português."""
    now = datetime.now()
    dias = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
    dia_semana = dias[now.weekday()]
    return f"{dia_semana}, {now.strftime('%d/%m/%Y às %H:%M:%S')}"


def get_memory_info() -> Dict[str, Any]:
    """Obtém informações de memória RAM no Windows usando ctypes."""
    try:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            total_gb = stat.ullTotalPhys / (1024 ** 3)
            avail_gb = stat.ullAvailPhys / (1024 ** 3)
            used_gb = total_gb - avail_gb
            return {
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "avail_gb": round(avail_gb, 2),
                "percent_used": stat.dwMemoryLoad,
            }
    except Exception:
        pass
    return {}


def get_system_stats() -> Dict[str, Any]:
    """Coleta métricas do computador."""
    mem = get_memory_info()
    return {
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count() or 1,
        "memory": mem,
        "datetime": get_system_time(),
    }


def open_browser(target: str) -> bool:
    """Abre uma URL ou pesquisa no navegador padrão."""
    if not target.startswith(("http://", "https://")):
        url = f"https://www.google.com/search?q={target}"
    else:
        url = target
    return webbrowser.open(url)
