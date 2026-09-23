# 🤖 J.A.R.V.I.S. - Assistente de IA Local

> **Just A Rather Very Intelligent System**  
> Assistente pessoal em Python integrado com modelos de linguagem locais via [Ollama](https://ollama.ai/), sem custos de API, 100% privado e offline.
> Equipado com **Interface Web Holográfica (HUD)** estilo Stark Industries (Homem de Ferro), **Reconhecimento de Voz (STT)** e **Síntese de Voz (TTS)**.

---

## ⚡ Recursos

- **Interface Web Holográfica:** HUD tático com tema escuro, gradientes neon ciano, glassmorphism e animação em Canvas do **Reator Arc Central**.
- **Comandos por Voz:** Fale diretamente no microfone (Web Speech API em português `pt-BR`) para comandar o Jarvis sem precisar digitar.
- **Resposta por Voz:** O Jarvis sintetiza e responde por voz em áudio com tom refinado e articulado.
- **Reator Arc Reativo:** O reator central muda de estado e pulsa com ondas sonoras conforme o Jarvis está *Standby*, *Ouvindo*, *Pensando* ou *Falando*.
- **Telemetria de Sistema em Tempo Real:** Monitoramento ao vivo do consumo de memória RAM, núcleos de CPU e latência.
- **Streaming Instantâneo de Resposta:** Tokens transmitidos em tempo real via Server-Sent Events (SSE).
- **Troca Dinâmica de Modelos:** Alterne entre `llama3.2:1b` (ultra rápido) e `llama3.2:latest` (3.2B para raciocínio complexo) diretamente pela interface ou pelo terminal.
- **Interface Terminal HUD Alternativa:** Para quem prefere usar diretamente via prompt de comando (`jarvis.py`).

---

## 📁 Estrutura do Projeto

```
jarvis/
├── app.py                      # Servidor FastAPI com endpoints REST e SSE Streaming
├── jarvis.py                   # CLI do terminal + inicializador rápido
├── core/
│   ├── __init__.py
│   ├── config.py               # Configurações de modelo, Ollama e personalidade
│   ├── llm_client.py           # Cliente HTTP para chat e streaming com Ollama
│   └── actions.py              # Ações locais (telemetria, data/hora, navegador)
├── web/
│   ├── templates/
│   │   └── index.html          # Interface HUD tática holográfica
│   └── static/
│       ├── css/
│       │   └── hud.css         # Efeitos de neon, glassmorphism e animações HUD
│       └── js/
│           ├── reactor.js      # Gráficos Canvas 2D do Reator Arc e ondas sonoras
│           └── app.js          # Controle da interface, microfone e voz do Jarvis
├── pyproject.toml              # Metadados e dependências (uv/pip)
├── requirements.txt            # Dependências (fastapi, uvicorn, requests, rich)
├── .gitignore                  # Arquivos ignorados pelo Git
└── README.md                   # Esta documentação
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
   - O projeto é gerenciado com `uv` (já configurado) ou Python padrão.

---

## 🚀 Como Iniciar

### 1. Iniciar a Interface Web Holográfica (Recomendado)

Inicie o servidor web e abra no navegador:

```powershell
uv run python app.py
```

Acesse no seu navegador: **`http://127.0.0.1:8000`**

- Clique no botão do **Microfone** para falar com o Jarvis.
- O Jarvis falará a resposta em áudio e digitará em tempo real.
- Você pode ligar/desligar o áudio do Jarvis a qualquer momento no botão **VOZ DO JARVIS: ON/OFF**.

---

### 2. Iniciar pelo Terminal HUD

Se preferir o terminal tático:

```powershell
uv run python jarvis.py
```

- Digite `/ajuda` para ver todos os comandos.
- Digite `/web` para abrir a interface holográfica no navegador.
- Digite `/status` para inspecionar a telemetria do computador.
- Digite `/modelo` para alternar entre os modelos locais instalados.

---

## 🎮 Comandos Disponíveis

| Comando | Descrição |
| :--- | :--- |
| `/web` | Inicia e abre a interface holográfica no navegador |
| `/ajuda` | Mostra todos os comandos do sistema |
| `/status` | Exibe uso de CPU, memória RAM e status da conexão com Ollama |
| `/modelo [nome]` | Lista os modelos locais ou altera o modelo ativo |
| `/hora` | Informa a data e horário atual |
| `/abrir <termo>` | Abre pesquisa no Google ou URL no navegador padrão |
| `/limpar` | Reinicia a memória de conversa do Jarvis |
| `/sair` | Encerra os protocolos do assistente |

---

## 🛡️ Licença
Projeto pessoal desenvolvido para automação e estudo de IA local.
