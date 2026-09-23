"""
Configurações do sistema J.A.R.V.I.S.
"""

# Configurações do servidor Ollama
OLLAMA_HOST = "http://127.0.0.1:11434"

# Modelos suportados
DEFAULT_MODEL = "llama3.2:1b"
ALTERNATIVE_MODEL = "llama3.2:latest"

# Parâmetros de geração
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9

# Personalidade do Jarvis
JARVIS_SYSTEM_PROMPT = (
    "Você é J.A.R.V.I.S. (Just A Rather Very Intelligent System), um assistente de inteligência artificial "
    "altamente sofisticado, prestativo, perspicaz e elegante. Você se comunica prioritariamente em português "
    "do Brasil. Trate o usuário cordialmente como 'Senhor' ou 'Mestre'. Suas respostas devem ser claras, precisas, "
    "úteis e com um leve toque de polidez refinada típica do Jarvis do Homem de Ferro. "
    "Se o usuário pedir respostas curtas ou comandos diretos, seja direto e eficiente."
)
