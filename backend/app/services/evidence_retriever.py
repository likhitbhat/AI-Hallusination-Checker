import abc
import re
import time
from typing import List, Dict, Optional
from urllib.parse import quote_plus
import httpx
from app.config import settings
from app.utils.logger import logger
from app.api.schemas import EvidenceItem
from app.services.source_reliability import source_reliability_scorer


class BaseSearchProvider(abc.ABC):
    @abc.abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[EvidenceItem]:
        pass


class DuckDuckGoProvider(BaseSearchProvider):
    """Zero-configuration search provider using DuckDuckGo HTML endpoint."""

    async def search(self, query: str, max_results: int = 5) -> List[EvidenceItem]:
        encoded_query = quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        }

        results: List[EvidenceItem] = []
        try:
            async with httpx.AsyncClient(timeout=1.0, follow_redirects=True) as client:
                resp = await client.post(url, headers=headers, data={"q": query})
                if resp.status_code == 200:
                    html = resp.text
                    # Extract result links and snippets via regex
                    links = re.findall(r'<a class="result__url"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html)
                    snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html)
                    titles = re.findall(r'<a class="result__a"[^>]*>(.*?)</a>', html)

                    count = min(len(titles), len(snippets), max_results)
                    for i in range(count):
                        raw_url = links[i][0] if i < len(links) else ""
                        # Clean DuckDuckGo redirect URL
                        uddg_match = re.search(r"uddg=([^&]+)", raw_url)
                        clean_url = httpx.URL(uddg_match.group(1)).query if uddg_match else raw_url
                        if clean_url.startswith("//"):
                            clean_url = "https:" + clean_url

                        clean_title = re.sub(r"<[^>]+>", "", titles[i]).strip()
                        clean_snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip()

                        if clean_snippet and len(clean_snippet) > 15:
                            score = source_reliability_scorer.score_source(clean_url)
                            results.append(EvidenceItem(
                                title=clean_title or "Web Evidence",
                                url=clean_url,
                                snippet=clean_snippet,
                                reliability_score=score,
                                domain=source_reliability_scorer.extract_domain(clean_url)
                            ))
        except Exception as e:
            logger.warning(f"DuckDuckGo search error: {e}")

        return results


