"""
Módulo de Ferramentas Web e Geolocalização do J.A.R.V.I.S.
Permite ao assistente buscar notícias recentes, pesquisar na internet e localizar endereços em tempo real.
"""

import re
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple
import requests
from ddgs import DDGS


def search_web(query: str, max_results: int = 4) -> List[Dict[str, str]]:
    """Realiza pesquisa web em tempo real no DuckDuckGo."""
    try:
        clean_q = re.sub(r"\b(jarvis|pesquise|pesquise na internet|procure por|busque)\b", "", query, flags=re.IGNORECASE).strip()
        with DDGS() as ddgs:
            results = list(ddgs.text(clean_q or query, max_results=max_results))
            formatted = []
            for r in results:
                formatted.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "href": r.get("href", ""),
                })
            return formatted
    except Exception as e:
        print(f"[Erro busca web]: {e}")
        return []


def search_news(query: str, max_results: int = 4) -> List[Dict[str, str]]:
    """Busca notícias recentes em tempo real."""
    try:
        clean_q = re.sub(r"\b(jarvis|notícias|noticia|notícias sobre|ultimas noticias)\b", "", query, flags=re.IGNORECASE).strip()
        with DDGS() as ddgs:
            results = list(ddgs.news(clean_q or "Brasil notícias", max_results=max_results))
            formatted = []
            for r in results:
                formatted.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "date": r.get("date", ""),
                    "source": r.get("source", ""),
                    "url": r.get("url", ""),
                })
            return formatted
    except Exception as e:
        print(f"[Erro busca notícias]: {e}")
        return []


def locate_address(address_query: str) -> Optional[Dict[str, Any]]:
    """Localiza endereços e coordenadas geográficas via OpenStreetMap Nominatim."""
    try:
        clean_addr = re.sub(r"\b(jarvis|onde fica|localize o endereço|localize|localização de|endereço de|como chegar em|mapa de)\b", "", address_query, flags=re.IGNORECASE).strip()
        if not clean_addr:
            clean_addr = address_query

        headers = {"User-Agent": "Jarvis-Tactical-Assistant/1.0 (Stark Industries)"}
        params = {"q": clean_addr, "format": "json", "addressdetails": "1", "limit": "1"}
        url = f"https://nominatim.openstreetmap.org/search?{urllib.parse.urlencode(params)}"

        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200 and res.json():
            data = res.json()[0]
            lat = data.get("lat")
            lon = data.get("lon")
            display_name = data.get("display_name")
            addr_details = data.get("address", {})
            maps_link = f"https://www.google.com/maps?q={lat},{lon}"

            return {
                "display_name": display_name,
                "lat": lat,
                "lon": lon,
                "city": addr_details.get("city") or addr_details.get("town") or addr_details.get("municipality", ""),
                "state": addr_details.get("state", ""),
                "country": addr_details.get("country", ""),
                "maps_url": maps_link,
            }
        return None
    except Exception as e:
        print(f"[Erro geolocalização]: {e}")
        return None


def enrich_prompt_with_live_data(prompt: str) -> Tuple[str, Optional[str]]:
    """
    Detecta se a solicitação necessita de dados online (notícias, busca web ou localização de endereço)
    e injeta os dados reais atualizados no prompt para que a LLM responda com máxima precisão e detalhe.
    Retorna (prompt_enriquecido, label_de_status).
    """
    prompt_lower = prompt.lower()

    # 1. Caso: Localização de endereço
    if any(kw in prompt_lower for kw in ["onde fica", "localize", "localização", "endereço", "como chegar", "mapa"]):
        geo = locate_address(prompt)
        if geo:
            context = (
                f"\n[DADOS DE GEOLOCALIZAÇÃO OBTIDOS EM TEMPO REAL VIA SATÉLITE/GPS]:\n"
                f"- Endereço Completo: {geo['display_name']}\n"
                f"- Coordenadas: Latitude {geo['lat']}, Longitude {geo['lon']}\n"
                f"- Cidade/Estado/País: {geo['city']}, {geo['state']} - {geo['country']}\n"
                f"- Link no Mapa: {geo['maps_url']}\n\n"
                f"INSTRUÇÃO AO JARVIS: Informe ao Senhor com precisão onde fica o local solicitado, descreva a região e forneça as coordenadas e o link do mapa de forma refinada e detalhada.\n"
            )
            return prompt + context, "📍 Localizando coordenadas e endereço via satélite..."
        else:
            # Fallback para busca de pontos turísticos / estabelecimentos
            web_res = search_web(f"endereço localização {prompt}", max_results=3)
            if web_res:
                web_text = "\n".join([f"- **{w['title']}**: {w['snippet']}" for w in web_res])
                context = (
                    f"\n[DADOS DE LOCALIZAÇÃO OBTIDOS EM TEMPO REAL DA INTERNET]:\n"
                    f"{web_text}\n\n"
                    f"INSTRUÇÃO AO JARVIS: Informe ao Senhor com precisão onde fica o local com base nos dados reais acima, incluindo rua, bairro, cidade e referências de forma detalhada.\n"
                )
                return prompt + context, "📍 Consultando localização e endereço na internet..."

    # 2. Caso: Notícias atualizadas
    if any(kw in prompt_lower for kw in ["notícia", "noticias", "notícia de", "notícias de", "acontecimentos recentes", "últimas notícias", "hoje no brasil"]):
        news = search_news(prompt, max_results=3)
        if news:
            news_text = "\n".join([f"- **{n['title']}** ({n.get('source', '')}): {n['snippet']} (Link: {n.get('url', '')})" for n in news])
            context = (
                f"\n[NOTÍCIAS ATUALIZADAS COLETADAS EM TEMPO REAL DA INTERNET]:\n"
                f"{news_text}\n\n"
                f"INSTRUÇÃO AO JARVIS: Apresente ao Senhor um resumo detalhado, completo e sofisticado das notícias acima, organizadas em tópicos claros e informativos.\n"
            )
            return prompt + context, "📰 Coletando notícias em tempo real na rede..."

    # 3. Caso: Pesquisa geral na internet / dados externos
    if any(kw in prompt_lower for kw in ["pesquise", "procure", "busque", "quem é", "o que é", "qual o", "quanto custa", "como funciona", "resultado"]):
        web_res = search_web(prompt, max_results=3)
        if web_res:
            web_text = "\n".join([f"- **{w['title']}**: {w['snippet']} (Fonte: {w['href']})" for w in web_res])
            context = (
                f"\n[DADOS ATUALIZADOS COLETADOS EM TEMPO REAL DA WEB]:\n"
                f"{web_text}\n\n"
                f"INSTRUÇÃO AO JARVIS: Elabore uma resposta rica, aprofundada, didática e muito bem estruturada para o Senhor com base nas informações coletadas acima.\n"
            )
            return prompt + context, "🔍 Realizando varredura na internet em tempo real..."

    return prompt, None
