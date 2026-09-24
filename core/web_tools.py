"""
Módulo de Ferramentas Web e Geolocalização do J.A.R.V.I.S.
Permite ao assistente buscar notícias recentes do mundo real, pesquisar na internet e localizar endereços em tempo real.
"""

import re
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple
import requests
from ddgs import DDGS


def search_web(query: str, max_results: int = 4) -> List[Dict[str, str]]:
    """Realiza pesquisa web em tempo real no DuckDuckGo no mundo real."""
    try:
        clean_q = re.sub(
            r"\b(jarvis|por favor|pesquise|pesquisa|pesquise na internet|procure por|procure|busque|me diga sobre|o que você sabe sobre)\b",
            "",
            query,
            flags=re.IGNORECASE,
        ).strip()
        search_term = clean_q if clean_q else query

        with DDGS() as ddgs:
            results = list(ddgs.text(search_term, max_results=max_results))
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
    """Busca notícias recentes e globais em tempo real, com fallback garantido."""
    try:
        clean_q = re.sub(
            r"\b(jarvis|por favor|notícias|noticia|notícias sobre|ultimas noticias|últimas notícias|me diga as notícias|o que está acontecendo no|o que ta acontecendo no|sobre o mundo hoje|do mundo hoje|no mundo hoje)\b",
            "",
            query,
            flags=re.IGNORECASE,
        ).strip()

        search_term = clean_q if clean_q else "noticias mundo hoje"
        results = []

        with DDGS() as ddgs:
            # 1. Tenta endpoint de news
            try:
                raw_news = list(ddgs.news(search_term, max_results=max_results))
                for r in raw_news:
                    title = r.get("title", "")
                    snippet = r.get("body", "")
                    if title and snippet:
                        results.append({
                            "title": title,
                            "snippet": snippet,
                            "source": r.get("source", ""),
                            "url": r.get("url", ""),
                        })
            except Exception:
                pass

            # 2. Se news vazio ou sem resultados, fallback para busca web de notícias
            if not results:
                raw_text = list(ddgs.text(f"últimas notícias {search_term}", max_results=max_results))
                for r in raw_text:
                    results.append({
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "source": r.get("href", ""),
                        "url": r.get("href", ""),
                    })

        return results
    except Exception as e:
        print(f"[Erro busca notícias]: {e}")
        return []


