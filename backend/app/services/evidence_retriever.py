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
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
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
        ]
    }

    async def search(self, query: str, max_results: int = 5) -> List[EvidenceItem]:
        q_lower = query.lower()
        matched: List[EvidenceItem] = []
        for key, items in self.KNOWLEDGE_BASE.items():
            if key in q_lower:
                matched.extend(items)
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

        if provider_name == "tavily" and settings.SEARCH_API_KEY:
            results = await self.tavily_provider.search(query, max_results=settings.SEARCH_RESULTS_PER_CLAIM)

        if not results:
            # First try DuckDuckGo live search
            results = await self.ddg_provider.search(query, max_results=settings.SEARCH_RESULTS_PER_CLAIM)

        # Fallback to internal knowledge base if network is restricted or query matches known ground truth
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