class TavilyProvider(BaseSearchProvider):
    """Tavily search provider for LLM and research workloads."""

    async def search(self, query: str, max_results: int = 5) -> List[EvidenceItem]:
        if not settings.SEARCH_API_KEY:
            return []

        results = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    headers={"Content-Type": "application/json"},
                    json={
                        "api_key": settings.SEARCH_API_KEY,
                        "query": query,
                        "search_depth": "basic",
                        "max_results": max_results,
                        "include_answer": False
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("results", []):
                        url = item.get("url", "")
                        results.append(EvidenceItem(
                            title=item.get("title", ""),
                            url=url,
                            snippet=item.get("content", ""),
                            reliability_score=source_reliability_scorer.score_source(url),
                            domain=source_reliability_scorer.extract_domain(url)
                        ))
        except Exception as e:
            logger.warning(f"Tavily search provider error: {e}")

        return results


class MockSearchProvider(BaseSearchProvider):
    """Deterministic mock provider for unit testing and offline evaluation datasets."""

    KNOWLEDGE_BASE = {
        "india": [
            EvidenceItem(
                title="Government of India Official Portal",
                url="https://india.gov.in/my-government/whos-who",
                snippet="India has 28 states and 8 Union Territories as of the reorganization in 2019 and 2020.",
                reliability_score=1.00,
                domain="india.gov.in"
            ),
            EvidenceItem(
                title="Encyclopedia Britannica - States of India",
                url="https://www.britannica.com/place/India",
                snippet="India comprises 28 states and 8 union territories. The capital of Karnataka is Bengaluru.",
                reliability_score=0.80,
                domain="britannica.com"
            )
        ],
        "karnataka": [
            EvidenceItem(
                title="Karnataka State Portal",
                url="https://karnataka.gov.in/english",
                snippet="Bengaluru is the capital of the southern state of Karnataka. The state was formed on 1 November 1956.",
                reliability_score=1.00,
                domain="karnataka.gov.in"
            )
        ],
        "australia": [
            EvidenceItem(
                title="Australian Government Information",
                url="https://www.australia.gov.au/about-australia",
                snippet="Canberra is the capital city of Australia. Australia has 6 states and 2 major mainland territories.",
                reliability_score=1.00,
                domain="australia.gov.au"
            )
        ],
        "water": [
            EvidenceItem(
                title="National Institute of Standards and Technology (NIST)",
                url="https://webbook.nist.gov/chemistry/fluid/",
                snippet="Water boils at approximately 100°C (212°F) at standard atmospheric pressure (1 atm).",
                reliability_score=1.00,
                domain="nist.gov"
            )
        ],
        "mars": [
            EvidenceItem(
                title="NASA - Mars Exploration Program",
                url="https://mars.nasa.gov/all-about-mars/facts/",
                snippet="Mars is currently uninhabited by humans. No human has ever visited or colonized Mars; the human population is zero.",
                reliability_score=1.00,
                domain="nasa.gov"
            )
        ],
        "eiffel": [
            EvidenceItem(
                title="Official Eiffel Tower Website",
                url="https://www.toureiffel.paris/en",
                snippet="The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, France.",
                reliability_score=0.95,
                domain="toureiffel.paris"
            )
        ],
        "france": [
            EvidenceItem(
                title="Official Portal of the French Republic",
                url="https://www.service-public.fr",
                snippet="Paris is the capital and most populous city of France.",
                reliability_score=1.00,
                domain="service-public.fr"
            ),
            EvidenceItem(
                title="Encyclopedia Britannica - Paris",
                url="https://www.britannica.com/place/Paris",
                snippet="Paris is the capital city of France and the center of French commerce, culture, and government.",
                reliability_score=0.80,
                domain="britannica.com"
            )
        ],
        "paris": [
            EvidenceItem(
                title="Encyclopedia Britannica - Paris",
                url="https://www.britannica.com/place/Paris",
                snippet="Paris is the capital city of France.",
                reliability_score=0.80,
                domain="britannica.com"
            )
        ],
        "python": [
            EvidenceItem(
                title="Python Software Foundation",
                url="https://www.python.org/doc/essays/blurb/",
                snippet="Python is an interpreted, object-oriented, high-level programming language with dynamic semantics, created by Guido van Rossum and first released in 1991.",
                reliability_score=0.95,
                domain="python.org"
            )
        ],
        "einstein": [
            EvidenceItem(
                title="Nobel Prize Official - Albert Einstein",
                url="https://www.nobelprize.org/prizes/physics/1921/einstein/biographical/",
                snippet="Albert Einstein was a German-born theoretical physicist who received the 1921 Nobel Prize in Physics for his services to theoretical physics, especially for his discovery of the law of the photoelectric effect. He developed the theory of relativity.",
                reliability_score=0.98,
                domain="nobelprize.org"
            )
        ],
        "sun": [
            EvidenceItem(
                title="NASA Solar System Exploration",
                url="https://science.nasa.gov/sun/",
                snippet="The Earth revolves around the Sun once every 365.25 days. The Sun is the star at the center of the Solar System.",
                reliability_score=1.00,
                domain="nasa.gov"
            )
        ],
        "earth": [
            EvidenceItem(
                title="NASA Earth Science",
                url="https://science.nasa.gov/earth/",
                snippet="The Earth is the third planet from the Sun and the only astronomical object known to harbor life. It revolves around the Sun.",
                reliability_score=1.00,
                domain="nasa.gov"
            )
        ],
        "everest": [
            EvidenceItem(
                title="Encyclopedia Britannica - Mount Everest",
                url="https://www.britannica.com/place/Mount-Everest",
                snippet="Mount Everest is the highest mountain peak in the world, located in the Himalayas on the crest of the Great Himalayas of southern Asia on the border between Nepal and the Tibet Autonomous Region of China. Its official elevation is 8,848.86 metres.",
                reliability_score=0.85,
                domain="britannica.com"
            )
        ],
        "photosynthesis": [
            EvidenceItem(
                title="Encyclopedia Britannica - Photosynthesis",
                url="https://www.britannica.com/science/photosynthesis",
                snippet="Photosynthesis is the process by which green plants and certain other organisms transform light energy into chemical energy.",
                reliability_score=0.85,
                domain="britannica.com"
            )
        ],
        "speed of light": [
            EvidenceItem(
                title="NIST Physical Constants",
                url="https://physics.nist.gov/cgi-bin/cuu/Value?c",
                snippet="The speed of light in vacuum, commonly denoted c, is a universal physical constant exactly equal to 299,792,458 metres per second (approximately 300,000 km/s).",
                reliability_score=1.00,
                domain="nist.gov"
            )
        ],
        "tokyo": [
            EvidenceItem(
                title="Tokyo Metropolitan Government",
                url="https://www.metro.tokyo.lg.jp/english/",
                snippet="Tokyo is the capital and most populous prefecture of Japan, located at the head of Tokyo Bay.",
                reliability_score=1.00,
                domain="metro.tokyo.lg.jp"
            )
        ],
        "japan": [
            EvidenceItem(
                title="Ministry of Foreign Affairs of Japan",
                url="https://www.mofa.go.jp/about/",
                snippet="Tokyo is the capital city of Japan.",
                reliability_score=1.00,
                domain="mofa.go.jp"
            )
        ],
        "london": [
            EvidenceItem(
                title="UK Government Portal",
                url="https://www.gov.uk/government/organisations",
                snippet="London is the capital and largest city of England and the United Kingdom.",
                reliability_score=1.00,
                domain="gov.uk"
            )
        ],
        "united kingdom": [
            EvidenceItem(
                title="UK Government Portal",
                url="https://www.gov.uk/government/organisations",
                snippet="London is the capital city of the United Kingdom.",
                reliability_score=1.00,
                domain="gov.uk"
            )
        ],
        "germany": [
            EvidenceItem(
                title="Federal Government of Germany",
                url="https://www.bundesregierung.de/breg-en",
                snippet="Berlin is the capital and largest city of Germany both by area and by population.",
                reliability_score=1.00,
                domain="bundesregierung.de"
            )
        ],
        "united states": [
            EvidenceItem(
                title="Official Portal of the United States Government",
                url="https://www.usa.gov/about-the-us",
                snippet="The United States comprises 50 states, a federal district, and several territories. Washington, D.C. is the capital of the United States.",
                reliability_score=1.00,
                domain="usa.gov"
            )
        ],
        "barack obama": [
            EvidenceItem(
                title="The White House - Presidential Biographies",
                url="https://www.whitehouse.gov/about-the-white-house/presidents/barack-obama/",
                snippet="Barack Obama was the 44th President of the United States, serving from 2009 to 2017.",
                reliability_score=1.00,
                domain="whitehouse.gov"
            )
        ],
        "javascript": [
            EvidenceItem(
                title="Mozilla Developer Network (MDN)",
                url="https://developer.mozilla.org/en-US/docs/Web/JavaScript",
                snippet="JavaScript is a lightweight, interpreted, compiled programming language with first-class functions, best known as the scripting language for Web pages.",
                reliability_score=0.95,
                domain="developer.mozilla.org"
            )
        ]
    }

    async def search(self, query: str, max_results: int = 5) -> List[EvidenceItem]:
        q_lower = query.lower()
        matched: List[EvidenceItem] = []
        for key, items in self.KNOWLEDGE_BASE.items():
            if key in q_lower:
                for it in items:
                    if it not in matched:
                        matched.append(it)
        return matched[:max_results]


class EvidenceRetriever:
    """Manages search queries, provider selection, deduplication, and caching."""

    def __init__(self):
        self._cache: Dict[str, tuple[float, List[EvidenceItem]]] = {}
        self.mock_provider = MockSearchProvider()
        self.ddg_provider = DuckDuckGoProvider()
        self.tavily_provider = TavilyProvider()

    def optimize_query(self, claim_text: str) -> str:
        # Strip trailing punctuation and common conversational fillers
        query = re.sub(r"[.!?]+$", "", claim_text.strip())
        query = re.sub(r"^(?:it is known that|studies show that|according to)\s+", "", query, flags=re.IGNORECASE)
        return query

    async def retrieve_evidence(self, claim_text: str) -> List[EvidenceItem]:
        query = self.optimize_query(claim_text)
        cache_key = query.lower()

        # Check in-memory cache
        if cache_key in self._cache:
            cached_time, cached_results = self._cache[cache_key]
            if time.time() - cached_time < settings.SEARCH_CACHE_TTL_SECONDS:
                return cached_results

        provider_name = settings.SEARCH_PROVIDER.lower()
        results: List[EvidenceItem] = []

        if provider_name == "mock":
            results = await self.mock_provider.search(query, max_results=settings.SEARCH_RESULTS_PER_CLAIM)
        elif provider_name == "tavily" and settings.SEARCH_API_KEY:
            results = await self.tavily_provider.search(query, max_results=settings.SEARCH_RESULTS_PER_CLAIM)
            if not results:
                results = await self.mock_provider.search(query, max_results=settings.SEARCH_RESULTS_PER_CLAIM)
        else:
            # Default live search: try DuckDuckGo, fallback to knowledge base if offline or rate-limited
            results = await self.ddg_provider.search(query, max_results=settings.SEARCH_RESULTS_PER_CLAIM)
            if not results:
                results = await self.mock_provider.search(query, max_results=settings.SEARCH_RESULTS_PER_CLAIM)

        # Deduplicate results by URL
        seen_urls = set()
        deduped = []
        for item in results:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                deduped.append(item)

        self._cache[cache_key] = (time.time(), deduped)
        return deduped


evidence_retriever = EvidenceRetriever()