def locate_address(address_query: str) -> Optional[Dict[str, Any]]:
    """Localiza endereços e coordenadas geográficas reais via OpenStreetMap Nominatim."""
    try:
        clean_addr = re.sub(
            r"\b(jarvis|onde fica|localize o endereço|localize|localização de|endereço de|como chegar em|mapa de)\b",
            "",
            address_query,
            flags=re.IGNORECASE,
        ).strip()
        if not clean_addr:
            clean_addr = address_query

        headers = {"User-Agent": "Jarvis-Assistant/1.0"}
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
    e injeta os dados reais atualizados no prompt para que a LLM responda com máxima precisão factual no mundo real.
    Retorna (prompt_enriquecido, label_de_status).
    """
    prompt_lower = prompt.lower()

    # 1. Caso: Localização de endereço
    if any(kw in prompt_lower for kw in ["onde fica", "localize", "localização", "localizacao", "endereço", "endereco", "como chegar", "mapa"]):
        geo = locate_address(prompt)
        if geo:
            context = (
                f"\n[DADOS DE GEOLOCALIZAÇÃO OBTIDOS EM TEMPO REAL NO MUNDO REAL]:\n"
                f"- Endereço Completo: {geo['display_name']}\n"
                f"- Coordenadas: Latitude {geo['lat']}, Longitude {geo['lon']}\n"
                f"- Cidade/Estado/País: {geo['city']}, {geo['state']} - {geo['country']}\n"
                f"- Link no Mapa: {geo['maps_url']}\n\n"
                f"DIRETRIZES OBRIGATÓRIAS AO JARVIS:\n"
                f"1. Responda em no máximo 2 a 3 frases rápidas.\n"
                f"2. Informe o endereço e a localização exata do mundo real.\n"
                f"3. Proibido citar Tony Stark ou ficção de quadrinhos.\n"
            )
            return prompt + context, "📍 Localizando coordenadas no mapa real..."
        else:
            web_res = search_web(f"endereço localização {prompt}", max_results=3)
            if web_res:
                web_text = "\n".join([f"- **{w['title']}**: {w['snippet']}" for w in web_res])
                context = (
                    f"\n[DADOS DE LOCALIZAÇÃO REAIS DA INTERNET]:\n"
                    f"{web_text}\n\n"
                    f"DIRETRIZES OBRIGATÓRIAS AO JARVIS:\n"
                    f"1. Responda em no máximo 2 a 3 frases rápidas com o endereço real.\n"
                    f"2. Foco 100% no mundo real, sem alucinações ou ficção.\n"
                )
                return prompt + context, "📍 Consultando localização na internet..."

    # 2. Caso: Notícias e acontecimentos atuais do mundo
    news_triggers = [
        "notícia", "noticia", "notícias", "noticias",
        "mundo hoje", "no mundo", "do mundo", "acontecendo no mundo",
        "acontece no mundo", "o que tá acontecendo", "o que ta acontecendo",
        "o que está acontecendo", "manchetes", "noticiário", "noticiario",
        "fatos de hoje", "acontecimentos recentes", "últimas notícias", "ultimas noticias",
        "guerra", "política", "politica", "economia mundial"
    ]
    if any(kw in prompt_lower for kw in news_triggers):
        news = search_news(prompt, max_results=4)
        if news:
            news_text = "\n".join([f"- **{n['title']}** ({n.get('source', '')}): {n['snippet']}" for n in news])
            context = (
                f"\n[NOTÍCIAS REAIS E FACTUAIS DO MUNDO COLETADAS DA INTERNET EM TEMPO REAL]:\n"
                f"{news_text}\n\n"
                f"DIRETRIZES OBRIGATÓRIAS AO JARVIS:\n"
                f"1. MUNDO REAL E ZERO ALUCINAÇÃO: Resuma estritamente os fatos e acontecimentos reais listados acima.\n"
                f"2. PROIBIÇÃO TOTAL DE FICÇÃO: Personagens como Tony Stark, Indústrias Stark e super-heróis NÃO EXISTEM no mundo real. Jamais mencione qualquer coisa fictícia.\n"
                f"3. CONCISÃO ABSOLUTA: Responda em no máximo 2 a 3 frases rápidas em texto corrido (sem listas com marcadores), com foco nos fatos principais para leitura fluida por voz.\n"
            )
            return prompt + context, "📰 Coletando notícias reais do mundo..."

    # 3. Caso: Pesquisa geral na internet / dados externos
    search_triggers = [
        "pesquise", "pesquisa", "procure", "busque", "quem é", "quem e", "quem foi",
        "o que é", "o que e", "qual o", "qual a", "quanto custa", "como funciona",
        "resultado", "informações sobre", "informacoes sobre", "dados sobre",
        "qual a situação", "qual a situacao", "preço", "preco", "cotação", "cotacao",
        "clima", "tempo em", "temperatura em", "quem ganhou"
    ]
    if any(kw in prompt_lower for kw in search_triggers):
        web_res = search_web(prompt, max_results=4)
        if web_res:
            web_text = "\n".join([f"- **{w['title']}**: {w['snippet']}" for w in web_res])
            context = (
                f"\n[DADOS FACTUAIS REAIS COLETADOS DA INTERNET EM TEMPO REAL]:\n"
                f"{web_text}\n\n"
                f"DIRETRIZES OBRIGATÓRIAS AO JARVIS:\n"
                f"1. Baseie sua resposta ESTRITAMENTE nos dados reais da internet acima.\n"
                f"2. Proibido inventar fatos ou citar Tony Stark/Marvel.\n"
                f"3. Responda em no máximo 2 a 3 frases rápidas em texto corrido, objetivas e consistentes.\n"
            )
            return prompt + context, "🔍 Realizando busca factual na internet..."

    return prompt, None
