# 🤖 J.A.R.V.I.S. - Assistente de IA Local

> **Just A Rather Very Intelligent System**  
> Assistente pessoal em Python integrado com modelos de linguagem locais via [Ollama](https://ollama.ai/), sem custos de API, 100% privado e offline.

---

## ⚡ Recursos

- **LLM Local e Gratuita:** Integração nativa com modelos da família `llama3.2` (`1b` para velocidade extrema e `3b` para maior raciocínio).
- **Interface Terminal HUD:** Visual futurista estilizado em terminal utilizando a biblioteca `rich`.
- **Streaming de Resposta:** Respostas geradas token por token em tempo real.
- **Memória de Conversa:** Mantém histórico contextual durante a sessão de conversa.
- **Comandos de Sistema:** Verificação de telemetria de CPU/RAM, data/hora e abertura de sites no navegador.
- **Troca Dinâmica de Modelos:** Alterne entre modelos locais em tempo de execução com o comando `/modelo`.

---

## 📁 Estrutura do Projeto

```
jarvis/
├── jarvis.py             # Script principal de execução e interface
├── core/
│   ├── __init__.py
│   ├── config.py         # Configurações de modelo, Ollama e personalidade
│   ├── llm_client.py     # Cliente HTTP para chat e streaming com Ollama
│   └── actions.py        # Ações locais (telemetria, data/hora, navegador)
├── pyproject.toml        # Metadados e dependências do projeto
├── requirements.txt      # Dependências simples (requests, rich)
├── .gitignore            # Arquivos ignorados pelo Git
└── README.md             # Esta documentação
```

---

## 🛠️ Pré-requisitos

1. **Ollama**: Instalado na máquina ([Download Ollama](https://ollama.ai/download)).
   - Certifique-se de que os modelos estão baixados:
     ```bash
     ollama pull llama3.2:1b
     ollama pull llama3.2
     ```
   - O serviço do Ollama deve estar rodando (`ollama serve`).

2. **Python / UV**:
   - O projeto pode ser gerenciado com `uv` (recomendado) ou com Python padrão.

---

## 🚀 Como Executar

### Opção 1: Usando `uv` (Recomendado)

O `uv` baixa o Python e instala os pacotes automaticamente em segundos:

```bash
# Criar o ambiente virtual e sincronizar dependências
uv venv
uv pip install -r requirements.txt

# Executar o Jarvis
uv run python jarvis.py
```

### Opção 2: Usando `python` padrão

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt

# Iniciar o Jarvis
python jarvis.py
```

---

## 🎮 Comandos Disponíveis no Terminal

| Comando | Descrição |
| :--- | :--- |
| `/ajuda` | Mostra todos os comandos do sistema |
| `/status` | Exibe uso de CPU, memória RAM e status da conexão com Ollama |
| `/modelo` | Lista os modelos locais ou altera o modelo ativo (ex: `/modelo llama3.2:latest`) |
| `/hora` | Informa a data e horário atual |
| `/abrir <termo>` | Abre pesquisa no Google ou URL no navegador padrão |
| `/limpar` | Reinicia a memória de conversa do Jarvis |
| `/sair` | Encerra os protocolos do assistente |

---

## 🛡️ Licença
Projeto pessoal desenvolvido para automação e estudo de IA local.
