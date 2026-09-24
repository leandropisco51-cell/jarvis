"""
Motor de Síntese de Voz Neural (Neural TTS) do J.A.R.V.I.S.
Utiliza Microsoft Edge Neural TTS (edge-tts) para gerar voz humana ultra-realista em Português Brasileiro.
"""

import re
import edge_tts

# Vozes neurais disponíveis e seus ajustes de timbre/cadência
NEURAL_VOICES = {
    "pt-BR-AntonioNeural": {
        "name": "Jarvis (Antonio Neural)",
        "voice": "pt-BR-AntonioNeural",
        "rate": "+6%",
        "pitch": "-2Hz",
    },
    "pt-BR-FranciscaNeural": {
        "name": "F.R.I.D.A.Y. (Francisca Neural)",
        "voice": "pt-BR-FranciscaNeural",
        "rate": "+6%",
        "pitch": "+0Hz",
    },
    "pt-BR-ThalitaMultilingualNeural": {
        "name": "Thalita (Multilíngue Neural)",
        "voice": "pt-BR-ThalitaMultilingualNeural",
        "rate": "+5%",
        "pitch": "+0Hz",
    },
}

DEFAULT_VOICE_ID = "pt-BR-AntonioNeural"


def clean_text_for_speech(text: str) -> str:
    """
    Limpa marcações Markdown, blocos de código extensos, URLs e símbolos
    para que a leitura pela voz neural seja natural, fluida e sem tropeços.
    """
    if not text:
        return ""

    # Substituir blocos de código por aviso breve para não soletrar linhas de código
    text = re.sub(r"```[\s\S]*?```", " Código gerado na tela. ", text)

    # Remover links markdown mantendo apenas o texto: [texto](url) -> texto
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

    # Remover URLs soltas
    text = re.sub(r"https?://\S+", "", text)

    # Remover tags HTML básicas (<br>, <b>, <i>, <span>, etc.)
    text = re.sub(r"<[^>]+>", " ", text)

    # Remover caracteres de formatação markdown (*, #, _, `, ~)
    text = re.sub(r"[*#_`~>|]", "", text)

    # Remover emojis de decoração técnica repetitivos que atrapalham a leitura
    text = re.sub(r"[⚡🔧🧠📊🌐✅❌⚠️🚀💡📌🔍🖥️💾]", "", text)

    # Normalizar múltiplos espaços e quebras de linha
    text = re.sub(r"\s+", " ", text).strip()

    return text


async def synthesize_neural_speech(text: str, voice_id: str = DEFAULT_VOICE_ID) -> bytes:
    """
    Gera o áudio MP3 em memória utilizando a voz neural selecionada.
    """
    clean_text = clean_text_for_speech(text)
    if not clean_text:
        return b""

    preset = NEURAL_VOICES.get(voice_id, NEURAL_VOICES[DEFAULT_VOICE_ID])
    communicate = edge_tts.Communicate(
        text=clean_text,
        voice=preset["voice"],
        rate=preset["rate"],
        pitch=preset["pitch"],
    )

    audio_chunks = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.extend(chunk["data"])

    return bytes(audio_chunks)
