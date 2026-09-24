"""
Módulo de Diagnóstico de Hardware e Otimização do Sistema do J.A.R.V.I.S.
Permite inspecionar CPU, RAM, discos, processos pesados e executar limpezas seguras de cache e memória.
"""

import ctypes
import gc
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import psutil

# Processos essenciais do sistema protegidos contra qualquer alteração
PROTECTED_PROCESSES = {
    "system", "system idle process", "registry", "smss.exe", "csrss.exe",
    "wininit.exe", "services.exe", "lsass.exe", "svchost.exe", "fontdrvhost.exe",
    "dwm.exe", "explorer.exe", "taskhostw.exe", "sihost.exe", "python.exe",
    "uv.exe", "ollama.exe", "ollama_llama_server.exe", "llama-server.exe"
}


class SystemOptimizer:
    """Controlador de telemetria de hardware e rotinas de otimização de sistema."""

    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """Coleta métricas detalhadas do processador."""
        try:
            percent = psutil.cpu_percent(interval=0.1)
            logical_cores = psutil.cpu_count(logical=True) or 1
            physical_cores = psutil.cpu_count(logical=False) or 1
            freq = psutil.cpu_freq()
            current_mhz = round(freq.current, 0) if freq else 0

            return {
                "percent": percent,
                "logical_cores": logical_cores,
                "physical_cores": physical_cores,
                "freq_mhz": current_mhz,
            }
        except Exception as e:
            return {"percent": 0, "logical_cores": 1, "physical_cores": 1, "error": str(e)}

    @staticmethod
    def get_ram_info() -> Dict[str, Any]:
        """Coleta métricas detalhadas de memória RAM."""
        try:
            vm = psutil.virtual_memory()
            total_gb = round(vm.total / (1024 ** 3), 2)
            used_gb = round(vm.used / (1024 ** 3), 2)
            avail_gb = round(vm.available / (1024 ** 3), 2)
            percent = vm.percent

            if percent >= 90:
                health = "CRÍTICO"
            elif percent >= 75:
                health = "ATENÇÃO"
            else:
                health = "OTIMIZADO"

            return {
                "total_gb": total_gb,
                "used_gb": used_gb,
                "avail_gb": avail_gb,
                "percent": percent,
                "health": health,
            }
        except Exception as e:
            return {"total_gb": 0, "used_gb": 0, "avail_gb": 0, "percent": 0, "health": "DESCONHECIDO", "error": str(e)}

    @staticmethod
    def get_disk_info(drive_letter: str = "C:\\") -> Dict[str, Any]:
        """Coleta métricas de uso do disco principal."""
        try:
            usage = psutil.disk_usage(drive_letter)
            total_gb = round(usage.total / (1024 ** 3), 2)
            used_gb = round(usage.used / (1024 ** 3), 2)
            free_gb = round(usage.free / (1024 ** 3), 2)
            percent = usage.percent

            return {
                "drive": drive_letter,
                "total_gb": total_gb,
                "used_gb": used_gb,
                "free_gb": free_gb,
                "percent": percent,
            }
        except Exception as e:
            return {"drive": drive_letter, "total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0, "error": str(e)}

    @staticmethod
    def get_temp_folder_size() -> float:
        """Calcula o tamanho em MB dos arquivos na pasta temporária do usuário."""
        temp_dir = Path(tempfile.gettempdir())
        total_bytes = 0
        try:
            for entry in os.scandir(temp_dir):
                try:
                    if entry.is_file(follow_symlinks=False):
                        total_bytes += entry.stat().st_size
                except (PermissionError, FileNotFoundError):
                    continue
        except Exception:
            pass
        return round(total_bytes / (1024 * 1024), 2)

    @staticmethod
    def get_top_processes(n: int = 5) -> List[Dict[str, Any]]:
        """Lista os processos que mais consomem memória RAM no momento."""
        processes = []
        for p in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            try:
                mem = p.info.get('memory_info')
                if mem:
                    rss_mb = round(mem.rss / (1024 * 1024), 1)
                    name = p.info.get('name') or "Desconhecido"
                    processes.append({
                        "pid": p.info['pid'],
                        "name": name,
                        "memory_mb": rss_mb,
                        "cpu_percent": p.info.get('cpu_percent') or 0.0,
                        "is_protected": name.lower() in PROTECTED_PROCESSES,
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        processes.sort(key=lambda x: x["memory_mb"], reverse=True)
        return processes[:n]

    @classmethod
    def get_full_hardware_report(cls) -> Dict[str, Any]:
        """Compila um relatório holístico da integridade do hardware."""
        cpu = cls.get_cpu_info()
        ram = cls.get_ram_info()
        disk = cls.get_disk_info("C:\\")
        top_proc = cls.get_top_processes(5)
        temp_mb = cls.get_temp_folder_size()

        return {
            "cpu": cpu,
            "ram": ram,
            "disk": disk,
            "temp_folder_mb": temp_mb,
            "top_processes": top_proc,
            "status": "ESTÁVEL" if ram["health"] != "CRÍTICO" else "SOBRECARREGADO",
        }

    @staticmethod
    def clean_temp_files() -> Dict[str, Any]:
        """
        Limpa arquivos temporários do usuário de forma segura.
        Ignora arquivos em uso/bloqueados pelo Windows sem interrupções.
        """
        temp_dir = Path(tempfile.gettempdir())
        freed_bytes = 0
        deleted_count = 0
        skipped_count = 0

        for item in temp_dir.iterdir():
            try:
                if item.is_file() or item.is_symlink():
                    file_size = item.stat().st_size
                    item.unlink(missing_ok=True)
                    freed_bytes += file_size
                    deleted_count += 1
                elif item.is_dir():
                    dir_size = 0
                    try:
                        for f in item.rglob('*'):
                            if f.is_file():
                                dir_size += f.stat().st_size
                    except Exception:
                        pass
                    shutil.rmtree(item, ignore_errors=True)
                    freed_bytes += dir_size
                    deleted_count += 1
            except (PermissionError, FileNotFoundError, OSError):
                skipped_count += 1
                continue

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        return {
            "freed_mb": freed_mb,
            "deleted_items": deleted_count,
            "skipped_in_use": skipped_count,
        }

    @staticmethod
    def optimize_ram() -> Dict[str, Any]:
        """
        Libera memória RAM liberando buffers ociosos e forçando coleta de lixo.
        No Windows, invoca EmptyWorkingSet para processos acessíveis do usuário.
        """
        ram_before = psutil.virtual_memory()

        # 1. Coleta de lixo no runtime Python
        gc.collect()

        # 2. Chamada à API nativa do Windows EmptyWorkingSet
        processes_trimmed = 0
        try:
            kernel32 = ctypes.windll.kernel32
            psapi = ctypes.windll.psapi
            PROCESS_SET_QUOTA = 0x0100
            PROCESS_QUERY_INFORMATION = 0x0400

            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    name = (proc.info.get('name') or "").lower()
                    if name in PROTECTED_PROCESSES:
                        continue

                    pid = proc.info['pid']
                    handle = kernel32.OpenProcess(PROCESS_SET_QUOTA | PROCESS_QUERY_INFORMATION, False, pid)
                    if handle:
                        if psapi.EmptyWorkingSet(handle):
                            processes_trimmed += 1
                        kernel32.CloseHandle(handle)
                except Exception:
                    continue
        except Exception:
            pass

        ram_after = psutil.virtual_memory()
        diff_bytes = ram_before.used - ram_after.used
        freed_mb = round(max(0, diff_bytes) / (1024 * 1024), 2)

        return {
            "freed_mb": freed_mb,
            "ram_before_percent": ram_before.percent,
            "ram_after_percent": ram_after.percent,
            "processes_trimmed": processes_trimmed,
        }

    @classmethod
    def run_full_optimization(cls) -> Dict[str, Any]:
        """Executa a otimização completa (disco + RAM) e retorna o balanço consolidado."""
        temp_res = cls.clean_temp_files()
        ram_res = cls.optimize_ram()
        new_ram = cls.get_ram_info()
        new_disk = cls.get_disk_info()

        return {
            "freed_disk_mb": temp_res["freed_mb"],
            "deleted_temp_items": temp_res["deleted_items"],
            "freed_ram_mb": ram_res["freed_mb"],
            "ram_before_percent": ram_res["ram_before_percent"],
            "ram_after_percent": ram_res["ram_after_percent"],
            "current_ram_percent": new_ram["percent"],
            "current_ram_avail_gb": new_ram["avail_gb"],
            "current_disk_free_gb": new_disk["free_gb"],
        }

    @classmethod
    def detect_optimizer_intent(cls, text: str) -> Optional[Tuple[str, str]]:
        """
        Detecta intenção de análise de hardware ou otimização do sistema.
        Retorna ('diagnostic', query) ou ('optimize', query) ou None.
        """
        lower = text.lower().strip()

        # 1. Comandos explícitos de Otimização e Limpeza
        optimize_keywords = [
            "otimize a máquina", "otimize a maquina", "otimize o sistema", "otimizar sistema",
            "otimizar computador", "otimizar pc", "otimize meu pc", "acelere a máquina",
            "acelere o computador", "acelerar meu pc", "deixe o pc mais rápido",
            "deixe o computador mais rapido", "deixe a máquina mais rápida",
            "deixe a maquina mais rapida", "limpe a memória ram", "limpe a memoria ram",
            "limpar memória", "limpar memoria", "libere memória", "libere memoria",
            "limpe os arquivos temporários", "limpe os temporarios", "otimizar", "otimize"
        ]
        if any(kw in lower for kw in optimize_keywords):
            return ("optimize", text)

        # 2. Comandos de Diagnóstico e Inspeção de Hardware
        diagnostic_keywords = [
            "analise o hardware", "analise meu hardware", "diagnóstico de hardware",
            "diagnostico de hardware", "como está meu pc", "como esta meu pc",
            "como está o hardware", "como esta o hardware", "status do hardware",
            "temperatura do processador", "saúde do sistema", "saude do sistema",
            "processos mais pesados", "quem está consumindo mais memória",
            "quem esta consumindo mais memoria", "uso de ram", "uso da cpu", "uso de disco"
        ]
        if any(kw in lower for kw in diagnostic_keywords):
            return ("diagnostic", text)

        return None


# Instância global
system_optimizer = SystemOptimizer()
