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
            r"\b(jarvis|por favor|pesquise|pesquisa|pesquise na internet|procure por|procure|busque|me diga sobre|o que você sabe sobre|me fale sobre|fale sobre|informações sobre|informacoes sobre|dados sobre|o que é o medicamento|o que é o remédio|o que é|o que e)\b",
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


def fetch_google_news_rss(query: str = "", max_results: int = 4) -> List[Dict[str, str]]:
    """Obtém manchetes em tempo real via RSS do Google Notícias (sem rate-limit, 100% atualizado)."""
    try:
        import xml.etree.ElementTree as ET
        if query and query.strip():
            encoded = urllib.parse.quote(query.strip())
            url = f"https://news.google.com/rss/search?q={encoded}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        else:
            url = "https://news.google.com/rss?hl=pt-BR&gl=BR&ceid=BR:pt-419"

        resp = requests.get(
            url,
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            items = root.findall(".//item")[:max_results]
            results = []
            for item in items:
                title_elem = item.find("title")
                source_elem = item.find("source")
                link_elem = item.find("link")
                title = title_elem.text if title_elem is not None else ""
                source = source_elem.text if source_elem is not None else ""
                link = link_elem.text if link_elem is not None else ""
                if title:
                    clean_title = re.sub(r" - [^-]+$", "", title).strip()
                    results.append({
                        "title": clean_title,
                        "snippet": f"Manchete em destaque: {title}",
                        "source": source,
                        "url": link,
                    })
            return results
    except Exception as e:
        print(f"[Erro RSS Notícias]: {e}")
    return []


def search_news(query: str, max_results: int = 4) -> List[Dict[str, str]]:
    """Busca notícias recentes e globais em tempo real, priorizando RSS de alta fidelidade."""
    try:
        clean_q = re.sub(
            r"\b(jarvis|por favor|notícias|noticia|notícias sobre|ultimas noticias|últimas notícias|me diga as notícias|o que está acontecendo no|o que ta acontecendo no|o que tá acontecendo no|sobre o mundo hoje|do mundo hoje|no mundo hoje|no mundo|do mundo|mundo hoje)\b",
            "",
            query,
            flags=re.IGNORECASE,
        ).strip(" ?.,!")

        # 1. Tenta RSS do Google Notícias em tempo real
        rss_results = fetch_google_news_rss(clean_q, max_results=max_results)
        if rss_results:
            return rss_results

        # 2. Fallback: DuckDuckGo text search
        search_term = f"ultimas noticias {clean_q}" if clean_q else "ultimas noticias brasil mundo"
        results = []
        with DDGS() as ddgs:
            raw_text = list(ddgs.text(search_term, max_results=max_results))
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
                f"1. Responda em no máximo 2 a 3 frases rápidas, em tom coloquial, natural e direto.\n"
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
                    f"1. Responda em no máximo 2 a 3 frases rápidas com o endereço real, em linguagem coloquial.\n"
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
                f"\n[MANCHETES E FATOS REAIS DO MUNDO HOJE]:\n"
                f"{news_text}\n\n"
                f"DIRETRIZES OBRIGATÓRIAS AO JARVIS:\n"
                f"1. Fale como um parceiro esperto em tom leve, ágil e coloquial (ex: 'Olha só o que tá rolando hoje...').\n"
                f"2. Resuma de forma direta os principais acontecimentos reais listados acima.\n"
                f"3. Responda em no máximo 2 a 3 frases rápidas em texto corrido (sem listas com marcadores), perfeito para voz.\n"
                f"4. Mantenha foco 100% no mundo real.\n"
            )
            return prompt + context, "📰 Coletando notícias reais do mundo..."

    # 3. Caso: Pesquisa geral na internet / medicamentos / dados externos
    search_triggers = [
        "pesquise", "pesquisa", "procure", "busque", "quem é", "quem e", "quem foi",
        "o que é", "o que e", "qual o", "qual a", "quanto custa", "como funciona",
        "resultado", "informações sobre", "informacoes sobre", "dados sobre",
        "informação sobre", "informacao sobre", "me fale sobre", "fale sobre",
        "qual a situação", "qual a situacao", "preço", "preco", "cotação", "cotacao",
        "clima", "tempo em", "temperatura em", "quem ganhou",
        # Termos médicos, de remédios e saúde:
        "medicamento", "remédio", "remedio", "bula", "para que serve", "efeito", "efeitos",
        "colateral", "colaterais", "posologia", "dosagem", "comprimido", "indicação", "indicacao",
        "contraindicação", "contraindicacao", "farmácia", "farmacia", "farmacologia",
        "substância", "substancia", "tratamento", "doença", "doenca", "sintoma", "sintomas",
        "saúde", "saude"
    ]
    if any(kw in prompt_lower for kw in search_triggers):
        web_res = search_web(prompt, max_results=4)
        if web_res:
            web_text = "\n".join([f"- **{w['title']}**: {w['snippet']}" for w in web_res])
            context = (
                f"\n[DADOS FACTUAIS REAIS COLETADOS DA INTERNET]:\n"
                f"{web_text}\n\n"
                f"DIRETRIZES OBRIGATÓRIAS AO JARVIS:\n"
                f"1. Explique de forma direta, clara e amigável o que é o item/medicamento pesquisado, para que serve e suas características conforme os dados acima.\n"
                f"2. Use linguagem coloquial, leve e descontraída em português do Brasil.\n"
                f"3. Responda em no máximo 2 a 3 frases rápidas em texto corrido, de forma objetiva e prestativa.\n"
            )
            return prompt + context, "🔍 Realizando busca factual na internet..."

    return prompt, None
